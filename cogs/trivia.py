# cogs/trivia.py

import discord
from discord.ext import commands
import aiohttp
import random

from storage import load_trivia_stats, save_trivia_stats


class Trivia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def trivia(self, ctx):

        url = "https://the-trivia-api.com/v2/questions"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:

                if resp.status != 200:
                    return await ctx.send("Trivia API error.")

                data = await resp.json()

        q = data[0]

        question = q["question"]["text"]
        correct = q["correctAnswer"]
        options = q["incorrectAnswers"] + [correct]

        random.shuffle(options)

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        desc = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))

        embed = discord.Embed(
            title="Trivia",
            description=f"{question}\n\n{desc}",
            color=discord.Color.blue()
        )

        msg = await ctx.send(embed=embed)

        for emoji in emojis:
            await msg.add_reaction(emoji)

        def check(payload):

            return (
                payload.user_id == ctx.author.id
                and payload.message_id == msg.id
                and str(payload.emoji) in emojis
            )

        try:

            payload = await self.bot.wait_for(
                "raw_reaction_add",
                timeout=20,
                check=check
            )

        except:

            return await ctx.send(f"Time up! Answer was **{correct}**")

        choice = emojis.index(str(payload.emoji))
        selected = options[choice]

        stats = load_trivia_stats()
        uid = str(ctx.author.id)

        stats.setdefault(uid, {"correct": 0, "wrong": 0})

        if selected == correct:

            stats[uid]["correct"] += 1
            msg = "Correct!"

        else:

            stats[uid]["wrong"] += 1
            msg = f"Wrong! Answer: **{correct}**"

        save_trivia_stats(stats)

        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(Trivia(bot))
