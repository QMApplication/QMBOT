import discord
from discord.ext import commands
import random
import asyncio

from storage import load_coins, save_coins


GAMBLE_FEE_FLAT = 25
GAMBLE_TIMEOUT_RAKE_RATE = 0.10


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
    async def gamble(self, ctx, amount: str):

        uid = str(ctx.author.id)

        coins = ensure_user_coins(uid)
        user = coins[uid]

        wallet = user["wallet"]

        if amount.lower() == "all":
            bet = wallet - GAMBLE_FEE_FLAT
        else:
            if not amount.isdigit():
                return await ctx.send("❌ Invalid bet.")

            bet = int(amount)

        if bet <= 0:
            return await ctx.send("❌ Invalid bet.")

        fee = GAMBLE_FEE_FLAT

        if wallet < bet + fee:
            return await ctx.send(
                f"💸 You need **{bet+fee}** coins (bet {bet} + fee {fee})."
            )

        user["wallet"] -= fee
        save_coins(coins)

        result = random.choice(["red", "black"])

        embed = discord.Embed(
            title="🎰 Place Your Bet!",
            description=(
                f"Bet: **{bet}** coins\n"
                f"Fee paid: **{fee}** coins\n\n"
                "React:\n"
                "🟥 = Red\n"
                "⬛ = Black\n\n"
                "You have **5 seconds**."
            ),
            color=discord.Color.gold()
        )

        message = await ctx.send(embed=embed)

        await message.add_reaction("🟥")
        await message.add_reaction("⬛")

        def check(reaction, user2):
            return (
                user2.id == ctx.author.id
                and reaction.message.id == message.id
                and str(reaction.emoji) in ["🟥", "⬛"]
            )

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add",
                timeout=5,
                check=check
            )
        except asyncio.TimeoutError:

            rake = int(bet * GAMBLE_TIMEOUT_RAKE_RATE)

            coins = ensure_user_coins(uid)
            user = coins[uid]

            taken = min(user["wallet"], rake)
            user["wallet"] -= taken

            save_coins(coins)

            return await ctx.send(
                f"⏰ You didn't react.\nLost **{taken}** coins."
            )

        choice = "red" if str(reaction.emoji) == "🟥" else "black"

        coins = ensure_user_coins(uid)
        user = coins[uid]

        if user["wallet"] < bet:
            return await ctx.send("⚠️ Not enough coins anymore.")

        user["wallet"] -= bet

        if choice == result:

            winnings = bet * 2
            user["wallet"] += winnings

            msg = discord.Embed(
                title="🎉 You Win!",
                description=f"The wheel landed on **{result.upper()}**!\nYou won **{winnings}** coins!",
                color=discord.Color.green()
            )

        else:

            msg = discord.Embed(
                title="😢 You Lose!",
                description=f"The wheel landed on **{result.upper()}**.\nYou lost **{bet}** coins.",
                color=discord.Color.red()
            )

        save_coins(coins)

        await ctx.send(embed=msg)

    # -------------------------
    # Coinflip
    # -------------------------

    @commands.command()
    async def coinflip(self, ctx):

        result = random.choice(["Heads", "Tails"])

        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Games(bot))
