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
            "I hope you know ur a fat fuck, biggie",
            "Any racial slur would be a complement to you",
            "I would rather drag my testicles over shattered glass than to talk to you any longer",
            "Even moses cant part that fucking unibrow, ugly fuck",
            "your Ital*an (from iggy)",
            "kys",
            "retard.",
            "retarded is a compliment to you",
            "I hope love never finds ur fugly ahh",
            "Fuckkk 🐺...",
            "flippin Malteser",
            "Fuck you, you ho. Come and say to my face, I'll fuck you in the ass in front of everybody. You bitch.",
            "Whoever's willing to fuck you is just too lazy to jerk off.",
            "God just be making anyone",
            "You should have been a blowjob"
        ]

        msg = f"{ctx.author.mention} insults {member.mention}: **{random.choice(lines)}**"

        await ctx.send(msg)

    # -------------------------
    # THREATEN
    # -------------------------

    @commands.command()
    async def threaten(self, ctx, member: discord.Member):

        lines = [
            "I will pee your pants",
            "I will touch you",
            "*twirls your balls (testicular torsion way)* 🔌😈",
            "I will jiggle your tits",
            "I will send you to I*aly",
            "I will wet your socks (sexually)",
            "🇫🇷"
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
            "That message has been escorted out by security.",
            "Please keep your hands, feet, and words to yourself.",
            "This is a no-weird-zone. Thank you for your cooperation.",
            "Bonk. Go to respectful conversation jail.",
            "That was a bit much. Let’s dial it back.",
            "Socks will remain dry. Boundaries enforced.",
            "International incidents are not permitted here."
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

        await ctx.send(
            f"{ctx.author.mention} stabbed {member.mention}!"
        )

    # -------------------------
    # LICK
    # -------------------------

    @commands.command()
    async def lick(self, ctx, member: discord.Member):

        await ctx.send(
            f"{ctx.author.mention} licked {member.mention}."
        )


async def setup(bot):
    await bot.add_cog(Social(bot))
