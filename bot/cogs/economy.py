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
    BANKROB_MAX_STEAL_PCT_CAP,
)
from ui_utils import C, E, embed, success, error, warn, cooldown_str, balance_bar

# ─── Constants ────────────────────────────────────────────────────────────────

DEBT_INTEREST_RATE     = 0.03
DEBT_INTEREST_INTERVAL = 3600

TAX_BRACKETS = [
    (500,          0.10),
    (2000,         0.20),
    (5000,         0.30),
    (10000,        0.40),
    (float("inf"), 0.50),
]

WORK_COOLDOWN = 3600
WORK_REWARDS = [
    ("You debugged someone's spaghetti code",        80,  200),
    ("You delivered food through a storm",            50,  150),
    ("You tutored a panicking first-year",           100,  250),
    ("You drove strangers around all evening",        60,  180),
    ("You flipped burgers for 8 brutal hours",        70,  160),
    ("You freelanced a logo at 2 AM",               120,  300),
    ("You sold old clothes online for profit",        40,  120),
    ("You walked someone's overexcited dog",          30,  100),
    ("You worked a quiet library shift",              80,  170),
    ("You ghost-wrote an essay for a rich kid",      150,  350),
    ("You moderated an online forum all day",         90,  220),
    ("You streamed to three viewers and a bot",       60,  160),
    ("You fixed a boomer's printer remotely",        110,  240),
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

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
        user["star_meta"] = {"day": _today_key(), "given": {}}


def ensure_user(coins, user_id):
    uid = str(user_id)
    defaults = {
        "wallet": 100, "bank": 0, "debt": 0, "debt_since": 0,
        "stars": 0, "last_daily": 0, "last_beg": 0,
        "last_rob": 0, "last_bankrob": 0, "last_work": 0,
        "active_effects": {},
        "star_meta": {"day": _today_key(), "given": {}},
    }
    if uid not in coins:
        coins[uid] = dict(defaults)
    else:
        for k, v in defaults.items():
            coins[uid].setdefault(k, v)
        _reset_star_meta_if_needed(coins[uid])
    return coins[uid]


def has_effect(user: dict, effect: str) -> bool:
    effects = user.get("active_effects", {})
    return effect in effects and effects[effect] > time.time()


def calculate_tax(amount: int) -> tuple[int, float]:
    for threshold, rate in TAX_BRACKETS:
        if amount <= threshold:
            return int(amount * rate), rate
    return int(amount * 0.50), 0.50


def accrue_debt_interest(user: dict) -> int:
    debt = int(user.get("debt", 0))
    if debt <= 0:
        return 0
    debt_since = float(user.get("debt_since", 0))
    full_hours = int((time.time() - debt_since) / DEBT_INTEREST_INTERVAL)
    if full_hours < 1:
        return debt
    new_debt = int(debt * ((1 + DEBT_INTEREST_RATE) ** full_hours))
    user["debt"] = new_debt
    user["debt_since"] = debt_since + full_hours * DEBT_INTEREST_INTERVAL
    return new_debt


# ─── Cog ──────────────────────────────────────────────────────────────────────

class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── BALANCE ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="balance", description="Check your coin balance.")
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        coins  = load_coins()
        user   = ensure_user(coins, member.id)
        debt   = accrue_debt_interest(user)
        save_coins(coins)

        is_you = member == ctx.author
        desc = (
            f"{E.WALLET} **Wallet** › `{user['wallet']:,}` coins\n"
            f"{E.BANK} **QMBank** › `{user['bank']:,}` coins\n"
            f"{E.STAR} **Stars** › `{user['stars']:,}`"
        )
        if debt > 0:
            desc += f"\n{E.DEBT} **Debt** › `{debt:,}` coins *(3 % / hr)*"

        total = user['wallet'] + user['bank']
        e = embed(
            f"{E.CROWN}  {member.display_name}'s Balance",
            desc,
            color=C.ECONOMY,
            footer=f"Total wealth: {total:,} coins",
        )
        e.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=e)

    # ── DEPOSIT ───────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="deposit", description="Deposit coins into your bank.")
    async def deposit(self, ctx, amount: str):
        coins = load_coins()
        user  = ensure_user(coins, ctx.author.id)
        amt   = user["wallet"] if amount.lower() == "all" else (int(amount) if amount.isdigit() else None)
        if amt is None:
            return await ctx.send(embed=error("Deposit", "Enter a number or `all`."))
        if amt <= 0 or amt > user["wallet"]:
            return await ctx.send(embed=error("Deposit", f"You only have `{user['wallet']:,}` coins in your wallet."))
        user["wallet"] -= amt
        user["bank"]   += amt
        save_coins(coins)
        e = success("Deposited!", f"Moved **{amt:,}** coins into {E.BANK} **QMBank**.")
        e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=True)
        e.add_field(name=f"{E.BANK} QMBank",   value=f"`{user['bank']:,}`",   inline=True)
        await ctx.send(embed=e)

    # ── WITHDRAW ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="withdraw", description="Withdraw coins from your bank.")
    async def withdraw(self, ctx, amount: str):
        coins = load_coins()
        user  = ensure_user(coins, ctx.author.id)
        amt   = user["bank"] if amount.lower() == "all" else (int(amount) if amount.isdigit() else None)
        if amt is None:
            return await ctx.send(embed=error("Withdraw", "Enter a number or `all`."))
        if amt <= 0 or amt > user["bank"]:
            return await ctx.send(embed=error("Withdraw", f"You only have `{user['bank']:,}` coins in the bank."))
        user["bank"]   -= amt
        user["wallet"] += amt
        save_coins(coins)
        e = success("Withdrawn!", f"Moved **{amt:,}** coins to your {E.WALLET} wallet.")
        e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=True)
        e.add_field(name=f"{E.BANK} QMBank",   value=f"`{user['bank']:,}`",   inline=True)
        await ctx.send(embed=e)

    # ── DAILY ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="daily", description="Claim your daily coins.")
    async def daily(self, ctx):
        coins = load_coins()
        user  = ensure_user(coins, ctx.author.id)
        now   = datetime.now(timezone.utc)
        last  = datetime.fromtimestamp(user["last_daily"], timezone.utc)
        if last.date() == now.date():
            tomorrow  = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            remaining = cooldown_str(int((tomorrow - now).total_seconds()))
            return await ctx.send(embed=warn("Daily Already Claimed", f"{E.CLOCK} Come back in **{remaining}**."))
        reward = random.randint(100, 500)
        user["wallet"] += reward
        user["last_daily"] = now.timestamp()
        save_coins(coins)
        e = success("Daily Reward!", f"{E.COIN} You received **{reward:,}** coins!")
        e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=False)
        e.set_footer(text="Come back tomorrow for your next reward!")
        await ctx.send(embed=e)

    # ── BEG ───────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="beg", description="Beg for some spare change.")
    async def beg(self, ctx):
        coins = load_coins()
        user  = ensure_user(coins, ctx.author.id)
        now   = time.time()
        if now - user["last_beg"] < 120:
            remaining = cooldown_str(int(120 - (now - user["last_beg"])))
            return await ctx.send(embed=warn("Slow Down", f"People are tired of you. Try again in **{remaining}**."))
        responses = [
            "A kind stranger tossed you some change.",
            "Someone felt sorry for you.",
            "A passing NPC dropped their wallet.",
            "The universe took pity on you.",
            "A pigeon dropped coins. Somehow.",
        ]
        amount = random.randint(5, 50)
        user["wallet"] += amount
        user["last_beg"] = now
        save_coins(coins)
        e = embed(f"{E.BEG}  Begging Result", f"{random.choice(responses)}\n\n{E.COIN} You got **{amount}** coins.", C.ECONOMY)
        e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=False)
        await ctx.send(embed=e)

    # ── WORK ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="work", description="Do some work and earn coins (1 hr cooldown).")
    async def work(self, ctx):
        coins = load_coins()
        user  = ensure_user(coins, ctx.author.id)
        now   = time.time()
        if now - user["last_work"] < WORK_COOLDOWN:
            remaining = cooldown_str(int(WORK_COOLDOWN - (now - user["last_work"])))
            return await ctx.send(embed=warn("Too Tired", f"{E.CLOCK} You need rest. Come back in **{remaining}**."))
        desc, min_pay, max_pay = random.choice(WORK_REWARDS)
        earned = random.randint(min_pay, max_pay)
        tax, rate = calculate_tax(earned)
        net = earned - tax
        user["wallet"] += net
        user["last_work"] = now
        save_coins(coins)
        e = success("Payday!", f"_{desc}._")
        e.add_field(name=f"{E.COIN} Gross",          value=f"`{earned:,}` coins", inline=True)
        e.add_field(name=f"{E.TAX} Tax ({int(rate*100)}%)", value=f"`-{tax:,}` coins",  inline=True)
        e.add_field(name=f"{E.WORK} Net Pay",         value=f"`+{net:,}` coins",  inline=True)
        e.add_field(name=f"{E.WALLET} Wallet",        value=f"`{user['wallet']:,}`", inline=False)
        e.set_footer(text="Cooldown: 1 hour")
        await ctx.send(embed=e)

    # ── PAY ───────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="pay", description="Send coins to another user.")
    async def pay(self, ctx, member: discord.Member, amount: str):
        if member == ctx.author:
            return await ctx.send(embed=error("Pay", "You can't pay yourself."))
        if member.bot:
            return await ctx.send(embed=error("Pay", "Bots don't accept tips."))
        coins    = load_coins()
        sender   = ensure_user(coins, ctx.author.id)
        receiver = ensure_user(coins, member.id)
        amt      = sender["wallet"] if amount.lower() == "all" else (int(amount) if amount.isdigit() else None)
        if amt is None:
            return await ctx.send(embed=error("Pay", "Enter a number or `all`."))
        if amt <= 0:
            return await ctx.send(embed=error("Pay", "Amount must be positive."))
        if sender["wallet"] < amt:
            return await ctx.send(embed=error("Pay", f"You only have `{sender['wallet']:,}` coins."))
        sender["wallet"]   -= amt
        receiver["wallet"] += amt
        save_coins(coins)
        e = success("Payment Sent!", f"{ctx.author.mention} sent **{amt:,}** {E.COIN} to {member.mention}.")
        e.add_field(name="Your Wallet",             value=f"`{sender['wallet']:,}`",   inline=True)
        e.add_field(name=f"{member.display_name}'s Wallet", value=f"`{receiver['wallet']:,}`", inline=True)
        await ctx.send(embed=e)

    # ── TAX ───────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="tax", description="Calculate the tax you'd pay on an amount.")
    async def tax(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send(embed=error("Tax", "Amount must be positive."))
        tax_amt, rate = calculate_tax(amount)
        net = amount - tax_amt
        brackets = []
        prev = 0
        found = False
        for threshold, r in TAX_BRACKETS:
            label = f"up to {int(threshold):,}" if threshold != float("inf") else f"{prev:,}+"
            mark  = " ◄ your bracket" if not found and amount <= threshold else ""
            if mark:
                found = True
            brackets.append(f"`{label}` → {int(r*100)}%{mark}")
            prev = int(threshold) if threshold != float("inf") else prev
        e = embed(
            f"{E.TAX}  Tax Calculator",
            f"**Amount:** {amount:,} coins\n"
            f"**Rate:** {int(rate*100)}%\n"
            f"**Tax Owed:** `{tax_amt:,}` coins\n"
            f"**Net After Tax:** `{net:,}` coins\n\n"
            + "\n".join(brackets),
            C.ECONOMY,
        )
        await ctx.send(embed=e)

    # ── DEBT ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="debt", description="Check your current debt balance.")
    async def debt(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        coins  = load_coins()
        user   = ensure_user(coins, member.id)
        debt   = accrue_debt_interest(user)
        save_coins(coins)
        if debt <= 0:
            return await ctx.send(embed=success("Debt Free!", f"{member.display_name} owes nothing. 🎉"))
        e = embed(
            f"{E.DEBT}  {member.display_name}'s Debt",
            f"Current debt: **{debt:,}** coins\n\n"
            f"{E.CLOCK} Interest compounds at **3% per hour**.\n"
            f"Use `/repaydebt` to pay it down.",
            C.DEBT,
        )
        await ctx.send(embed=e)

    # ── REPAY DEBT ────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="repaydebt", description="Repay your debt (or part of it).")
    async def repaydebt(self, ctx, amount: str = "all"):
        coins = load_coins()
        user  = ensure_user(coins, ctx.author.id)
        debt  = accrue_debt_interest(user)
        if debt <= 0:
            return await ctx.send(embed=success("No Debt!", "You have nothing to repay. 🎉"))
        pay = min(debt, user["wallet"]) if amount.lower() == "all" else (int(amount) if amount.isdigit() else None)
        if pay is None:
            return await ctx.send(embed=error("Repay", "Enter a number or `all`."))
        if pay <= 0:
            return await ctx.send(embed=error("Repay", "Amount must be positive."))
        if user["wallet"] < pay:
            pay = user["wallet"]
        if pay == 0:
            return await ctx.send(embed=error("Repay", "You have no coins to repay with."))
        user["wallet"] -= pay
        user["debt"]    = max(0, debt - pay)
        if user["debt"] == 0:
            user["debt_since"] = 0
        save_coins(coins)
        remaining = user["debt"]
        if remaining == 0:
            e = success("Debt Cleared! 🎉", f"You paid **{pay:,}** coins and are now debt-free!")
        else:
            e = embed(
                f"{E.DEBT}  Partial Repayment",
                f"Paid **{pay:,}** coins.\n{E.CLOCK} Remaining: **{remaining:,}** coins.",
                C.WARN,
            )
        e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=False)
        await ctx.send(embed=e)

    # ── STAR (give) ───────────────────────────────────────────────────────────

    @commands.hybrid_command(name="star", description="Give someone a golden star.")
    async def star(self, ctx, member: discord.Member):
        if member == ctx.author:
            return await ctx.send(embed=error("Golden Star", "You can't star yourself."))
        if member.bot:
            return await ctx.send(embed=error("Golden Star", "Bots don't collect stars."))
        coins    = load_coins()
        giver    = ensure_user(coins, ctx.author.id)
        receiver = ensure_user(coins, member.id)
        _reset_star_meta_if_needed(giver)
        key = str(member.id)
        given_today = int(giver["star_meta"]["given"].get(key, 0))
        if given_today >= 2:
            return await ctx.send(embed=warn("Limit Reached", f"You've already given **2** stars to {member.mention} today."))
        giver["star_meta"]["given"][key] = given_today + 1
        receiver["stars"] += 1
        save_coins(coins)
        e = embed(
            f"{E.STAR}  Star Given!",
            f"{ctx.author.mention} gifted {member.mention} a **golden star**!",
            C.TRIVIA,
        )
        e.add_field(name=f"{member.display_name}'s Stars", value=f"`{receiver['stars']:,}` {E.STAR}", inline=False)
        await ctx.send(embed=e)

    # ── STARS (check) ─────────────────────────────────────────────────────────

    @commands.hybrid_command(name="stars", description="Check how many golden stars you have.")
    async def stars(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        coins  = load_coins()
        user   = ensure_user(coins, member.id)
        e = embed(
            f"{E.STAR}  {member.display_name}'s Stars",
            f"**{user['stars']:,}** golden stars",
            C.TRIVIA,
        )
        e.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=e)

    # ── STAR LEADERBOARD ──────────────────────────────────────────────────────

    @commands.hybrid_command(name="starleaderboard", description="Star leaderboard.")
    async def starleaderboard(self, ctx):
        coins = load_coins()
        board = sorted(coins.items(), key=lambda x: int(x[1].get("stars", 0)), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines  = []
        for i, (uid, data) in enumerate(board):
            stars  = data.get("stars", 0)
            member = ctx.guild.get_member(int(uid)) if ctx.guild else None
            name   = member.display_name if member else f"User {uid}"
            you    = "  ← you" if int(uid) == ctx.author.id else ""
            medal  = medals[i] if i < 3 else f"{i+1}."
            lines.append(f"{medal}  **{name}** — `{stars:,}` {E.STAR}{you}")
        e = embed(f"{E.TROPHY}  Star Leaderboard", "\n".join(lines) or "No data.", C.TRIVIA)
        await ctx.send(embed=e)

    # ── BAL TOP ───────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="baltop", description="Richest users leaderboard.")
    async def baltop(self, ctx):
        coins = load_coins()
        board = sorted(coins.items(), key=lambda x: x[1].get("wallet", 0) + x[1].get("bank", 0), reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"]
        lines  = []
        for i, (uid, data) in enumerate(board):
            total  = data.get("wallet", 0) + data.get("bank", 0)
            member = ctx.guild.get_member(int(uid)) if ctx.guild else None
            name   = member.display_name if member else f"User {uid}"
            you    = "  ← you" if int(uid) == ctx.author.id else ""
            medal  = medals[i] if i < 3 else f"{i+1}."
            lines.append(
                f"{medal}  **{name}**{you}\n"
                f"     {E.WALLET} `{data.get('wallet',0):,}`  {E.BANK} `{data.get('bank',0):,}`  · Total `{total:,}`"
            )
        e = embed(f"{E.TROPHY}  Balance Leaderboard", "\n".join(lines) or "No data.", C.ECONOMY)
        await ctx.send(embed=e)

    # ── ROB ───────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="rob", description="Attempt to rob someone's wallet.")
    async def rob(self, ctx, member: discord.Member):
        if member == ctx.author:
            return await ctx.send(embed=error("Rob", "You can't rob yourself."))
        if member.bot:
            return await ctx.send(embed=error("Rob", "Bots have no coins to steal."))
        coins  = load_coins()
        robber = ensure_user(coins, ctx.author.id)
        victim = ensure_user(coins, member.id)
        now    = time.time()
        cd     = 60 if has_effect(robber, "kachow_clock_until") else 300
        if now - robber["last_rob"] < cd:
            return await ctx.send(embed=warn("Rob Cooldown", f"{E.CLOCK} Try again in **{cooldown_str(int(cd-(now-robber['last_rob'])))}**."))
        if int(victim.get("wallet", 0)) <= 0:
            return await ctx.send(embed=warn("Rob Failed", f"{member.display_name} is completely broke. Nothing to steal."))
        robber["last_rob"] = now
        success_rate = 0.20 if has_effect(victim, "comfort_until") else 0.40
        if random.random() < success_rate:
            steal = random.randint(10, min(200, victim["wallet"]))
            victim["wallet"]  -= steal
            robber["wallet"]  += steal
            save_coins(coins)
            e = embed(f"{E.ROB}  Robbery Success!", f"You swiped **{steal:,}** coins from {member.mention}. Slick move.", C.WIN)
            e.add_field(name=f"{E.WALLET} Your Wallet", value=f"`{robber['wallet']:,}`", inline=True)
        else:
            debt_added   = random.randint(30, 100)
            interest_now = int(debt_added * DEBT_INTEREST_RATE)
            old_debt     = int(robber.get("debt", 0))
            robber["debt"] = old_debt + debt_added
            if old_debt == 0:
                robber["debt_since"] = now
            hit = min(robber["wallet"], interest_now)
            robber["wallet"] = max(0, robber["wallet"] - hit)
            save_coins(coins)
            e = embed(
                f"{E.LOSE}  Busted!",
                f"You got caught trying to rob {member.mention}.\n\n"
                f"{E.DEBT} **Debt added:** `{debt_added:,}` coins\n"
                f"{E.COIN} **Interest hit:** `-{hit:,}` coins\n\n"
                f"*Interest grows at 3%/hr — use `/repaydebt` fast!*",
                C.LOSE,
            )
            e.add_field(name=f"{E.WALLET} Wallet", value=f"`{robber['wallet']:,}`", inline=True)
            e.add_field(name=f"{E.DEBT} Debt",     value=f"`{robber['debt']:,}`",   inline=True)
        await ctx.send(embed=e)

    # ── BANK ROB ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="bankrob", description="Attempt to rob someone's bank.")
    async def bankrob(self, ctx, member: discord.Member):
        if member == ctx.author:
            return await ctx.send(embed=error("Bank Rob", "You can't rob your own bank."))
        if member.bot:
            return await ctx.send(embed=error("Bank Rob", "Bots have no banks."))
        coins  = load_coins()
        robber = ensure_user(coins, ctx.author.id)
        victim = ensure_user(coins, member.id)
        now    = time.time()
        cd     = 180 if has_effect(robber, "kachow_clock_until") else 600
        if now - robber["last_bankrob"] < cd:
            return await ctx.send(embed=warn("Cooldown", f"{E.CLOCK} Try again in **{cooldown_str(int(cd-(now-robber['last_bankrob'])))}**."))
        if int(victim.get("bank", 0)) <= 0:
            return await ctx.send(embed=warn("Bank Rob Failed", f"{member.display_name} has nothing in their bank."))
        robber["last_bankrob"] = now
        success_rate = 0.05 if has_effect(victim, "comfort_until") else 0.20
        if random.random() < success_rate:
            pct    = random.uniform(BANKROB_STEAL_MIN_PCT, BANKROB_STEAL_MAX_PCT)
            amount = max(BANKROB_MIN_STEAL, int(victim["bank"] * pct))
            amount = min(amount, int(victim["bank"] * BANKROB_MAX_STEAL_PCT_CAP), victim["bank"])
            victim["bank"]    -= amount
            robber["wallet"]  += amount
            save_coins(coins)
            e = embed(f"{E.BANK}  Bank Heist Success!", f"You cracked {member.mention}'s vault and grabbed **{amount:,}** coins!", C.WIN)
            e.add_field(name=f"{E.WALLET} Your Wallet", value=f"`{robber['wallet']:,}`", inline=True)
        else:
            debt_added   = random.randint(80, 200)
            interest_now = int(debt_added * DEBT_INTEREST_RATE)
            old_debt     = int(robber.get("debt", 0))
            robber["debt"] = old_debt + debt_added
            if old_debt == 0:
                robber["debt_since"] = now
            hit = min(robber["wallet"], interest_now)
            robber["wallet"] = max(0, robber["wallet"] - hit)
            save_coins(coins)
            e = embed(
                f"{E.LOSE}  Heist Failed!",
                f"Security caught you outside {member.mention}'s vault.\n\n"
                f"{E.DEBT} **Debt added:** `{debt_added:,}` coins\n"
                f"{E.COIN} **Interest hit:** `-{hit:,}` coins\n\n"
                f"*Interest grows at 3%/hr — use `/repaydebt` fast!*",
                C.LOSE,
            )
            e.add_field(name=f"{E.WALLET} Wallet", value=f"`{robber['wallet']:,}`", inline=True)
            e.add_field(name=f"{E.DEBT} Debt",     value=f"`{robber['debt']:,}`",   inline=True)
        await ctx.send(embed=e)

    # ── RESET ECONOMY ─────────────────────────────────────────────────────────

    @commands.hybrid_command(name="reseteconomy", description="Reset all balances (admin only).")
    @commands.has_permissions(administrator=True)
    async def reseteconomy(self, ctx):
        from storage import load_data, save_data
        coins = load_coins()
        for uid in coins:
            coins[uid]["wallet"]     = 100
            coins[uid]["bank"]       = 0
            coins[uid]["debt"]       = 0
            coins[uid]["debt_since"] = 0
        save_coins(coins)
        data = load_data()
        data["economy_reset_ts"] = time.time()
        save_data(data)
        e = embed(
            f"{E.WARN_ACT}  Economy Reset",
            "All wallets reset to **100** coins. Banks and debts cleared.\n\n"
            f"⚠️ Trivia prizes are **reduced by 75%** for the next 24 hours.",
            C.WARN,
            footer=f"Reset by {ctx.author.display_name}",
        )
        await ctx.send(embed=e)

    @reseteconomy.error
    async def reseteconomy_error(self, ctx, err):
        if isinstance(err, commands.MissingPermissions):
            await ctx.send(embed=error("Permission Denied", "You need **Administrator** to use this."))


async def setup(bot):
    await bot.add_cog(Economy(bot))
