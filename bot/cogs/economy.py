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

EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


def make_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )


def ensure_user(coins, user_id):
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

    return coins[uid]


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # BALANCE
    # -------------------------

    @commands.hybrid_command(
        name="balance",
        description="Check your balance."
    )
    async def balance(self, ctx, member: discord.Member = None):
        coins = load_coins()
        member = member or ctx.author
        user = ensure_user(coins, member.id)

        embed = make_embed(
            f"{member.display_name} — Balance",
            "Current funds"
        )
        embed.add_field(name="¢ Wallet", value=f"`{user['wallet']}`", inline=True)
        embed.add_field(name="♕ QMBank", value=f"`{user['bank']}`", inline=True)

        await ctx.send(embed=embed)

    # -------------------------
    # DEPOSIT
    # -------------------------

    @commands.hybrid_command(
        name="deposit",
        description="Deposit coins into your bank."
    )
    async def deposit(self, ctx, amount: str):
        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        if amount.lower() == "all":
            amount = user["wallet"]
        else:
            if not amount.isdigit():
                return await ctx.send(
                    embed=make_embed("Deposit", "Invalid amount.")
                )
            amount = int(amount)

        if amount <= 0 or amount > user["wallet"]:
            return await ctx.send(
                embed=make_embed("Deposit", "Not enough coins.")
            )

        user["wallet"] -= amount
        user["bank"] += amount
        save_coins(coins)

        embed = make_embed(
            "Deposit Complete",
            f"Moved **{amount}** coins into **QMBank**."
        )
        embed.add_field(name="¢ Wallet", value=f"`{user['wallet']}`", inline=True)
        embed.add_field(name="♕ QMBank", value=f"`{user['bank']}`", inline=True)

        await ctx.send(embed=embed)

    # -------------------------
    # WITHDRAW
    # -------------------------

    @commands.hybrid_command(
        name="withdraw",
        description="Withdraw coins from your bank."
    )
    async def withdraw(self, ctx, amount: str):
        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        if amount.lower() == "all":
            amount = user["bank"]
        else:
            if not amount.isdigit():
                return await ctx.send(
                    embed=make_embed("Withdraw", "Invalid amount.")
                )
            amount = int(amount)

        if amount <= 0 or amount > user["bank"]:
            return await ctx.send(
                embed=make_embed("Withdraw", "Not enough bank coins.")
            )

        user["bank"] -= amount
        user["wallet"] += amount
        save_coins(coins)

        embed = make_embed(
            "Withdrawal Complete",
            f"Moved **{amount}** coins into your wallet."
        )
        embed.add_field(name="¢ Wallet", value=f"`{user['wallet']}`", inline=True)
        embed.add_field(name="♕ QMBank", value=f"`{user['bank']}`", inline=True)

        await ctx.send(embed=embed)

    # -------------------------
    # DAILY
    # -------------------------

    @commands.hybrid_command(
        name="daily",
        description="Claim your daily coins."
    )
    async def daily(self, ctx):
        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

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

            return await ctx.send(
                embed=make_embed(
                    "Daily Reward",
                    f"Available again in **{h}h {m}m {s}s**"
                )
            )

        reward = random.randint(200, 350)

        user["wallet"] += reward
        user["last_daily"] = now.timestamp()
        save_coins(coins)

        embed = make_embed(
            "Daily Reward",
            f"You received **{reward}** coins."
        )
        embed.add_field(name="¢ Wallet", value=f"`{user['wallet']}`", inline=False)

        await ctx.send(embed=embed)

    # -------------------------
    # BEG
    # -------------------------

    @commands.hybrid_command(
        name="beg",
        description="Beg for some coins."
    )
    async def beg(self, ctx):
        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        now = time.time()

        if now - user["last_beg"] < 30:
            remaining = int(30 - (now - user["last_beg"]))
            return await ctx.send(
                embed=make_embed(
                    "Begging Result",
                    f"Try again in **{remaining}s**"
                )
            )

        amount = random.randint(10, 30)

        user["wallet"] += amount
        user["last_beg"] = now
        save_coins(coins)

        embed = make_embed(
            "Begging Result",
            f"Someone gave you **{amount}** coins."
        )
        embed.add_field(name="¢ Wallet", value=f"`{user['wallet']}`", inline=False)

        await ctx.send(embed=embed)

    # -------------------------
    # BALANCE LEADERBOARD
    # -------------------------

    @commands.hybrid_command(
        name="baltop",
        description="Show the richest users."
    )
    async def baltop(self, ctx):
        coins = load_coins()
        leaderboard = []

        for uid, data in coins.items():
            wallet = data.get("wallet", 0)
            bank = data.get("bank", 0)
            total = wallet + bank
            leaderboard.append((uid, wallet, bank, total))

        leaderboard.sort(key=lambda x: x[3], reverse=True)

        blocks = []

        for i, (uid, wallet, bank, total) in enumerate(leaderboard[:10], 1):
            member = ctx.guild.get_member(int(uid)) if ctx.guild else None
            name = member.display_name if member else f"User {uid}"
            you = " ⋆ YOU" if int(uid) == ctx.author.id else ""

            block = (
                f"{i}. {name}\n"
                f"   ¢ Wallet : {wallet}\n"
                f"   ♕ QMBank : {bank}\n"
                f"   Total    : {total}{you}"
            )
            blocks.append(block)

        table = "```text\n" + "\n\n".join(blocks) + "\n```"

        embed = make_embed("Balance Leaderboard", table)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
