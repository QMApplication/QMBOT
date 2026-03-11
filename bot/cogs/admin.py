import discord
from discord.ext import commands

from config import (
    SUGGESTION_CHANNEL_ID,
    ANNOUNCEMENT_CHANNEL_ID,
    PACKAGE_USER_ID,
)
from storage import load_suggestions, save_suggestions
from cogs.tasks import dm_package_to_user


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


class Admin(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # SUGGEST
    # -------------------------

    @commands.hybrid_command(
        name="suggest",
        description="Submit a suggestion for the server."
    )
    async def suggest(self, ctx: commands.Context, *, suggestion: str):

        channel = self.bot.get_channel(SUGGESTION_CHANNEL_ID)

        if not channel:
            return await ctx.send("Suggestion channel not configured.")

        suggestions = load_suggestions()

        entry = {
            "user": ctx.author.id,
            "text": suggestion
        }

        suggestions.append(entry)
        save_suggestions(suggestions)

        embed = discord.Embed(
            title="Suggestion",
            description=suggestion,
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"From {ctx.author.display_name}")

        msg = await channel.send(embed=embed)

        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        confirm = discord.Embed(
            title="Submitted",
            description="Your suggestion has been sent.",
            color=EMBED_COLOR
        )

        await ctx.send(embed=confirm)

    # -------------------------
    # ANNOUNCEMENT
    # -------------------------

    @commands.hybrid_command(
        name="announcement",
        description="Send a server announcement."
    )
    @commands.has_permissions(manage_guild=True)
    async def announcement(self, ctx: commands.Context, *, message: str):

        channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)

        if not channel:
            return await ctx.send("Announcement channel not configured.")

        embed = discord.Embed(
            title="Announcement",
            description=message,
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Posted by {ctx.author.display_name}")

        await channel.send(embed=embed)

        confirm = discord.Embed(
            title="Sent",
            description="Announcement posted successfully.",
            color=EMBED_COLOR
        )

        await ctx.send(embed=confirm)

    # -------------------------
    # PACKAGE (manual backup)
    # -------------------------

    @commands.hybrid_command(
        name="package",
        description="Send a manual backup of the bot data."
    )
    async def package(self, ctx: commands.Context):

        if ctx.author.id != PACKAGE_USER_ID:
            return await ctx.send("You are not authorised.")

        success = await dm_package_to_user(
            self.bot,
            PACKAGE_USER_ID,
            reason="Manual package command"
        )

        if success:
            embed = discord.Embed(
                title="Backup",
                description="Backup sent successfully.",
                color=EMBED_COLOR
            )
        else:
            embed = discord.Embed(
                title="Backup",
                description="Backup failed.",
                color=EMBED_COLOR
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Admin(bot))
