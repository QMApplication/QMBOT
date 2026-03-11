import discord
from discord.ext import commands

from storage import load_swear_jar, save_swear_jar


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


def make_embed(title: str, description: str):
    return discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )


class SwearJar(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # SWEAR JAR TOTAL
    # -------------------------

    @commands.hybrid_command(
        name="swearjar",
        description="Show the total number of swears recorded in the server."
    )
    async def swearjar(self, ctx: commands.Context):

        jar = load_swear_jar()
        total = jar.get("total", 0)

        embed = make_embed(
            "🫙 Swear Jar",
            f"Total swears recorded: **{total}**"
        )

        await ctx.send(embed=embed)

    # -------------------------
    # SWEAR LEADERBOARD
    # -------------------------

    @commands.hybrid_command(
        name="swearleaderboard",
        description="Show the users who swear the most."
    )
    async def swearleaderboard(self, ctx: commands.Context):

        jar = load_swear_jar()
        users = jar.get("users", {})

        if not users:
            return await ctx.send(
                embed=make_embed(
                    "Swear Leaderboard",
                    "No swears recorded yet."
                )
            )

        sorted_users = sorted(
            users.items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True
        )

        lines = []

        for i, (uid, data) in enumerate(sorted_users[:10], start=1):

            try:
                user = await self.bot.fetch_user(int(uid))
                name = user.name
            except Exception:
                name = f"User {uid}"

            count = data.get("count", 0)

            lines.append(f"**{i}. {name}** — `{count}`")

        embed = make_embed(
            "🧼 Swear Leaderboard",
            "\n".join(lines)
        )

        await ctx.send(embed=embed)

    # -------------------------
    # SWEAR RESET
    # -------------------------

    @commands.hybrid_command(
        name="swearreset",
        description="Reset the swear jar (admin only)."
    )
    @commands.has_permissions(administrator=True)
    async def swearreset(self, ctx: commands.Context):

        save_swear_jar({
            "total": 0,
            "users": {}
        })

        await ctx.send(
            embed=make_embed(
                "Swear Jar Reset",
                "🧹 The swear jar has been reset."
            )
        )

    # -------------------------
    # SWEAR FINE
    # -------------------------

    @commands.hybrid_command(
        name="swearfine",
        description="Check how many times you have sworn."
    )
    async def swearfine(self, ctx: commands.Context):

        jar = load_swear_jar()
        users = jar.get("users", {})

        uid = str(ctx.author.id)
        count = users.get(uid, {}).get("count", 0)

        embed = make_embed(
            "💰 Your Swear Count",
            f"You have sworn **{count}** times."
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SwearJar(bot))
