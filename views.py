import discord
from config import cfg

class ConfirmView(discord.ui.View):
    """View for confirming actions with yes/no buttons"""
    def __init__(self, author):
        super().__init__()
        self.value = None
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author

    @discord.ui.button(label="J'ai fini !", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.grey)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()

class ScoreModal(discord.ui.Modal):
    """Modal for submitting scores"""
    def __init__(self, bot, *args, **kwargs):
        super().__init__(title=f"Score détaillé ({cfg.contest.ABC})", *args, **kwargs)
        self.bot = bot
        
        score_input = discord.ui.InputText(
            label="Scores",
            placeholder=f"Exemple : {cfg.contest.EXEMPLE}"
        )
        self.add_item(score_input)

    async def callback(self, interaction: discord.Interaction):
        score = self.children[0].value
        if not self._validate_score(score):
            await interaction.response.send_message(
                f"Format incorrect. Exemple : {cfg.contest.EXEMPLE}", 
                ephemeral=True
            )
            return

        await self._process_score(interaction)
        self.stop()

    def _validate_score(self, score: str) -> bool:
        try:
            scores = list(map(int, score.replace(" ", "").split("+")))
            return (len(scores) == cfg.contest.NB_PROBLEMS and 
                   all(0 <= x <= 100 for x in scores))
        except Exception:
            return False

    async def _process_score(self, interaction: discord.Interaction):
        scores = list(map(int, self.children[0].value.replace(" ", "").split("+")))
        self.bot.data.set_one(interaction.user.id, scores)
        await interaction.response.send_message(
            "Score publié ! Vous avez débloqué le salon #classement."
        )
        await interaction.user.add_roles(self.bot.role_ranking)
        await self.bot.ranking.update()
