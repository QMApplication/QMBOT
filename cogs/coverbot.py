# cogs/coverbot.py
import discord
from discord.ext import commands

from config import COVER_BOT_ID, COVER_INVITE_URL, RESTRICT_GUILD_NAME
from utils import get_member_safe

def _restricted_here(ctx: commands.Context) -> bool:
    return (RESTRICT_GUILD_NAME is None) or (ctx.guild and ctx.guild.name == RESTRICT_GUILD_NAME)

class CoverBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="coverstatus", help="Show whether the Cover bot is in this server.")
    async def coverstatus(self, ctx: commands.Context):
        if not _restricted_here(ctx):
            return await ctx.send(f"❌ This command is only for **{RESTRICT_GUILD_NAME}**.")
        member = await get_member_safe(ctx.guild, COVER_BOT_ID)
        if member:
            await ctx.send("✅ The Cover bot is **already in this server**.")
        else:
            await ctx.send("ℹ️ The Cover bot is **not in this server** yet.")

    @commands.command(name="coverjoin", help="Invite the Cover bot (opens the OAuth page).")
    @commands.has_permissions(manage_guild=True)
    async def coverjoin(self, ctx: commands.Context):
        if not _restricted_here(ctx):
            return await ctx.send(f"❌ This command is only for **{RESTRICT_GUILD_NAME}**.")

        member = await get_member_safe(ctx.guild, COVER_BOT_ID)
        if member:
            return await ctx.send("✅ The Cover bot is already here.")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Cover Bot", url=COVER_INVITE_URL))
        embed = discord.Embed(
            title="Add the Cover bot",
            description=("Click the button below to open the Discord OAuth2 page.\n"
                         "You must be logged in and have **Manage Server** permission here."),
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed, view=view)

        try:
            dm_view = discord.ui.View()
            dm_view.add_item(discord.ui.Button(label="Invite Cover Bot", url=COVER_INVITE_URL))
            await ctx.author.send("Here’s the invite link for the Cover bot:", view=dm_view)
        except discord.Forbidden:
            pass

    @commands.command(name="coverleave", help="Remove the Cover bot from this server.")
    @commands.has_permissions(kick_members=True)
    async def coverleave(self, ctx: commands.Context):
        if not _restricted_here(ctx):
            return await ctx.send(f"❌ This command is only for **{RESTRICT_GUILD_NAME}**.")

        member = await get_member_safe(ctx.guild, COVER_BOT_ID)
        if not member:
            return await ctx.send("ℹ️ The Cover bot isn’t in this server.")

        try:
            await member.kick(reason=f"Requested by {ctx.author} via !coverleave")
            await ctx.send("👋 The Cover bot has been removed from this server.")
        except discord.Forbidden:
            await ctx.send("❌ I don’t have permission to kick that bot (role too low or missing permission).")
        except discord.HTTPException as e:
            await ctx.send(f"⚠️ Failed to remove: {type(e).__name__}. Try again later.")

async def setup(bot: commands.Bot):
    await bot.add_cog(CoverBot(bot))
