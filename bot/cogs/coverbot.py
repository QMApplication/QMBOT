import discord
from discord.ext import commands

from config import COVER_BOT_ID, COVER_INVITE_URL, RESTRICT_GUILD_NAME
from utils import get_member_safe


from ui_utils import C, E
EMBED_COLOR = C.ADMIN


def _restricted_here(ctx: commands.Context) -> bool:
    return (
        RESTRICT_GUILD_NAME is None
        or (ctx.guild is not None and ctx.guild.name == RESTRICT_GUILD_NAME)
    )


class CoverBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="coverstatus",
        description="Show whether the Cover bot is in this server."
    )
    async def coverstatus(self, ctx: commands.Context):
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server.")

        if not _restricted_here(ctx):
            return await ctx.send(
                f"This command is only for **{RESTRICT_GUILD_NAME}**."
            )

        member = await get_member_safe(ctx.guild, COVER_BOT_ID)

        if member:
            embed = discord.Embed(
                title="🤖  Cover Bot",
                description="The Cover bot is already in this server.",
                color=EMBED_COLOR
            )
        else:
            embed = discord.Embed(
                title="🤖  Cover Bot",
                description="The Cover bot is not in this server. Use `/coverjoin` to invite it.",
                color=EMBED_COLOR
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="coverjoin",
        description="Invite the Cover bot to this server."
    )
    @commands.has_permissions(manage_guild=True)
    async def coverjoin(self, ctx: commands.Context):
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server.")

        if not _restricted_here(ctx):
            return await ctx.send(
                f"This command is only for **{RESTRICT_GUILD_NAME}**."
            )

        member = await get_member_safe(ctx.guild, COVER_BOT_ID)
        if member:
            return await ctx.send("The Cover bot is already here.")

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(label="🔗  Invite Cover Bot", url=COVER_INVITE_URL)
        )

        embed = discord.Embed(
            title="🔗  Invite Cover Bot",
            description=(
                "Use the button below to open the Discord OAuth2 page.\n"
                "You must be logged in and have permission to manage this server."
            ),
            color=EMBED_COLOR
        )

        await ctx.send(embed=embed, view=view)

        try:
            dm_view = discord.ui.View()
            dm_view.add_item(
                discord.ui.Button(label="🔗  Invite Cover Bot", url=COVER_INVITE_URL)
            )

            dm_embed = discord.Embed(
                title="🔗  Invite Cover Bot",
                description="Here is the invite link for the Cover bot.",
                color=EMBED_COLOR
            )

            await ctx.author.send(embed=dm_embed, view=dm_view)
        except discord.Forbidden:
            pass

    @commands.hybrid_command(
        name="coverleave",
        description="Remove the Cover bot from this server."
    )
    @commands.has_permissions(kick_members=True)
    async def coverleave(self, ctx: commands.Context):
        if not ctx.guild:
            return await ctx.send("This command can only be used in a server.")

        if not _restricted_here(ctx):
            return await ctx.send(
                f"This command is only for **{RESTRICT_GUILD_NAME}**."
            )

        member = await get_member_safe(ctx.guild, COVER_BOT_ID)
        if not member:
            return await ctx.send("The Cover bot is not in this server. Use `/coverjoin` to invite it.")

        try:
            await member.kick(reason=f"Requested by {ctx.author} via coverleave")

            embed = discord.Embed(
                title="🤖  Cover Bot",
                description="The Cover bot has been removed from this server.",
                color=EMBED_COLOR
            )
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send(
                "I don’t have permission to kick that bot."
            )

        except discord.HTTPException as e:
            await ctx.send(
                f"Failed to remove the bot: {type(e).__name__}."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(CoverBot(bot))
