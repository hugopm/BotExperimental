from data import BotData
data = BotData()

import os, sys
token = os.environ["TOKEN_FIOI"].rstrip('\n')

import discord

bot = discord.Bot()
guild_fioi_id = 696724725279359097
def fioi_slash(**kwargs):
    return bot.slash_command(guild_ids=[guild_fioi_id], **kwargs)
guild_fioi = None
role_debrief = None
role_ranking = None
salon_classement = None
@bot.event
async def on_ready():
    global guild_fioi, role_debrief, role_ranking, salon_classement
    print(f"We have logged in as {bot.user}")
    guild_fioi = await bot.fetch_guild(guild_fioi_id)
    role_debrief = guild_fioi.get_role(1017111368547176449)
    role_ranking = guild_fioi.get_role(1063951772332339271)
    salon_classement = await guild_fioi.fetch_channel(1063952121180979311)
    assert(salon_classement != None)
    await update_liverank()


class Confirm(discord.ui.View):
    def __init__(self, author):
        super().__init__()
        self.value = None
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author

    @discord.ui.button(label="J'ai fini !", style=discord.ButtonStyle.green)
    async def confirm_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.value = True
        self.stop()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.grey)
    async def cancel_callback(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.value = False
        self.stop()


@fioi_slash(description="J'ai fini l'épreuve")
async def debrief(ctx : discord.ApplicationContext):
    if role_debrief in ctx.author.roles:
        await ctx.respond(f"Vous avez déjà le rôle {role_debrief.name}")
        return
    view = Confirm(ctx.author)
    await ctx.respond(f"{ctx.author.mention}, avez vous bien fini l'épreuve de sélection 1 ? Tout abus pourra entraîner une disqualification.", view=view)
    await view.wait()
    if view.value is None:
        await ctx.edit(content="Timeout", view=None)
    elif view.value:
        await ctx.edit(content=f"Vous avez obtenu le rôle {role_debrief.name} !", view=None)
        await ctx.author.add_roles(role_debrief)
    else:
        await ctx.edit(content="Vous avez annulé la commande. Ce bot n'est pas un jouet, merci de l'utiliser sérieusement.", view=None)

from enum import Enum

@fioi_slash(description="Publier votre score")
async def liverank(ctx : discord.ApplicationContext,
    score : discord.Option(str, "scores séparés par des + (exemple 100+100+50+100+40+10)")):
    if not role_debrief in ctx.author.roles:
        await ctx.respond(f"Vous devez avoir le rôle {role_debrief.name} pour déclarer votre score.", ephemeral=True)
        return
    sl = []
    try:
        sl = score.replace(" ", "").split("+")
        sl = list(map(int, sl))
        assert(len(sl) == 6)
        for x in sl:
            assert (0 <= x and x <= 100)
    except:
        await ctx.respond(f"Vous n'avez pas respecté le format attendu (votre entrée : {score})", ephemeral=True)
        return
    data.set_one(ctx.author.id, sl)
    await ctx.respond("Merci d'avoir publié votre score ! Vous avez débloqué le salon #classement", ephemeral=True)
    await update_liverank()
    await ctx.author.add_roles(role_ranking)

async def update_liverank():
    content = ""
    sorted_scores = sorted(data.scan(), key = lambda x : -sum(x[1]))
    for i, [user_id, sl] in enumerate(sorted_scores, 1):
        user = await guild_fioi.fetch_member(user_id)
        assert(user != None)
        sl_str = "+".join(map(str, sl))
        content += f"**{i}. {user.nick} : {sum(sl)}** ({sl_str})\n"
    if not content:
        content = "Vide"
    ####
    message = None
    async for msg in salon_classement.history(limit=100):
        if msg.author == bot.user:
            message = msg
            break
    if message:
        await message.edit(content=content)
    else:
        await salon_classement.send(content)

@fioi_slash(description="Pour Hugo")
async def debug(ctx):
    isOk = await bot.is_owner(ctx.author)
    if isOk:
        await update_liverank()
    await ctx.respond("Ok" if isOk else "Interdit", ephemeral=True)

bot.run(token)
