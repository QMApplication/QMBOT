import discord
from discord.ext import commands
import time

from storage import load_coins, save_coins, load_stocks
from config import STOCKS


TRADE_SETTLEMENT_TIME = 120  # seconds


def ensure_user(user_id):
    coins = load_coins()
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0,
            "portfolio": {},
            "pending_portfolio": [],
            "trade_meta": {
                "last_trade_ts": {},
                "daily": {"day": "", "count": 0}
            }
        }
        save_coins(coins)

    else:
        coins[uid].setdefault("portfolio", {})
        coins[uid].setdefault("pending_portfolio", [])
        coins[uid].setdefault("trade_meta", {
            "last_trade_ts": {},
            "daily": {"day": "", "count": 0}
        })

    return coins


class Stocks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # STOCK LIST
    # -------------------------

    @commands.command()
    async def stocks(self, ctx):

        stocks = load_stocks()

        desc = ""

        for name in STOCKS:

            price = stocks[name]["price"]

            desc += f"**{name}** — {price} coins\n"

        embed = discord.Embed(
            title="📈 Stock Market",
            description=desc,
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)

    # -------------------------
    # STOCK VALUE
    # -------------------------

    @commands.command()
    async def stockvalue(self, ctx, stock: str):

        stock = stock.capitalize()

        stocks = load_stocks()

        if stock not in stocks:
            return await ctx.send("Unknown stock.")

        data = stocks[stock]

        price = data["price"]
        history = data.get("history", [])

        change = 0
        if len(history) > 1:
            change = price - history[-2]

        embed = discord.Embed(
            title=f"{stock} Stock",
            color=discord.Color.blue()
        )

        embed.add_field(name="Price", value=price)

        embed.add_field(name="Change", value=change)

        await ctx.send(embed=embed)

    # -------------------------
    # PORTFOLIO
    # -------------------------

    @commands.command()
    async def portfolio(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        coins = ensure_user(member.id)

        user = coins[str(member.id)]

        pf = user.get("portfolio", {})

        stocks = load_stocks()

        desc = ""

        total = 0

        for s in STOCKS:

            qty = pf.get(s, 0)

            if qty > 0:

                value = qty * stocks[s]["price"]

                total += value

                desc += f"{s}: {qty} shares ({value})\n"

        if desc == "":
            desc = "No stocks."

        embed = discord.Embed(
            title=f"{member.display_name}'s Portfolio",
            description=desc
        )

        embed.add_field(name="Total Value", value=total)

        await ctx.send(embed=embed)

    # -------------------------
    # BUY STOCK
    # -------------------------

    @commands.command()
    async def buy(self, ctx, stock: str, amount: int):

        stock = stock.capitalize()

        if stock not in STOCKS:
            return await ctx.send("Unknown stock.")

        stocks = load_stocks()

        price = stocks[stock]["price"]

        cost = price * amount

        coins = ensure_user(ctx.author.id)

        user = coins[str(ctx.author.id)]

        if amount <= 0:
            return await ctx.send("Invalid amount.")

        if user["wallet"] < cost:
            return await ctx.send("Not enough coins.")

        user["wallet"] -= cost

        user["pending_portfolio"].append({
            "stock": stock,
            "shares": amount,
            "settles_at": time.time() + TRADE_SETTLEMENT_TIME
        })

        save_coins(coins)

        # notify market engine
        tasks = self.bot.get_cog("BackgroundTasks")
        if tasks:
            tasks.record_trade(stock, "buy", amount)

        await ctx.send(
            f"📈 Bought **{amount}** {stock} shares.\n"
            f"Settlement in {TRADE_SETTLEMENT_TIME}s."
        )

    # -------------------------
    # SELL STOCK
    # -------------------------

    @commands.command()
    async def sell(self, ctx, stock: str, amount: int):

        stock = stock.capitalize()

        if stock not in STOCKS:
            return await ctx.send("Unknown stock.")

        coins = ensure_user(ctx.author.id)

        user = coins[str(ctx.author.id)]

        pf = user["portfolio"]

        owned = pf.get(stock, 0)

        if amount <= 0 or owned < amount:
            return await ctx.send("Not enough shares.")

        stocks = load_stocks()

        price = stocks[stock]["price"]

        revenue = price * amount

        pf[stock] -= amount

        user["wallet"] += revenue

        save_coins(coins)

        tasks = self.bot.get_cog("BackgroundTasks")
        if tasks:
            tasks.record_trade(stock, "sell", amount)

        await ctx.send(
            f"📉 Sold **{amount}** {stock} shares for **{revenue}** coins."
        )

    # -------------------------
    # CLAIM SETTLED SHARES
    # -------------------------

    @commands.command()
    async def claim(self, ctx):

        coins = ensure_user(ctx.author.id)

        user = coins[str(ctx.author.id)]

        pending = user["pending_portfolio"]

        now = time.time()

        claimed = 0

        for lot in pending[:]:

            if lot["settles_at"] <= now:

                stock = lot["stock"]

                qty = lot["shares"]

                user["portfolio"][stock] = user["portfolio"].get(stock, 0) + qty

                pending.remove(lot)

                claimed += qty

        save_coins(coins)

        if claimed == 0:
            return await ctx.send("No shares ready.")

        await ctx.send(f"✅ Claimed **{claimed}** shares.")


async def setup(bot):
    await bot.add_cog(Stocks(bot))
