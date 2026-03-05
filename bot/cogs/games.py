# cogs/games.py

import discord
from discord.ext import commands
import random

from storage import load_coins, save_coins


def ensure_user_coins(user_id):
    user_id = str(user_id)
    coins = load_coins()

    if user_id not in coins:
        coins[user_id] = {
            "wallet": 100,
            "bank": 0
        }

    save_coins(coins)
    return coins


class Games(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # Gamble
    # -------------------------

    @commands.command()
    async def gamble(self, ctx, amount: int):

        coins = ensure_user_coins(ctx.author.id)
        user = coins[str(ctx.author.id)]

        if amount <= 0 or user["wallet"] < amount:
            return await ctx.send("Invalid bet.")

        user["wallet"] -= amount

        win = random.choice([True, False])

        if win:

            winnings = amount * 2
            user["wallet"] += winnings

            msg = f"You won **{winnings}** coins!"

        else:

            msg = f"You lost **{amount}** coins."

        save_coins(coins)

        await ctx.send(msg)

    # -------------------------
    # Coinflip
    # -------------------------

    @commands.command()
    async def coinflip(self, ctx):

        result = random.choice(["Heads", "Tails"])

        await ctx.send(f"🪙 {result}")


async def setup(bot):
    await bot.add_cog(Games(bot))
