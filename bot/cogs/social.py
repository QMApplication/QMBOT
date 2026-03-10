import discord
from discord.ext import commands
import random


class Social(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # INSULT
    # -------------------------

    @commands.command()
    async def insult(self, ctx, member: discord.Member):

        if member.bot:
            return await ctx.send("🤖 I won't insult bots.")

        lines = [
            "has the IQ of a damp sponge.",
            "could lose a debate with a brick.",
            "once tried to microwave a salad.",
            "is proof evolution can go backwards.",
            "has the strategic thinking of a potato."
        ]

        msg = f"{ctx.author.mention} insults {member.mention}: **{random.choice(lines)}**"

        await ctx.send(msg)

    # -------------------------
    # THREATEN
    # -------------------------

    @commands.command()
    async def threaten(self, ctx, member: discord.Member):

        lines = [
            "I'm coming for your kneecaps.",
            "sleep with one eye open tonight.",
            "you better watch your back.",
            "your days are numbered.",
            "this server isn't big enough for both of us."
        ]

        await ctx.send(
            f"{ctx.author.mention} threatens {member.mention}: **{random.choice(lines)}**"
        )

    # -------------------------
    # WARN
    # -------------------------

    @commands.command()
    async def warn(self, ctx, member: discord.Member):

        lines = [
            "This is your final warning.",
            "Don't test my patience.",
            "Behave yourself.",
            "You're walking on thin ice.",
            "Consider yourself warned."
        ]

        await ctx.send(
            f"⚠️ {ctx.author.mention} warns {member.mention}: **{random.choice(lines)}**"
        )

    # -------------------------
    # COMPLIMENT
    # -------------------------

    @commands.command()
    async def compliment(self, ctx, member: discord.Member):

        lines = [
            "You're the MVP of this server.",
            "You make this place better.",
            "You're smarter than the average Discord user.",
            "Your memes are elite tier.",
            "You're carrying this server."
        ]

        await ctx.send(
            f"{ctx.author.mention} compliments {member.mention}: **{random.choice(lines)}**"
        )

    # -------------------------
    # STAB
    # -------------------------

    @commands.command()
    async def stab(self, ctx, member: discord.Member):

        lines = [
            "🔪 Critical hit!",
            "🗡️ Sneak attack!",
            "💀 Fatal blow!",
            "🩸 That looked painful.",
            "⚔️ Direct strike."
        ]

        await ctx.send(
            f"{ctx.author.mention} stabbed {member.mention}! {random.choice(lines)}"
        )

    # -------------------------
    # LICK
    # -------------------------

    @commands.command()
    async def lick(self, ctx, member: discord.Member):

        lines = [
            "😳 That was unexpected.",
            "👅 That's kinda weird.",
            "🤨 Why would you do that?",
            "😶 Everyone saw that.",
            "🫣 That's embarrassing."
        ]

        await ctx.send(
            f"{ctx.author.mention} licked {member.mention}. {random.choice(lines)}"
        )


async def setup(bot):
    await bot.add_cog(Social(bot))
