# cogs/economy.py - updated

import discord
from discord.ext import commands
import random
import time
from datetime import datetime, timedelta, timezone

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
            "last_beg": 0
        }
        save_coins(coins)

    return coins


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # Balance
    # -------------------------

    @commands.command(name="balance")
    async def balance(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        coins = ensure_user_coins(member.id)
        data = coins[str(member.id)]

        embed = discord.Embed(
            title=f"💰 {member.display_name}'s Balance",
            color=discord.Color.purple()
        )

        embed.add_field(name="Wallet", value=f"💵 {data['wallet']} coins")
        embed.add_field(name="Bank", value=f"🏦 {data['bank']} coins")

        await ctx.send(embed=embed)

    # -------------------------
    # Deposit
    # -------------------------

    @commands.command(name="deposit")
    async def deposit(self, ctx, amount: str):

        uid = str(ctx.author.id)
        coins = ensure_user_coins(uid)
        user = coins[uid]

        if amount.lower() == "all":
            amt = user["wallet"]
        else:
            if not amount.isdigit():
                return await ctx.send("❌ Enter a number or `all`.")
            amt = int(amount)

        if amt <= 0 or amt > user["wallet"]:
            return await ctx.send("❌ Not enough wallet balance.")

        user["wallet"] -= amt
        user["bank"] += amt

        save_coins(coins)

        await ctx.send(f"🏦 Deposited **{amt}** coins.")

    # -------------------------
    # Withdraw
    # -------------------------

    @commands.command(name="withdraw")
    async def withdraw(self, ctx, amount: str):

        uid = str(ctx.author.id)
        coins = ensure_user_coins(uid)
        user = coins[uid]

        if amount.lower() == "all":
            amt = user["bank"]
        else:
            if not amount.isdigit():
                return await ctx.send("❌ Enter a number or `all`.")
            amt = int(amount)

        if amt <= 0 or amt > user["bank"]:
            return await ctx.send("❌ Not enough bank balance.")

        user["bank"] -= amt
        user["wallet"] += amt

        save_coins(coins)

        await ctx.send(f"💰 Withdrew **{amt}** coins.")

    # -------------------------
    # Daily
    # -------------------------

    @commands.command(name="daily")
    async def daily(self, ctx):

        uid = str(ctx.author.id)
        coins = ensure_user_coins(uid)
        user = coins[uid]

        now = datetime.now(timezone.utc)
        last_ts = user.get("last_daily", 0)
        last_claim = datetime.fromtimestamp(last_ts, tz=timezone.utc)

        if last_claim.date() == now.date():
            tomorrow = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            remaining = (tomorrow - now).total_seconds()

            h = int(remaining // 3600)
            m = int((remaining % 3600) // 60)
            s = int(remaining % 60)

            return await ctx.send(
                f"🕒 Already claimed. Try again in **{h}h {m}m {s}s**."
            )

        reward = random.randint(200, 350)

        user["wallet"] += reward
        user["last_daily"] = now.timestamp()

        save_coins(coins)

        await ctx.send(f"💰 Daily claimed: **{reward}** coins!")

    # -------------------------
    # Beg
    # -------------------------

    @commands.command(name="beg")
    async def beg(self, ctx):

        uid = str(ctx.author.id)
        coins = ensure_user_coins(uid)
        user = coins[uid]

        now = time.time()
        cooldown = 30

        last_beg = user.get("last_beg", 0)

        if now - last_beg < cooldown:
            remaining = int(cooldown - (now - last_beg))
            return await ctx.send(
                f"⏳ You must wait **{remaining}s** before begging again."
            )

        amount = random.randint(10, 30)

        responses = [
            "A kind stranger gave you",
            "Your sob story worked. You received",
            "You found coins on the floor:",
            "Someone felt bad and handed you",
        ]

        user["wallet"] += amount
        user["last_beg"] = now

        save_coins(coins)

        await ctx.send(
            f"{random.choice(responses)} **{amount}** coins!"
        )


async def setup(bot):
    await bot.add_cog(Economy(bot))
