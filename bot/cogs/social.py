import discord
from discord.ext import commands
import random


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


def make_embed(title: str, description: str, footer: str):
    embed = discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )
    embed.set_footer(text=footer)
    return embed


class Social(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # INSULT
    # -------------------------

    @commands.hybrid_command(
        name="insult",
        description="Insult another user."
    )
    async def insult(self, ctx, member: discord.Member):

        if member.bot:
            return await ctx.send(
                embed=discord.Embed(
                    title="Insult",
                    description="I won't insult bots.",
                    color=EMBED_COLOR
                )
            )

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

        embed = make_embed(
            "Insult",
            random.choice(lines),
            f"{ctx.author.display_name} → {member.display_name}"
        )

        embed.description = f"{ctx.author.mention} → {member.mention}\n\n{embed.description}"

        await ctx.send(embed=embed)

    # -------------------------
    # THREATEN
    # -------------------------

    @commands.hybrid_command(
        name="threaten",
        description="Threaten another user."
    )
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

        embed = make_embed(
            "Threat",
            random.choice(lines),
            f"{ctx.author.display_name} → {member.display_name}"
        )

        embed.description = f"{ctx.author.mention} → {member.mention}\n\n{embed.description}"

        await ctx.send(embed=embed)

    # -------------------------
    # WARN
    # -------------------------

    @commands.hybrid_command(
        name="warn",
        description="Warn another user."
    )
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

        embed = make_embed(
            "Warning",
            random.choice(lines),
            f"{ctx.author.display_name} → {member.display_name}"
        )

        embed.description = f"{ctx.author.mention} → {member.mention}\n\n{embed.description}"

        await ctx.send(embed=embed)

    # -------------------------
    # COMPLIMENT
    # -------------------------

    @commands.hybrid_command(
        name="compliment",
        description="Compliment another user."
    )
    async def compliment(self, ctx, member: discord.Member):

        lines = [
            "You're the MVP of this server.",
            "You make this place better.",
            "You're smarter than the average Discord user.",
            "Your memes are elite tier.",
            "You're carrying this server."
        ]

        embed = make_embed(
            "Compliment",
            random.choice(lines),
            f"{ctx.author.display_name} → {member.display_name}"
        )

        embed.description = f"{ctx.author.mention} → {member.mention}\n\n{embed.description}"

        await ctx.send(embed=embed)

    # -------------------------
    # STAB
    # -------------------------

    @commands.hybrid_command(
        name="stab",
        description="Stab another user."
    )
    async def stab(self, ctx, member: discord.Member):

        embed = make_embed(
            "Action",
            f"{ctx.author.mention} stabbed {member.mention}.",
            f"{ctx.author.display_name} → {member.display_name}"
        )

        await ctx.send(embed=embed)

    # -------------------------
    # LICK
    # -------------------------

    @commands.hybrid_command(
        name="lick",
        description="Lick another user."
    )
    async def lick(self, ctx, member: discord.Member):

        embed = make_embed(
            "Action",
            f"{ctx.author.mention} licked {member.mention}.",
            f"{ctx.author.display_name} → {member.display_name}"
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Social(bot))
