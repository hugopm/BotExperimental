import os, sys
token = os.environ["TOKEN_FIOI"].rstrip('\n')

import discord

bot = discord.Bot()
guild_fioi_id = 696724725279359097
sc = bot.slash_command(guild_ids=[guild_fioi_id])
guild_fioi = None
role_debrief = None
@bot.event
async def on_ready():
    global guild_fioi, role_debrief
    print(f"We have logged in as {bot.user}")
    guild_fioi = await bot.fetch_guild(guild_fioi_id)
    role_debrief = guild_fioi.get_role(1017111368547176449)


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


@sc
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

bot.run(token)
