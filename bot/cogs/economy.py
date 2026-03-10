import discord
from discord.ext import commands
import random
import time
from datetime import datetime, timedelta, timezone

from storage import load_coins, save_coins
from config import (
    ALWAYS_BANKROB_USER_ID,
    BANKROB_STEAL_MIN_PCT,
    BANKROB_STEAL_MAX_PCT,
    BANKROB_MIN_STEAL,
    BANKROB_MAX_STEAL_PCT_CAP
)


def ensure_user(user_id):
    coins = load_coins()
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0,
            "last_daily": 0,
            "last_beg": 0,
            "last_rob": 0,
            "last_bankrob": 0
        }
        save_coins(coins)

    return coins


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # BALANCE
    # -------------------------

    @commands.command(name="balance")
    async def balance(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        coins = ensure_user(member.id)
        user = coins[str(member.id)]

        embed = discord.Embed(
            title=f"💰 {member.display_name}'s Balance",
            color=discord.Color.gold()
        )

        embed.add_field(name="Wallet", value=f"💵 {user['wallet']}")
        embed.add_field(name="Bank", value=f"🏦 {user['bank']}")

        await ctx.send(embed=embed)

    # -------------------------
    # DEPOSIT
    # -------------------------

    @commands.command()
    async def deposit(self, ctx, amount: str):

        coins = ensure_user(ctx.author.id)
        user = coins[str(ctx.author.id)]

        if amount == "all":
            amount = user["wallet"]
        else:
            if not amount.isdigit():
                return await ctx.send("Invalid amount.")
            amount = int(amount)

        if amount <= 0 or amount > user["wallet"]:
            return await ctx.send("Not enough coins.")

        user["wallet"] -= amount
        user["bank"] += amount

        save_coins(coins)

        await ctx.send(f"🏦 Deposited **{amount}** coins.")

    # -------------------------
    # WITHDRAW
    # -------------------------

    @commands.command()
    async def withdraw(self, ctx, amount: str):

        coins = ensure_user(ctx.author.id)
        user = coins[str(ctx.author.id)]

        if amount == "all":
            amount = user["bank"]
        else:
            if not amount.isdigit():
                return await ctx.send("Invalid amount.")
            amount = int(amount)

        if amount <= 0 or amount > user["bank"]:
            return await ctx.send("Not enough bank coins.")

        user["bank"] -= amount
        user["wallet"] += amount

        save_coins(coins)

        await ctx.send(f"💰 Withdrew **{amount}** coins.")

    # -------------------------
    # DAILY
    # -------------------------

    @commands.command()
    async def daily(self, ctx):

        coins = ensure_user(ctx.author.id)
        user = coins[str(ctx.author.id)]

        now = datetime.now(timezone.utc)

        last = datetime.fromtimestamp(user["last_daily"], timezone.utc)

        if last.date() == now.date():

            tomorrow = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            remaining = tomorrow - now
            seconds = int(remaining.total_seconds())

            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60

            return await ctx.send(f"⏳ Try again in **{h}h {m}m {s}s**")

        reward = random.randint(200, 350)

        user["wallet"] += reward
        user["last_daily"] = now.timestamp()

        save_coins(coins)

        await ctx.send(f"🎁 You received **{reward}** coins!")

    # -------------------------
    # BEG
    # -------------------------

    @commands.command()
    async def beg(self, ctx):

        coins = ensure_user(ctx.author.id)
        user = coins[str(ctx.author.id)]

        now = time.time()

        if now - user["last_beg"] < 30:

            remaining = int(30 - (now - user["last_beg"]))
            return await ctx.send(f"⏳ Wait **{remaining}s**")

        amount = random.randint(10, 30)

        user["wallet"] += amount
        user["last_beg"] = now

        save_coins(coins)

        await ctx.send(f"Someone gave you **{amount}** coins.")

    # -------------------------
    # BEG LEADERBOARD
    # -------------------------

    @commands.command()
    async def begleaderboard(self, ctx):

        coins = load_coins()

        sorted_users = sorted(
            coins.items(),
            key=lambda x: x[1].get("last_beg", 0),
            reverse=True
        )

        desc = ""

        for i, (uid, data) in enumerate(sorted_users[:10], 1):

            user = await self.bot.fetch_user(int(uid))

            desc += f"{i}. {user.name}\n"

        embed = discord.Embed(
            title="🥇 Beg Leaderboard",
            description=desc
        )

        await ctx.send(embed=embed)

    # -------------------------
    # PAY
    # -------------------------

    @commands.command()
    async def pay(self, ctx, member: discord.Member, amount: int):

        if amount <= 0:
            return await ctx.send("Invalid amount.")

        coins = ensure_user(ctx.author.id)
        user = coins[str(ctx.author.id)]

        if user["wallet"] < amount:
            return await ctx.send("Not enough coins.")

        coins = ensure_user(member.id)
        target = coins[str(member.id)]

        user["wallet"] -= amount
        target["wallet"] += amount

        save_coins(coins)

        await ctx.send(
            f"💸 {ctx.author.mention} paid {member.mention} **{amount}** coins."
        )

    # -------------------------
    # ROB
    # -------------------------

    @commands.command()
    async def rob(self, ctx, member: discord.Member):

        if member == ctx.author:
            return await ctx.send("You can't rob yourself.")

        coins = ensure_user(ctx.author.id)
        robber = coins[str(ctx.author.id)]

        coins = ensure_user(member.id)
        victim = coins[str(member.id)]

        if victim["wallet"] <= 0:
            return await ctx.send("They have nothing.")

        success = random.choice([True, False])

        if success:

            steal = random.randint(10, victim["wallet"])

            victim["wallet"] -= steal
            robber["wallet"] += steal

            msg = f"🦹 You stole **{steal}** coins!"

        else:

            fine = random.randint(5, 30)

            robber["wallet"] = max(0, robber["wallet"] - fine)

            msg = f"🚨 Failed robbery. You paid **{fine}** coins."

        save_coins(coins)

        await ctx.send(msg)

    # -------------------------
    # BANK ROB
    # -------------------------

    @commands.command()
    async def bankrob(self, ctx, member: discord.Member):

        if member.id == ctx.author.id:
            return await ctx.send("You can't rob yourself.")

        coins = ensure_user(ctx.author.id)
        robber = coins[str(ctx.author.id)]

        coins = ensure_user(member.id)
        victim = coins[str(member.id)]

        bank = victim["bank"]

        if bank <= 0:
            return await ctx.send("They have no bank coins.")

        pct = random.uniform(BANKROB_STEAL_MIN_PCT, BANKROB_STEAL_MAX_PCT)

        amount = int(bank * pct)

        amount = max(amount, BANKROB_MIN_STEAL)

        amount = min(amount, int(bank * BANKROB_MAX_STEAL_PCT_CAP))

        victim["bank"] -= amount
        robber["wallet"] += amount

        save_coins(coins)

        await ctx.send(f"🏦 You robbed **{amount}** bank coins!")

    # -------------------------
    # BALANCE LEADERBOARD
    # -------------------------

    @commands.command()
    async def baltop(self, ctx):

        coins = load_coins()

        leaderboard = []

        for uid, data in coins.items():
            total = data.get("wallet", 0) + data.get("bank", 0)
            leaderboard.append((uid, total))

        leaderboard.sort(key=lambda x: x[1], reverse=True)

        desc = ""

        for i, (uid, total) in enumerate(leaderboard[:10], 1):

            user = await self.bot.fetch_user(int(uid))

            desc += f"{i}. {user.name} — {total}\n"

        embed = discord.Embed(
            title="🏆 Richest Players",
            description=desc
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
