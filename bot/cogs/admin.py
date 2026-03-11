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


def make_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )


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
            return await ctx.send(
                embed=make_embed("Suggestion", "Suggestion channel not configured.")
            )

        suggestions = load_suggestions()

        entry = {
            "user": ctx.author.id,
            "text": suggestion
        }

        suggestions.append(entry)
        save_suggestions(suggestions)

        embed = make_embed("Suggestion", suggestion)
        embed.set_footer(text=f"From {ctx.author.display_name}")

        msg = await channel.send(embed=embed)

        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        confirm = make_embed("Submitted", "Your suggestion has been sent.")
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
            return await ctx.send(
                embed=make_embed("Announcement", "Announcement channel not configured.")
            )

        embed = make_embed("Announcement", message)
        embed.set_footer(text=f"Posted by {ctx.author.display_name}")

        await channel.send(embed=embed)

        confirm = make_embed("Sent", "Announcement posted successfully.")
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
            return await ctx.send(
                embed=make_embed("Backup", "You are not authorised.")
            )

        success = await dm_package_to_user(
            self.bot,
            PACKAGE_USER_ID,
            reason="Manual package command"
        )

        if success:
            embed = make_embed("Backup", "Backup sent successfully.")
        else:
            embed = make_embed("Backup", "Backup failed.")

        await ctx.send(embed=embed)

    # -------------------------
    # ERROR HANDLERS
    # -------------------------

    @announcement.error
    async def announcement_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=make_embed("Announcement", "You do not have permission to use this command.")
            )
        else:
            await ctx.send(
                embed=make_embed("Announcement", "Something went wrong while sending the announcement.")
            )

    @suggest.error
    async def suggest_error(self, ctx: commands.Context, error):
        await ctx.send(
            embed=make_embed("Suggestion", "Something went wrong while submitting your suggestion.")
        )

    @package.error
    async def package_error(self, ctx: commands.Context, error):
        await ctx.send(
            embed=make_embed("Backup", "Something went wrong while creating the backup.")
        )


async def setup(bot):
    await bot.add_cog(Admin(bot))
