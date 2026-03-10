import discord
from discord.ext import commands

from config import (
    SUGGESTION_CHANNEL_ID,
    ANNOUNCEMENT_CHANNEL_ID,
    PACKAGE_USER_ID,
)
from storage import load_suggestions, save_suggestions
from cogs.tasks import dm_package_to_user


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # SUGGEST
    # -------------------------

    @commands.command()
    async def suggest(self, ctx, *, suggestion: str):

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
            title="💡 New Suggestion",
            description=suggestion,
            color=discord.Color.blue()
        )

        embed.set_footer(text=f"Suggested by {ctx.author}")

        msg = await channel.send(embed=embed)

        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        await ctx.send("Suggestion submitted!")

    # -------------------------
    # ANNOUNCEMENT
    # -------------------------

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def announcement(self, ctx, *, message: str):

        channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)

        if not channel:
            return await ctx.send("Announcement channel not configured.")

        embed = discord.Embed(
            title="📢 Announcement",
            description=message,
            color=discord.Color.gold()
        )

        embed.set_footer(text=f"Posted by {ctx.author}")

        await channel.send(embed=embed)

        await ctx.send("Announcement sent.")

    # -------------------------
    # PACKAGE (manual backup)
    # -------------------------

    @commands.command()
    async def package(self, ctx):

        if ctx.author.id != PACKAGE_USER_ID:
            return await ctx.send("You are not authorised.")

        success = await dm_package_to_user(
            self.bot,
            PACKAGE_USER_ID,
            reason="Manual package command"
        )

        if success:
            await ctx.send("Backup sent.")
        else:
            await ctx.send("Backup failed.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
