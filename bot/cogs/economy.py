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

EMBED_COLOR = discord.Color.from_rgb(110, 40, 110)


def make_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _reset_star_meta_if_needed(user: dict):
    user.setdefault("stars", 0)
    user.setdefault("star_meta", {"day": _today_key(), "given": {}})

    if not isinstance(user["star_meta"], dict):
        user["star_meta"] = {"day": _today_key(), "given": {}}

    user["star_meta"].setdefault("day", _today_key())
    user["star_meta"].setdefault("given", {})

    if user["star_meta"]["day"] != _today_key():
        user["star_meta"] = {
            "day": _today_key(),
            "given": {}
        }


def ensure_user(coins, user_id):
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0,
            "stars": 0,
            "last_daily": 0,
            "last_beg": 0,
            "last_rob": 0,
            "last_bankrob": 0,
            "active_effects": {},
            "star_meta": {
                "day": _today_key(),
                "given": {}
            }
        }
    else:
        coins[uid].setdefault("wallet", 100)
        coins[uid].setdefault("bank", 0)
        coins[uid].setdefault("stars", 0)
        coins[uid].setdefault("last_daily", 0)
        coins[uid].setdefault("last_beg", 0)
        coins[uid].setdefault("last_rob", 0)
        coins[uid].setdefault("last_bankrob", 0)
        coins[uid].setdefault("active_effects", {})
        _reset_star_meta_if_needed(coins[uid])

    return coins[uid]


