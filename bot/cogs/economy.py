# cogs/economy.py

import random
import time
from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

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


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # Balance
    # -------------------------
    @commands.hybrid_command(
        name="balance",
        description="Check your or someone else's balance."
    )
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
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
    @commands.hybrid_command(
        name="deposit",
        description="Deposit coins into your bank."
    )
    async def deposit(self, ctx: commands.Context, amount: str):
        uid = str(ctx.author.id)
        coins = ensure_user_coins(uid)
        user = coins[uid]

        if amount.lower() == "all":
            amt = int(user["wallet"])
        else:
            if not amount.isdigit():
                return await ctx.send("❌ Enter a number or `all`.")
            amt = int(amount)

        if amt <= 0 or amt > int(user["wallet"]):
            return await ctx.send("❌ Not enough wallet balance.")

        user["wallet"] -= amt
        user["bank"] += amt
        save_coins(coins)

        await ctx.send(f"🏦 Deposited **{amt}** coins.")

    # -------------------------
    # Withdraw
    # -------------------------
    @commands.hybrid_command(
        name="withdraw",
        description="Withdraw coins from your bank."
    )
    async def withdraw(self, ctx: commands.Context, amount: str):
        uid = str(ctx.author.id)
        coins = ensure_user_coins(uid)
        user = coins[uid]

        if amount.lower() == "all":
            amt = int(user["bank"])
        else:
            if not amount.isdigit():
                return await ctx.send("❌ Enter a number or `all`.")
            amt = int(amount)

        if amt <= 0 or amt > int(user["bank"]):
            return await ctx.send("❌ Not enough bank balance.")

        user["bank"] -= amt
        user["wallet"] += amt
        save_coins(coins)

        await ctx.send(f"💰 Withdrew **{amt}** coins.")

    # -------------------------
    # Daily
    # -------------------------
    @commands.hybrid_command(
        name="daily",
        description="Claim your daily reward."
    )
    async def daily(self, ctx: commands.Context):
        uid = str(ctx.author.id)
        coins = ensure_user_coins(uid)
        user = coins[uid]

        now = datetime.now(timezone.utc)
        last_ts = float(user.get("last_daily", 0) or 0)
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
    @commands.hybrid_command(
        name="beg",
        description="Beg for a few coins."
    )
    async def beg(self, ctx: commands.Context):
        uid = str(ctx.author.id)
        coins = ensure_user_coins(uid)
        user = coins[uid]

        now = time.time()
        cooldown = 30
        last_beg = float(user.get("last_beg", 0) or 0)

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

        await ctx.send(f"{random.choice(responses)} **{amount}** coins!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
