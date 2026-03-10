import asyncio
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

# If you moved update_xp into listeners.py, keep this import.
# If it lives somewhere else, change this import to match your project.
from cogs.listeners import update_xp


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

    else:
        data = coins[user_id]
        data.setdefault("wallet", 100)
        data.setdefault("bank", 0)
        data.setdefault("last_daily", 0)
        data.setdefault("last_rob", 0)
        data.setdefault("last_beg", 0)
        data.setdefault("last_bankrob", 0)
        data.setdefault("portfolio", {})
        data.setdefault("pending_portfolio", [])
        data.setdefault("trade_meta", {"last_trade_ts": {}, "daily": {"day": "", "count": 0}})
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


class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trivia", help="Answer a trivia question with emoji reactions!")
    async def trivia(self, ctx: commands.Context):
        url = "https://the-trivia-api.com/v2/questions"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Could not reach Trivia API. Try again later.")
                    data = await resp.json()
        except Exception:
            return await ctx.send("❌ Could not reach Trivia API. Try again later.")

        if not data:
            return await ctx.send("❌ No trivia received.")

        q = data[0]

        question = q["question"]["text"]
        correct = q["correctAnswer"]
        options = q["incorrectAnswers"] + [correct]
        random.shuffle(options)

        raw_cat = q.get("category", "General")
        category = (raw_cat[0] if isinstance(raw_cat, list) and raw_cat else raw_cat)
        category = str(category).title()

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        option_lines = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))

        embed = discord.Embed(
            title="🧠 Trivia Time!",
            description=f"**{question}**\n\n{option_lines}\n\nReact with the correct answer!",
            color=discord.Color.blue()
        )

        msg = await ctx.send(embed=embed)

        for emoji in emojis:
            try:
                await msg.add_reaction(emoji)
            except discord.HTTPException:
                pass

        def check(payload: discord.RawReactionActionEvent):
            return (
                payload.user_id == ctx.author.id
                and payload.message_id == msg.id
                and str(payload.emoji) in emojis
            )

        try:
            payload = await self.bot.wait_for(
                "raw_reaction_add",
                timeout=20.0,
                check=check
            )
        except asyncio.TimeoutError:
            return await ctx.send(f"⏰ Out of time! The correct answer was **{correct}**.")

        choice_index = emojis.index(str(payload.emoji))
        chosen = options[choice_index]

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
                await update_xp(self.bot, ctx.author.id, ctx.guild.id, 20)
            except Exception:
                pass

            add_trivia_result(uid, category, True)
            streaks[uid] = streak
            save_trivia_streaks(streaks)

            await ctx.send(f"✅ Correct! **+{reward}** coins (streak **{streak}**).")
        else:
            add_trivia_result(uid, category, False)
            streaks[uid] = 0
            save_trivia_streaks(streaks)

            await ctx.send(f"❌ Wrong! The correct answer was **{correct}**. Streak reset.")

    @commands.command(name="triviastats", help="Show trivia stats. Usage: !triviastats [@user]")
    async def triviastats(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        uid = str(member.id)

        stats = load_trivia_stats()
        user_stats = stats.get(uid)

        if not user_stats:
            return await ctx.send(f"📊 No trivia stats for **{member.display_name}** yet.")

        rows = []
        total_attempts = 0
        total_correct = 0

        for category, rec in user_stats.items():
            attempts = int(rec.get("attempts", 0))
            correct = int(rec.get("correct", 0))
            wrong = attempts - correct
            acc = (correct / attempts * 100.0) if attempts else 0.0

            total_attempts += attempts
            total_correct += correct
            rows.append((category, correct, wrong, attempts, acc))

        rows.sort(key=lambda r: r[3], reverse=True)

        lines = []
        for category, correct, wrong, attempts, acc in rows[:20]:
            lines.append(f"**{category}** — ✅ {correct} · ❌ {wrong} · {attempts} total · {acc:.0f}%")

        overall_acc = (total_correct / total_attempts * 100.0) if total_attempts else 0.0

        embed = discord.Embed(
            title=f"📊 Trivia Stats — {member.display_name}",
            description="\n".join(lines) if lines else "No data yet.",
            color=discord.Color.teal()
        )
        embed.set_footer(text=f"Overall: ✅ {total_correct} / {total_attempts} · {overall_acc:.0f}% accuracy")

        await ctx.send(embed=embed)

    @commands.command(
        name="trivialeaderboard",
        help="Show the server trivia leaderboard. Usage: !trivialeaderboard [correct|accuracy|attempts] [min_attempts] [count]"
    )
    async def trivialeaderboard(self, ctx: commands.Context, metric: str = "correct", min_attempts: int = 1, count: int = 10):
        metric = metric.lower().strip()
        if metric not in ("correct", "accuracy", "attempts"):
            metric = "correct"

        try:
            min_attempts = max(0, int(min_attempts))
        except Exception:
            min_attempts = 1

        try:
            count = max(3, min(25, int(count)))
        except Exception:
            count = 10

        stats = load_trivia_stats()
        guild = ctx.guild

        leaderboard = []

        for member in guild.members:
            if member.bot:
                continue

            uid = str(member.id)
            user_stats = stats.get(uid)
            if not user_stats:
                continue

            total_attempts = sum(int(rec.get("attempts", 0)) for rec in user_stats.values())
            total_correct = sum(int(rec.get("correct", 0)) for rec in user_stats.values())

            if total_attempts < min_attempts or total_attempts == 0:
                continue

            acc = (total_correct / total_attempts) * 100.0

            leaderboard.append({
                "member": member,
                "attempts": total_attempts,
                "correct": total_correct,
                "accuracy": acc,
            })

        if not leaderboard:
            return await ctx.send(f"📊 No qualifying players yet (min attempts: {min_attempts}).")

        if metric == "correct":
            leaderboard.sort(key=lambda r: (r["correct"], r["accuracy"], r["attempts"]), reverse=True)
            title = "🏆 Trivia Leaderboard — Most Correct"
        elif metric == "accuracy":
            leaderboard.sort(key=lambda r: (r["accuracy"], r["attempts"], r["correct"]), reverse=True)
            title = "🎯 Trivia Leaderboard — Best Accuracy"
        else:
            leaderboard.sort(key=lambda r: (r["attempts"], r["correct"], r["accuracy"]), reverse=True)
            title = "⏱️ Trivia Leaderboard — Most Attempts"

        lines = []
        for i, row in enumerate(leaderboard[:count], start=1):
            m = row["member"]
            lines.append(
                f"**{i}.** {m.mention} — "
                f"✅ {row['correct']} · ❌ {row['attempts'] - row['correct']} · "
                f"{row['attempts']} attempts · {row['accuracy']:.0f}% acc"
            )

        embed = discord.Embed(
            title=title,
            description="\n".join(lines),
            color=discord.Color.teal()
        )
        embed.set_footer(text=f"Filter: min attempts ≥ {min_attempts} • Metric: {metric}")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Trivia(bot))
