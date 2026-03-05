# cogs/economy.py

import discord
from discord.ext import commands
import random
import time

from storage import load_coins, save_coins


def ensure_user_coins(user_id):
    user_id = str(user_id)
    coins = load_coins()

    if user_id not in coins:
        coins[user_id] = {
            "wallet": 100,
            "bank": 0,
            "last_daily": 0,
            "last_rob": 0,
        }
        save_coins(coins)

    return coins


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # Balance
    # -------------------------

    @commands.command()
    async def balance(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        coins = ensure_user_coins(member.id)
        data = coins[str(member.id)]

        embed = discord.Embed(
            title=f"{member.display_name}'s Balance",
            color=discord.Color.green()
        )

        embed.add_field(name="Wallet", value=data["wallet"])
        embed.add_field(name="Bank", value=data["bank"])

        await ctx.send(embed=embed)

    # -------------------------
    # Deposit
    # -------------------------

    @commands.command()
    async def deposit(self, ctx, amount: int):

        coins = ensure_user_coins(ctx.author.id)
        user = coins[str(ctx.author.id)]

        if amount <= 0 or amount > user["wallet"]:
            return await ctx.send("Invalid amount.")

        user["wallet"] -= amount
        user["bank"] += amount

        save_coins(coins)

        await ctx.send(f"Deposited **{amount}** coins.")

    # -------------------------
    # Withdraw
    # -------------------------

    @commands.command()
    async def withdraw(self, ctx, amount: int):

        coins = ensure_user_coins(ctx.author.id)
        user = coins[str(ctx.author.id)]

        if amount <= 0 or amount > user["bank"]:
            return await ctx.send("Invalid amount.")

        user["bank"] -= amount
        user["wallet"] += amount

        save_coins(coins)

        await ctx.send(f"Withdrew **{amount}** coins.")

    # -------------------------
    # Daily
    # -------------------------

    @commands.command()
    async def daily(self, ctx):

        coins = ensure_user_coins(ctx.author.id)
        user = coins[str(ctx.author.id)]

        now = time.time()

        if now - user["last_daily"] < 86400:
            return await ctx.send("You already claimed your daily.")

        reward = random.randint(200, 350)

        user["wallet"] += reward
        user["last_daily"] = now

        save_coins(coins)

        await ctx.send(f"You received **{reward}** coins!")

    # -------------------------
    # Beg
    # -------------------------

    @commands.command()
    async def beg(self, ctx):

        coins = ensure_user_coins(ctx.author.id)
        user = coins[str(ctx.author.id)]

        amount = random.randint(10, 30)

        user["wallet"] += amount

        save_coins(coins)

        await ctx.send(f"You received **{amount}** coins.")


async def setup(bot):
    await bot.add_cog(Economy(bot))
