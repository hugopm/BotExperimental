import os
import discord
from discord import ApplicationContext
from ranking import Ranking 
from views import ConfirmView, ScoreModal
from data import BotData
from config import cfg
try:
    from pwmaker import getPw
    PASSWORD_ENABLED = True
except ImportError:
    PASSWORD_ENABLED = False
import re

class FioiBot(discord.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        
        self.data = BotData()
        self.ranking = Ranking(self)

    async def setup_bot_context(self):
        self.guild_fioi = await self.fetch_guild(cfg.GUILD_ID)
        await self._setup_roles()
        await self._setup_channels()

    async def _setup_roles(self):
        self.role_debrief = self.guild_fioi.get_role(cfg.roles.DEBRIEF)
        self.role_ranking = self.guild_fioi.get_role(cfg.roles.RANKING)
        self.role_participant = self.guild_fioi.get_role(cfg.roles.PARTICIPANT)

    async def _setup_channels(self):
        self.salon_classement = await self.guild_fioi.fetch_channel(cfg.channels.RANKING)
        assert self.salon_classement is not None

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await self.setup_bot_context()
        await self.ranking.update()
        # async for m in self.guild_fioi.fetch_members():
        #     if self.role_debrief in m.roles:
        #         print(m.name)
        #         await m.remove_roles(self.role_ranking, self.role_debrief)

bot = FioiBot()

def slash(desc):
    return bot.slash_command(guild_ids=[cfg.GUILD_ID], description=desc)

@slash("J'ai fini l'épreuve")
async def debrief(ctx: ApplicationContext):
    if cfg.lock_msg:
        await ctx.respond(cfg.lock_msg, ephemeral=True)
        return

    if bot.role_debrief in ctx.author.roles:
        await ctx.respond(f"Vous avez déjà le rôle {bot.role_debrief.name}")
        return

    view = ConfirmView(ctx.author)
    await ctx.respond(
        cfg.contest.MESSAGE.format(user_mention=ctx.author.mention),
        view=view
    )
    
    await view.wait()
    if view.value is None:
        await ctx.edit(content="Timeout", view=None)
    elif view.value:
        await ctx.author.add_roles(bot.role_debrief, bot.role_participant)
        await ctx.edit(content=f"Vous avez obtenu le rôle {bot.role_debrief.name} !", view=None)
    else:
        await ctx.edit(content="Vous avez annulé la commande. Ce bot n'est pas un jouet.", view=None)

@slash("Publier mon score")
async def liverank(ctx: ApplicationContext):
    if not await bot.is_owner(ctx.author):
        if bot.role_debrief not in ctx.author.roles:
            await ctx.respond(
                f"Vous devez avoir le rôle {bot.role_debrief.name} pour déclarer votre score.",
                ephemeral=True
            )
            return
    modal = ScoreModal(bot, timeout=10)
    await ctx.send_modal(modal)
    await modal.wait()

@slash("Statistiques de l'épreuve")
async def stats(ctx: ApplicationContext):
    if ctx.channel.id != cfg.channels.DEBRIEF:
        await ctx.respond("Cette commande doit être lancée dans #debrief-epreuve", ephemeral=True)
        return

    scores = [score for _, score in bot.data.scan()]
    stats = bot.ranking.calculate_problem_stats(scores)
    content = bot.ranking.format_stats(stats, len(scores))
    await ctx.respond(content)

@slash("Mot de passe CMS")
async def password(ctx: ApplicationContext):
    if not PASSWORD_ENABLED:
        await ctx.respond(
            "Cette commande n'est pas disponible car la génération de mot de passe n'est pas activée.",
            ephemeral=True
        )
        return

    try:
        id_fioi = _extract_id_from_name(ctx.author.display_name)
        if not id_fioi:
            await ctx.respond(
                "Vous devez vous renommer sur le serveur en 'Prénom (pseudo)' pour que le bot fonctionne.",
                ephemeral=True
            )
            return
            
        password = getPw(id_fioi)
        await ctx.respond(
            f"Ce message est temporaire. Conservez ce mot de passe en lieu sûr.\n"
            f"```\n"
            f"Identifiant : {id_fioi}\n"
            f"Mot de passe : {password}\n"
            f"```",
            ephemeral=True
        )
    except Exception as e:
        await ctx.respond(
            "Une erreur est survenue lors de la génération du mot de passe.",
            ephemeral=True
        )
        print(f"Password generation error for {ctx.author}: {e}")

@slash("debug")
async def debug(ctx : ApplicationContext):
    isOk = await bot.is_owner(ctx.author)
    if isOk:
        await bot.ranking.update()
    await ctx.respond("Ok" if isOk else "Interdit", ephemeral=True)

@slash("Supprimer les scores et les rôles")
async def clear(ctx: ApplicationContext):
    if not await bot.is_owner(ctx.author):
        await ctx.respond("Interdit.", ephemeral=True)
        return
        
    view = ConfirmView(ctx.author)
    await ctx.respond(
        "⚠️ Êtes-vous sûr de vouloir enlever les rôles debrief/classement et supprimer **tous** les scores ?",
        view=view,
        ephemeral=True
    )
    
    await view.wait()
    if view.value is None:
        await ctx.edit(content="Timeout", view=None)
    elif view.value:
        await ctx.edit(content="En cours..", view=None)
        bot.data.delete_all()
        await bot.ranking.update()
        async for m in bot.guild_fioi.fetch_members():
            if bot.role_debrief in m.roles:
                print(m.name)
                await m.remove_roles(bot.role_ranking, bot.role_debrief)
        await ctx.edit(content="Done. Ne pas oublier la config.", view=None)
    else:
        await ctx.edit(content="Opération annulée.", view=None)

def _extract_id_from_name(display_name: str):
    """
    Returns None if the display name is not in the expected format.
    
    >>> _extract_id_from_name("André-Pierre (lapcoder)")
    'lapcoder'
    >>> _extract_id_from_name("Test (userABC_42)")
    'userABC_42'
    >>> _extract_id_from_name("Test (invalid@id)")
    >>> _extract_id_from_name("Test (no spaces)")
    >>> _extract_id_from_name("Multiple (id1) (id2)")
    >>> _extract_id_from_name("(ordre) Important")
    """
    pattern = r'^[^(]+\(([a-zA-Z0-9_]+)\)$'
    match = re.match(pattern, display_name.strip())
    return match.group(1) if match else None

if __name__ == "__main__":
    bot.run(os.environ["TOKEN_FIOI"].rstrip('\n'))
