import discord
from discord.ext import commands

from storage import load_swear_jar, save_swear_jar


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

        embed = discord.Embed(
            title="🫙 Swear Jar",
            description=f"Total swears recorded: **{total}**",
            color=discord.Color.orange()
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
            return await ctx.send("No swears recorded yet.")

        sorted_users = sorted(
            users.items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True
        )

        desc = ""

        for i, (uid, data) in enumerate(sorted_users[:10], start=1):

            try:
                user = await self.bot.fetch_user(int(uid))
                name = user.name
            except Exception:
                name = f"User {uid}"

            count = data.get("count", 0)

            desc += f"**{i}. {name}** — {count}\n"

        embed = discord.Embed(
            title="🧼 Swear Leaderboard",
            description=desc,
            color=discord.Color.red()
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

        await ctx.send("🧹 Swear jar has been reset.")

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

        embed = discord.Embed(
            title="💰 Your Swear Count",
            description=f"You have sworn **{count}** times.",
            color=discord.Color.orange()
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(SwearJar(bot))
