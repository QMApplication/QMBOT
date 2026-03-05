# cogs/tasks.py
import random
from pathlib import Path
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

import storage  # so we can use storage.DATA_PATH
from config import (
    INTEREST_INTERVAL, INTEREST_RATE,
    DIVIDEND_INTERVAL, DIVIDEND_RATE,
    MARKET_ANNOUNCE_CHANNEL_ID,
    STOCKS,
    PACKAGE_USER_ID,
    PACKAGE_FILES,
)
from storage import load_coins, save_coins, load_stocks, save_stocks
from utils import build_zip_bytes


def _ensure_stock_db():
    s = load_stocks()
    changed = False
    for name in STOCKS:
        if name not in s or not isinstance(s.get(name), dict):
            s[name] = {"price": random.randint(80, 250), "history": []}
            changed = True
        s[name].setdefault("price", random.randint(80, 250))
        s[name].setdefault("history", [])
        if not s[name]["history"]:
            s[name]["history"] = [int(s[name]["price"])]
            changed = True
    if changed:
        save_stocks(s)
    return s


async def dm_backup_zip(bot: commands.Bot, user_id: int, reason: str):
    try:
        user = await bot.fetch_user(int(user_id))
    except Exception as e:
        print(f"[Backup] fetch_user failed: {e}")
        return False

    # PACKAGE_FILES are base names; our JSON lives under storage.DATA_PATH (DATA_DIR)
    paths = [str(Path(storage.DATA_PATH) / fname) for fname in PACKAGE_FILES]
    buf, included = build_zip_bytes(paths, folder_name="bot_backup")

    if not included:
        try:
            await user.send(f"⚠️ Backup ({reason}) — no files found.")
        except Exception:
            pass
        return True

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S_UTC")
    file = discord.File(buf, filename=f"qmul_bot_backup_{ts}.zip")

    try:
        await user.send(
            content=f"📦 **Bot Backup** ({reason})\nIncluded: {', '.join(Path(x).name for x in included)}",
            file=file
        )
        return True
    except discord.Forbidden:
        print("[Backup] DM forbidden (DMs closed / blocked).")
        return False
    except Exception as e:
        print(f"[Backup] send failed: {e}")
        return False


class BackgroundTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Track purchases if you later connect buy/sell cogs into this
        self.stock_purchase_count = {s: 0 for s in STOCKS}

        self.apply_bank_interest.start()
        self.update_stock_prices.start()
        self.pay_dividends.start()
        self.send_backup_zip_every_5h.start()

    def cog_unload(self):
        self.apply_bank_interest.cancel()
        self.update_stock_prices.cancel()
        self.pay_dividends.cancel()
        self.send_backup_zip_every_5h.cancel()

    @tasks.loop(seconds=INTEREST_INTERVAL)
    async def apply_bank_interest(self):
        coins = load_coins()
        changed = False
        for _uid, balances in coins.items():
            bank = int(balances.get("bank", 0) or 0)
            if bank > 0:
                interest = int(bank * INTEREST_RATE)
                if interest > 0:
                    balances["bank"] = bank + interest
                    changed = True
        if changed:
            save_coins(coins)
            print("[Interest] applied")

    @tasks.loop(minutes=5)
    async def update_stock_prices(self):
        stocks = _ensure_stock_db()

        # small random drift + occasional boom/crash
        crash = random.randint(1, 18) == 1
        boom = random.randint(1, 18) == 1

        crashed = []
        boomed = []

        for s in STOCKS:
            cur = int(stocks[s]["price"])
            if crash and cur > 200:
                new = max(1, int(cur * random.uniform(0.45, 0.85)))
                crashed.append((s, cur, new))
            elif boom and cur < 3000:
                new = int(cur * random.uniform(1.6, 2.4))
                boomed.append((s, cur, new))
            else:
                new = max(1, int(cur * (1 + random.uniform(-0.03, 0.05))))
            stocks[s]["price"] = new
            stocks[s].setdefault("history", []).append(new)
            if len(stocks[s]["history"]) > 24:
                stocks[s]["history"] = stocks[s]["history"][-24:]

        save_stocks(stocks)

        channel = self.bot.get_channel(MARKET_ANNOUNCE_CHANNEL_ID)
        if not channel:
            return

        if crashed:
            desc = "\n".join(f"🔻 **{s}** {old} → **{new}**" for s, old, new in crashed)
            await channel.send(embed=discord.Embed(
                title="📉 Market Crash!",
                description=desc,
                color=discord.Color.red()
            ))
        if boomed:
            desc = "\n".join(f"📈 **{s}** {old} → **{new}**" for s, old, new in boomed)
            await channel.send(embed=discord.Embed(
                title="📈 Market Boom!",
                description=desc,
                color=discord.Color.green()
            ))

    @tasks.loop(seconds=DIVIDEND_INTERVAL)
    async def pay_dividends(self):
        coins = load_coins()
        stocks = _ensure_stock_db()
        any_payout = False

        for _uid, data in coins.items():
            pf = (data.get("portfolio") or {})
            total_value = 0
            for s in STOCKS:
                qty = int(pf.get(s, 0) or 0)
                total_value += qty * int(stocks[s]["price"])
            payout = int(total_value * DIVIDEND_RATE)
            if payout > 0:
                data["wallet"] = int(data.get("wallet", 0) or 0) + payout
                any_payout = True

        if any_payout:
            save_coins(coins)
            channel = self.bot.get_channel(MARKET_ANNOUNCE_CHANNEL_ID)
            if channel:
                await channel.send("💸 Dividends have been paid out to all shareholders!")

    @tasks.loop(hours=5)
    async def send_backup_zip_every_5h(self):
        await dm_backup_zip(self.bot, PACKAGE_USER_ID, reason="Every 5 hours")

    @send_backup_zip_every_5h.before_loop
    async def before_backup_loop(self):
        await self.bot.wait_until_ready()
        # send once on boot
        await dm_backup_zip(self.bot, PACKAGE_USER_ID, reason="Bot started")

    @apply_bank_interest.before_loop
    @update_stock_prices.before_loop
    @pay_dividends.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(BackgroundTasks(bot))
