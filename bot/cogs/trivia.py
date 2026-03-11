import random
import aiohttp
import discord
from discord.ext import commands

from storage import (
    load_trivia_stats,
    save_trivia_stats,
    load_trivia_streaks,
    save_trivia_streaks,
    load_coins,
    save_coins,
)
from cogs.listeners import update_xp


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


def make_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )


def ensure_user_coins(user_id):
    user_id = str(user_id)
    coins = load_coins()

    if user_id not in coins:
        coins[user_id] = {
            "wallet": 100,
            "bank": 0,
            "last_daily": 0,
            "last_rob": 0,
            "last_beg": 0,
            "last_bankrob": 0,
            "portfolio": {},
            "pending_portfolio": [],
            "trade_meta": {
                "last_trade_ts": {},
                "daily": {"day": "", "count": 0}
            }
        }
        save_coins(coins)

    return coins


def add_trivia_result(uid: str, category: str, correct: bool):
    stats = load_trivia_stats()

    user = stats.setdefault(uid, {})
    cat = user.setdefault(category, {"correct": 0, "attempts": 0})

    cat["attempts"] += 1
    if correct:
        cat["correct"] += 1

    save_trivia_stats(stats)


class TriviaView(discord.ui.View):
    def __init__(self, *, author_id: int, options: list[str], correct_answer: str):
        super().__init__(timeout=20)
        self.author_id = author_id
        self.options = options
        self.correct_answer = correct_answer
        self.chosen_answer = None
        self.timed_out = False

        for i, option in enumerate(options):
            button = discord.ui.Button(
                label=str(i + 1),
                style=discord.ButtonStyle.secondary
            )
            button.callback = self.make_callback(option)
            self.add_item(button)

    def make_callback(self, option):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                return await interaction.response.send_message(
                    embed=make_embed("Trivia", "This question isn't for you."),
                    ephemeral=True
                )

            self.chosen_answer = option

            for child in self.children:
                child.disabled = True

            await interaction.response.edit_message(view=self)
            self.stop()

        return callback

    async def on_timeout(self):
        self.timed_out = True
        for child in self.children:
            child.disabled = True


class Trivia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # TRIVIA
    # -------------------------

    @commands.hybrid_command(
        name="trivia",
        description="Answer a trivia question."
    )
    async def trivia(self, ctx):

        url = "https://the-trivia-api.com/v2/questions"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await ctx.send(
                            embed=make_embed("Trivia", "Trivia API unavailable.")
                        )
                    data = await resp.json()

        except Exception:
            return await ctx.send(
                embed=make_embed("Trivia", "Trivia API unavailable.")
            )

        if not data:
            return await ctx.send(
                embed=make_embed("Trivia", "No trivia question was returned.")
            )

        q = data[0]

        question = q["question"]["text"]
        correct = q["correctAnswer"]
        options = q["incorrectAnswers"] + [correct]

        random.shuffle(options)

        raw_category = q.get("category", "General")
        if isinstance(raw_category, list):
            category = str(raw_category[0] if raw_category else "General").title()
        else:
            category = str(raw_category).title()

        option_text = "\n".join(
            f"**{i + 1}.** {opt}" for i, opt in enumerate(options)
        )

        embed = discord.Embed(
            title="Trivia",
            description=f"**{question}**\n\n{option_text}",
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Category: {category}")

        view = TriviaView(
            author_id=ctx.author.id,
            options=options,
            correct_answer=correct
        )

        msg = await ctx.send(embed=embed, view=view)

        await view.wait()

        if view.timed_out:
            await msg.edit(view=view)
            return await ctx.send(
                embed=make_embed("Trivia", f"Time expired.\n\nCorrect answer: **{correct}**")
            )

        chosen = view.chosen_answer
        uid = str(ctx.author.id)

        streaks = load_trivia_streaks()
        streak = int(streaks.get(uid, 0))

        if chosen == correct:
            streak += 1

            reward_base = 50
            streak_bonus = 5 * min(streak - 1, 10)
            reward = reward_base + streak_bonus

            coins = ensure_user_coins(ctx.author.id)
            coins[uid]["wallet"] += reward
            save_coins(coins)

            try:
                if ctx.guild:
                    await update_xp(self.bot, ctx.author.id, ctx.guild.id, 20)
            except Exception:
                pass

            add_trivia_result(uid, category, True)

            streaks[uid] = streak
            save_trivia_streaks(streaks)

            embed = discord.Embed(
                title="Correct",
                description=f"+{reward} coins\nStreak: {streak}",
                color=EMBED_COLOR
            )

            await ctx.send(embed=embed)

        else:
            add_trivia_result(uid, category, False)

            streaks[uid] = 0
            save_trivia_streaks(streaks)

            embed = discord.Embed(
                title="Incorrect",
                description=f"Correct answer: **{correct}**",
                color=EMBED_COLOR
            )

            await ctx.send(embed=embed)

    # -------------------------
    # STATS
    # -------------------------

    @commands.hybrid_command(
        name="triviastats",
        description="View trivia stats."
    )
    async def triviastats(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        stats = load_trivia_stats()
        uid = str(member.id)

        if uid not in stats:
            return await ctx.send(
                embed=make_embed("Trivia Stats", "No trivia stats yet.")
            )

        user_stats = stats[uid]

        lines = []
        total_attempts = 0
        total_correct = 0

        for cat, rec in user_stats.items():
            attempts = rec["attempts"]
            correct = rec["correct"]

            acc = (correct / attempts * 100) if attempts else 0

            total_attempts += attempts
            total_correct += correct

            lines.append(
                f"**{cat}** — {correct}/{attempts} ({acc:.0f}%)"
            )

        embed = discord.Embed(
            title=f"{member.display_name} — Trivia Stats",
            description="\n".join(lines),
            color=EMBED_COLOR
        )

        embed.set_footer(
            text=f"Total: {total_correct}/{total_attempts}"
        )

        await ctx.send(embed=embed)

    # -------------------------
    # LEADERBOARD
    # -------------------------

    @commands.hybrid_command(
        name="trivialeaderboard",
        description="Trivia leaderboard."
    )
    async def trivialeaderboard(self, ctx):

        if not ctx.guild:
            return await ctx.send(
                embed=make_embed("Trivia Leaderboard", "This command only works in servers.")
            )

        stats = load_trivia_stats()
        leaderboard = []

        for member in ctx.guild.members:
            if member.bot:
                continue

            uid = str(member.id)

            if uid not in stats:
                continue

            user_stats = stats[uid]

            correct = sum(x["correct"] for x in user_stats.values())
            attempts = sum(x["attempts"] for x in user_stats.values())

            leaderboard.append((member, correct, attempts))

        leaderboard.sort(key=lambda x: x[1], reverse=True)

        lines = []

        for i, (member, correct, attempts) in enumerate(leaderboard[:10], 1):
            acc = (correct / attempts * 100) if attempts else 0

            lines.append(
                f"{i}. {member.mention} — {correct}/{attempts} ({acc:.0f}%)"
            )

        embed = discord.Embed(
            title="Trivia Leaderboard",
            description="\n".join(lines) if lines else "No players yet.",
            color=EMBED_COLOR
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Trivia(bot))