def has_effect(user: dict, effect: str) -> bool:
    effects = user.get("active_effects", {})
    if effect not in effects:
        return False
    return effects[effect] > time.time()


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
        embed.add_field(name="✦ Stars", value=f"`{user['stars']}`", inline=True)

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

        reward = random.randint(1, 300)

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
        cooldown = 120

        if now - user["last_beg"] < cooldown:
            remaining = int(cooldown - (now - user["last_beg"]))
            return await ctx.send(
                embed=make_embed(
                    "Begging Result",
                    f"Try again in **{remaining}s**"
                )
            )

        amount = random.randint(1, 30)

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
    # STAR
    # -------------------------

    @commands.hybrid_command(
        name="star",
        description="Give someone a golden star."
    )
    async def star(self, ctx, member: discord.Member):

        if member == ctx.author:
            return await ctx.send(
                embed=make_embed("Golden Star", "You can't give yourself a star.")
            )

        if member.bot:
            return await ctx.send(
                embed=make_embed("Golden Star", "You can't give stars to bots.")
            )

        coins = load_coins()

        giver = ensure_user(coins, ctx.author.id)
        receiver = ensure_user(coins, member.id)

        _reset_star_meta_if_needed(giver)

        target_key = str(member.id)
        given_today = int(giver["star_meta"]["given"].get(target_key, 0))

        if given_today >= 2:
            return await ctx.send(
                embed=make_embed(
                    "Golden Star",
                    f"You've already given **2** stars to {member.mention} today."
                )
            )

        giver["star_meta"]["given"][target_key] = given_today + 1
        receiver["stars"] += 1

        save_coins(coins)

        embed = make_embed(
            "Golden Star Given",
            f"{ctx.author.mention} gave {member.mention} a **golden star**."
        )
        embed.add_field(name=f"{member.display_name} ✦ Stars", value=f"`{receiver['stars']}`", inline=False)

        await ctx.send(embed=embed)

    # -------------------------
    # STARS
    # -------------------------

    @commands.hybrid_command(
        name="stars",
        description="Check how many golden stars you have."
    )
    async def stars(self, ctx, member: discord.Member = None):
        coins = load_coins()
        member = member or ctx.author
        user = ensure_user(coins, member.id)

        embed = make_embed(
            f"{member.display_name} — Stars",
            f"✦ Golden Stars: **{user['stars']}**"
        )

        await ctx.send(embed=embed)

    # -------------------------
    # STAR LEADERBOARD
    # -------------------------

    @commands.hybrid_command(
        name="starleaderboard",
        description="Show the users with the most golden stars."
    )
    async def starleaderboard(self, ctx):
        coins = load_coins()
        leaderboard = []

        for uid, data in coins.items():
            stars = int(data.get("stars", 0))
            leaderboard.append((uid, stars))

        leaderboard.sort(key=lambda x: x[1], reverse=True)

        blocks = []

        for i, (uid, stars) in enumerate(leaderboard[:10], 1):
            member = ctx.guild.get_member(int(uid)) if ctx.guild else None
            name = member.display_name if member else f"User {uid}"
            you = " ⋆ YOU" if int(uid) == ctx.author.id else ""

            block = (
                f"{i}. {name}\n"
                f"   ✦ Stars : {stars}{you}"
            )
            blocks.append(block)

        table = "```text\n" + "\n\n".join(blocks) + "\n```"

        embed = make_embed("Star Leaderboard", table)
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

    # -------------------------
    # ROB
    # -------------------------

    @commands.hybrid_command(
        name="rob",
        description="Attempt to rob another user's wallet."
    )
    async def rob(self, ctx, member: discord.Member):

        if member == ctx.author:
            return await ctx.send(embed=make_embed("Rob", "You can't rob yourself."))

        if member.bot:
            return await ctx.send(embed=make_embed("Rob", "You can't rob bots."))

        coins = load_coins()

        robber = ensure_user(coins, ctx.author.id)
        victim = ensure_user(coins, member.id)

        now = time.time()

        cooldown = 300
        if has_effect(robber, "kachow_clock_until"):
            cooldown = 60

        if now - robber["last_rob"] < cooldown:
            remaining = int(cooldown - (now - robber["last_rob"]))
            return await ctx.send(
                embed=make_embed("Rob Cooldown", f"Try again in **{remaining}s**")
            )

        victim_wallet = int(victim.get("wallet", 0))

        if victim_wallet <= 0:
            return await ctx.send(
                embed=make_embed("Robbery Failed", "They have nothing to steal.")
            )

        robber["last_rob"] = now

        success_rate = 0.40
        if has_effect(victim, "comfort_until"):
            success_rate = 0.20

        success = random.random() < success_rate

        if success:
            steal = random.randint(10, min(200, victim_wallet))

            victim["wallet"] -= steal
            robber["wallet"] += steal

            save_coins(coins)

            embed = make_embed(
                "Robbery Success",
                f"You stole **{steal}** coins from {member.mention}."
            )

        else:
            fine = random.randint(20, 60)
            robber["wallet"] = max(0, robber["wallet"] - fine)

            save_coins(coins)

            embed = make_embed(
                "Robbery Failed",
                f"You got caught and paid **{fine}** coins."
            )

        embed.add_field(name="¢ Wallet", value=f"`{robber['wallet']}`", inline=False)

        await ctx.send(embed=embed)

    # -------------------------
    # BANK ROB
    # -------------------------

    @commands.hybrid_command(
        name="bankrob",
        description="Attempt to rob another user's QMBank."
    )
    async def bankrob(self, ctx, member: discord.Member):

        if member == ctx.author:
            return await ctx.send(embed=make_embed("Bank Rob", "You can't rob yourself."))

        if member.bot:
            return await ctx.send(embed=make_embed("Bank Rob", "You can't rob bots."))

        coins = load_coins()

        robber = ensure_user(coins, ctx.author.id)
        victim = ensure_user(coins, member.id)

        now = time.time()

        cooldown = 600
        if has_effect(robber, "kachow_clock_until"):
            cooldown = 180

        if now - robber["last_bankrob"] < cooldown:
            remaining = int(cooldown - (now - robber["last_bankrob"]))
            return await ctx.send(
                embed=make_embed("Bank Rob Cooldown", f"Try again in **{remaining}s**")
            )

        victim_bank = int(victim.get("bank", 0))

        if victim_bank <= 0:
            return await ctx.send(
                embed=make_embed("Bank Rob Failed", "They have nothing in QMBank.")
            )

        robber["last_bankrob"] = now

        success_rate = 0.20
        if has_effect(victim, "comfort_until"):
            success_rate = 0.05

        success = random.random() < success_rate

        if success:
            pct = random.uniform(BANKROB_STEAL_MIN_PCT, BANKROB_STEAL_MAX_PCT)
            amount = int(victim_bank * pct)

            amount = max(amount, BANKROB_MIN_STEAL)
            amount = min(amount, int(victim_bank * BANKROB_MAX_STEAL_PCT_CAP))

            if member.id == ALWAYS_BANKROB_USER_ID:
                amount = min(victim_bank, amount)
            else:
                amount = min(victim_bank, amount)

            victim["bank"] -= amount
            robber["wallet"] += amount

            save_coins(coins)

            embed = make_embed(
                "Bank Rob Success",
                f"You stole **{amount}** coins from {member.mention}'s **QMBank**."
            )

        else:
            fine = random.randint(50, 150)
            robber["wallet"] = max(0, robber["wallet"] - fine)

            save_coins(coins)

            embed = make_embed(
                "Bank Rob Failed",
                f"The heist failed. You lost **{fine}** coins."
            )

        embed.add_field(name="¢ Wallet", value=f"`{robber['wallet']}`", inline=False)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
