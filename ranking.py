from collections import defaultdict
from dataclasses import dataclass
import discord
from config import cfg

@dataclass
class ProblemStats:
    scores_distribution: defaultdict
    average: float

class Ranking:    
    def __init__(self, bot):
        self.bot = bot
        self.EMBED_MAX_LENGTH = 1024
        self.EMPTY_FIELD = "Vide"

    async def update(self):
        """Updates the ranking message in the #classement channel."""
        try:
            sorted_scores = self._sort_scores()
            embed = await self._create_ranking_embed(sorted_scores)
            await self._update_ranking_message(embed)
        except Exception as e:
            print(f"Error updating rankings: {e}")

    def _sort_scores(self):
        """Returns scores sorted in descending order by total score."""
        return sorted(self.bot.data.scan(), key=lambda x: -sum(x[1]))

    async def _create_ranking_embed(self, sorted_scores):
        """Creates a Discord embed containing the formatted ranking."""
        embed = discord.Embed(title=f"Classement {cfg.contest.NOM_EPREUVE}")
        contents = await self._generate_ranking_contents(sorted_scores)
        
        for content in contents:
            embed.add_field(
                name="\u200b", 
                value=content.rstrip('\n') or self.EMPTY_FIELD, 
                inline=False
            )
        return embed

    async def _generate_ranking_contents(self, sorted_scores):
        """Generates formatted ranking contents split into Discord-friendly chunks."""
        contents = [""]
        rank_class, last_sum = 0, -1

        for raw_rank, (user_id, scores) in enumerate(sorted_scores, 1):
            # rank_class will be something like 1, 1, 3, 4, 4, 4, 7...
            if sum(scores) != last_sum:
                rank_class = raw_rank
            last_sum = sum(scores)

            user = await self._fetch_user(user_id)
            if not user:
                continue

            entry = self._format_ranking_entry(rank_class, user, scores)
            if len(contents[-1] + entry) > self.EMBED_MAX_LENGTH:
                contents.append("")
            contents[-1] += entry

        return contents

    async def _fetch_user(self, user_id):
        """Fetches a user from the guild."""
        try:
            return await self.bot.guild_fioi.fetch_member(user_id)
        except discord.NotFound:
            return None

    def _format_ranking_entry(self, rank, user, scores):
        """Formats a single ranking entry."""
        total_score = sum(scores)
        score_breakdown = "+".join(map(str, scores))
        return f"~{rank}. **{user.display_name} : {total_score}** ({score_breakdown})\n"

    async def _update_ranking_message(self, embed):
        """Updates or sends a new ranking message in the designated channel."""
        existing_message = await self._find_existing_ranking_message()
        
        if existing_message:
            await existing_message.edit(embed=embed)
        else:
            await self.bot.salon_classement.send(embed=embed)

    async def _find_existing_ranking_message(self):
        """Finds the most recent ranking message by the bot."""
        async for msg in self.bot.salon_classement.history(limit=100):
            if msg.author == self.bot.user:
                return msg
        return None

    def calculate_problem_stats(self, scores):
        """Calculates statistics for each problem."""
        if not scores:
            return []

        num_problems = len(scores[0])
        stats = []
        
        for problem_idx in range(num_problems):
            distribution = defaultdict(int)
            total_score = 0
            
            for score_list in scores:
                score = score_list[problem_idx]
                distribution[score] += 1
                total_score += score
                
            average = total_score / len(scores)
            stats.append(ProblemStats(distribution, average))
            
        return stats

    def format_stats(self, stats, participant_count):
        """Formats problem statistics into a readable string."""
        lines = [
            f"Sur la base des {participant_count} participants ayant déclaré leur score avec /liverank"
        ]

        for i, stat in enumerate(stats, 1):
            score_info = sorted(stat.scores_distribution.items(), reverse=True)
            score_str = " / ".join(
                f"{score}% (x{count})" 
                for score, count in score_info
            )
            lines.append(
                f"p{i} (moyenne {round(stat.average)}%): {score_str}"
            )

        return "\n".join(lines)
