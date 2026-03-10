import asyncio
import random

import discord
from discord.ext import commands

from config import GAMBLE_FEE_FLAT, GAMBLE_TIMEOUT_RAKE_RATE
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
            "last_beg": 0,
            "last_bankrob": 0,
            "portfolio": {},
            "pending_portfolio": [],
            "trade_meta": {
                "last_trade_ts": {},
                "daily": {"day": "", "count": 0}
            }
        }
        save_coins(coins)
    else:
        user = coins[user_id]
        changed = False

        defaults = {
            "wallet": 100,
            "bank": 0,
            "last_daily": 0,
            "last_rob": 0,
            "last_beg": 0,
            "last_bankrob": 0,
            "portfolio": {},
            "pending_portfolio": [],
            "trade_meta": {
                "last_trade_ts": {},
                "daily": {"day": "", "count": 0}
            }
        }

        for key, value in defaults.items():
            if key not in user:
                user[key] = value
                changed = True

        if changed:
            save_coins(coins)

    return coins


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # Gamble
    # -------------------------
    @commands.hybrid_command(
        name="gamble",
        description="Gamble coins on red or black."
    )
    async def gamble(self, ctx: commands.Context, amount: str):
        uid = str(ctx.author.id)

        coins = ensure_user_coins(uid)
        user = coins[uid]

        wallet = int(user.get("wallet", 0))

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
                f"💸 You need **{bet + fee}** coins (bet **{bet}** + fee **{fee}**)."
            )

        # charge fee immediately
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

        try:
            await message.add_reaction("🟥")
            await message.add_reaction("⬛")
        except discord.HTTPException:
            pass

        def check(reaction: discord.Reaction, user2: discord.User):
            return (
                user2.id == ctx.author.id
                and reaction.message.id == message.id
                and str(reaction.emoji) in ("🟥", "⬛")
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

            taken = min(int(user.get("wallet", 0)), rake)
            user["wallet"] -= taken
            save_coins(coins)

            return await ctx.send(
                f"⏰ You didn't react in time.\n"
                f"💸 Lost **{taken}** coins."
            )

        choice = "red" if str(reaction.emoji) == "🟥" else "black"

        coins = ensure_user_coins(uid)
        user = coins[uid]

        if int(user.get("wallet", 0)) < bet:
            return await ctx.send("⚠️ Not enough coins anymore.")

        user["wallet"] -= bet

        if choice == result:
            winnings = bet * 2
            user["wallet"] += winnings

            msg = discord.Embed(
                title="🎉 You Win!",
                description=(
                    f"The wheel landed on **{result.upper()}**!\n"
                    f"You won **{winnings}** coins!"
                ),
                color=discord.Color.green()
            )
        else:
            msg = discord.Embed(
                title="😢 You Lose!",
                description=(
                    f"The wheel landed on **{result.upper()}**.\n"
                    f"You lost **{bet}** coins."
                ),
                color=discord.Color.red()
            )

        save_coins(coins)
        await ctx.send(embed=msg)

    # -------------------------
    # Coinflip
    # -------------------------
    @commands.hybrid_command(
        name="coinflip",
        description="Flip a coin."
    )
    async def coinflip(self, ctx: commands.Context):
        result = random.choice(["Heads", "Tails"])

        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
