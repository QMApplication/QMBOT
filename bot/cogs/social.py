import discord
from discord.ext import commands
import random

from storage import load_actions, save_actions


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


def make_embed(title: str, description: str, footer: str | None = None):
    embed = discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )

    if footer:
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
                embed=make_embed("Insult", "I won't insult bots.")
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
            f"{ctx.author.mention} → {member.mention}\n\n{random.choice(lines)}",
            f"{ctx.author.display_name} → {member.display_name}"
        )

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
            f"{ctx.author.mention} → {member.mention}\n\n{random.choice(lines)}",
            f"{ctx.author.display_name} → {member.display_name}"
        )

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
            f"{ctx.author.mention} → {member.mention}\n\n{random.choice(lines)}",
            f"{ctx.author.display_name} → {member.display_name}"
        )

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
            f"{ctx.author.mention} → {member.mention}\n\n{random.choice(lines)}",
            f"{ctx.author.display_name} → {member.display_name}"
        )

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

    # -------------------------
    # ACTION CREATE
    # -------------------------

    @commands.hybrid_command(
        name="actioncreate",
        description="Create a custom action."
    )
    @commands.has_permissions(manage_guild=True)
    async def actioncreate(self, ctx, verb: str, plural: str):

        actions = load_actions()
        verb = verb.lower().strip()
        plural = plural.strip()

        if not verb.isalpha():
            return await ctx.send(
                embed=make_embed("Action Create", "Verb must only contain letters.")
            )

        if verb in actions:
            return await ctx.send(
                embed=make_embed("Action Create", "That action already exists.")
            )

        actions[verb] = plural
        save_actions(actions)

        embed = make_embed(
            "Action Created",
            (
                f"Verb: `{verb}`\n"
                f"Output: `{plural}`\n\n"
                f"Use it with `/action {verb} @user`"
            )
        )

        await ctx.send(embed=embed)

    # -------------------------
    # ACTION
    # -------------------------

    @commands.hybrid_command(
        name="action",
        description="Use a custom action."
    )
    async def action(self, ctx, verb: str, member: discord.Member):

        actions = load_actions()
        verb = verb.lower().strip()

        if verb not in actions:
            return await ctx.send(
                embed=make_embed("Action", "That action does not exist.")
            )

        plural = actions[verb]

        embed = make_embed(
            "Action",
            f"{ctx.author.mention} {plural} {member.mention}.",
            f"{ctx.author.display_name} → {member.display_name}"
        )

        await ctx.send(embed=embed)

    # -------------------------
    # ACTION LIST
    # -------------------------

    @commands.hybrid_command(
        name="actionlist",
        description="Show all custom actions."
    )
    async def actionlist(self, ctx):

        actions = load_actions()

        if not actions:
            return await ctx.send(
                embed=make_embed("Action List", "No custom actions exist yet.")
            )

        verbs = sorted(actions.keys())

        lines = []
        for verb in verbs:
            lines.append(f"`{verb}` → {actions[verb]}")

        embed = make_embed(
            "Custom Actions",
            "\n".join(lines)
        )

        await ctx.send(embed=embed)

    # -------------------------
    # ACTION DELETE
    # -------------------------

    @commands.hybrid_command(
        name="actiondelete",
        description="Delete a custom action."
    )
    @commands.has_permissions(manage_guild=True)
    async def actiondelete(self, ctx, verb: str):

        actions = load_actions()
        verb = verb.lower().strip()

        if verb not in actions:
            return await ctx.send(
                embed=make_embed("Action Delete", "That action does not exist.")
            )

        removed = actions.pop(verb)
        save_actions(actions)

        embed = make_embed(
            "Action Deleted",
            f"Removed `{verb}` → {removed}"
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Social(bot))
