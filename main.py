from data import BotData
data = BotData()

import os, sys
token = os.environ["TOKEN_FIOI"].rstrip('\n')

from collections import defaultdict
import discord
# intents=discord.Intents(members=True)
bot = discord.Bot()
guild_fioi_id = 696724725279359097
def fioi_slash(**kwargs):
    return bot.slash_command(guild_ids=[guild_fioi_id], **kwargs)
guild_fioi = None
role_debrief = None
role_ranking = None
role_participant = None
salon_classement = None
@bot.event
async def on_ready():
    global guild_fioi, role_debrief, role_ranking, role_participant, salon_classement
    print(f"We have logged in as {bot.user}")
    guild_fioi = await bot.fetch_guild(guild_fioi_id)
    role_debrief = guild_fioi.get_role(1017111368547176449)
    role_ranking = guild_fioi.get_role(1063951772332339271)
    role_participant = guild_fioi.get_role(1064202998194126979)
    salon_classement = await guild_fioi.fetch_channel(1063952121180979311)
    assert(salon_classement != None)
    # async for m in guild_fioi.fetch_members():
    #     if role_debrief in m.roles:
    #         await m.remove_roles(role_ranking, role_debrief)
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
    await ctx.respond(f"{ctx.author.mention}, avez vous bien fini **le FARIO** (et toutes les épreuves de sélection précédentes) ? Tout abus pourra entraîner une disqualification.", view=view)
    await view.wait()
    if view.value is None:
        await ctx.edit(content="Timeout", view=None)
    elif view.value:
        await ctx.edit(content=f"Vous avez obtenu le rôle {role_debrief.name} !", view=None)
        await ctx.author.add_roles(role_debrief, role_participant)
    else:
        await ctx.edit(content="Vous avez annulé la commande. Ce bot n'est pas un jouet, merci de l'utiliser sérieusement.", view=None)

class LiverankModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(title = "Score détaillé (A+B+C)", *args, **kwargs)
        it = discord.ui.InputText(label="Scores")
        it.placeholder = "Exemple : 100+80+50"
        self.add_item(it)

    async def callback(self, interaction: discord.Interaction):
        score = self.children[0].value
        sl = []
        try:
            sl = score.replace(" ", "").split("+")
            sl = list(map(int, sl))
            assert(len(sl) == data.NB_PROBLEMS)
            for x in sl:
                assert (0 <= x and x <= 100)
        except:
            await interaction.response.send_message(f"Vous n'avez pas respecté le format attendu (votre entrée : {score}). Exemple d'entrée correcte : 100+80+50+70+100", ephemeral=True)
            return
        data.set_one(interaction.user.id, sl)
        await interaction.response.send_message("Merci d'avoir publié votre score ! Vous avez débloqué le salon #classement.")
        await update_liverank()
        await interaction.user.add_roles(role_ranking)
        self.stop()

@fioi_slash(description="Publier votre score")
async def liverank(ctx : discord.ApplicationContext):
    if not role_debrief in ctx.author.roles:
        await ctx.respond(f"Vous devez avoir le rôle {role_debrief.name} pour déclarer votre score.", ephemeral=True)
        return
    modal = LiverankModal(timeout = 10)
    await ctx.send_modal(modal)
    await modal.wait()

def get_nick(user):
    return user.nick if user.nick else user.name

async def update_liverank():
    content = ""
    sorted_scores = sorted(data.scan(), key = lambda x : -sum(x[1]))
    idClass, lastSum = 0, -1
    for rawId, [user_id, sl] in enumerate(sorted_scores, 1):
        if sum(sl) != lastSum:
            idClass = rawId
        lastSum = sum(sl)
        user = await guild_fioi.fetch_member(user_id)
        assert(user != None)
        sl_str = "+".join(map(str, sl))
        content += f"**{idClass}. {get_nick(user)} : {sum(sl)}** ({sl_str})\n"
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
async def debug(ctx : discord.ApplicationContext):
    isOk = await bot.is_owner(ctx.author)
    if isOk:
        await update_liverank()
    await ctx.respond("Ok" if isOk else "Interdit", ephemeral=True)

@fioi_slash(description="Statistiques de l'épreuve")
async def stats(ctx : discord.ApplicationContext):
    if ctx.channel.id != 1017111913387282523:
        await ctx.respond("Cette commande doit être lancée dans #debrief-epreuve", ephemeral=True)
        return
    scores = list(map(lambda x: x[1], data.scan()))
    nb_cont = len(scores)
    inv = [defaultdict(lambda: 0) for _ in range(data.NB_PROBLEMS)]
    moyenne = [0.0 for _ in range(data.NB_PROBLEMS)]
    for sl in scores:
        for i in range(data.NB_PROBLEMS):
            inv[i][sl[i]] += 1
            moyenne[i] += sl[i] / nb_cont
    content = f"Sur la base des {nb_cont} participants ayant déclaré leur score avec /liverank\n"
    for i in range(data.NB_PROBLEMS):
        info = sorted(inv[i].items(), reverse=True)
        info = list(map(lambda x: f"{x[0]}% (x{x[1]})", info))
        info = " / ".join(info)
        content += f"p{i+1} (moyenne {round(moyenne[i])}%): " + info + "\n"
    
    await ctx.respond(content)

bot.run(token)
