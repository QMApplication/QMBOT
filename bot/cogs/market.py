import io

import discord
import matplotlib.pyplot as plt
import numpy as np
from discord.ext import commands

from storage import load_coins, save_coins, load_stocks
from config import STOCKS


def ensure_user(coins, user_id):
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0,
            "portfolio": {}
        }

    coins[uid].setdefault("portfolio", {})

    return coins[uid]


class Stocks(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # STOCK LIST
    # -------------------------

    @commands.hybrid_command(
        name="stocks",
        description="View all stock prices."
    )
    async def stocks(self, ctx: commands.Context):

        stocks = load_stocks()

        desc = ""

        for name in STOCKS:
            price = stocks.get(name, {}).get("price", 0)
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

    @commands.hybrid_command(
        name="stockvalue",
        description="Show a stock's price and chart."
    )
    async def stockvalue(self, ctx: commands.Context, stock: str):

        stock_names = {s.lower(): s for s in STOCKS}
        key = stock.lower().strip()

        if key not in stock_names:
            return await ctx.send("Unknown stock.")

        stock_name = stock_names[key]

        stocks = load_stocks()
        data = stocks.get(stock_name)

        if not data:
            return await ctx.send("Unknown stock.")

        price = int(data.get("price", 0))
        history = data.get("history", []) or []

        change = 0
        if len(history) > 1:
            change = price - int(history[-2])

        if len(history) < 2:
            embed = discord.Embed(
                title=f"{stock_name} Stock",
                color=discord.Color.blue()
            )
            embed.add_field(name="Price", value=price)
            embed.add_field(name="Change", value=change)
            embed.add_field(name="Chart", value="Not enough history yet.")
            return await ctx.send(embed=embed)

        x = np.arange(len(history))
        y = np.array(history, dtype=float)

        plt.figure(figsize=(7, 4))
        plt.plot(x, y, marker="o")
        plt.title(f"{stock_name} Price History")
        plt.xlabel("Update")
        plt.ylabel("Price")
        plt.grid(True)

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)

        file = discord.File(buf, filename="stock.png")

        embed = discord.Embed(
            title=f"{stock_name} Stock",
            color=discord.Color.blue()
        )
        embed.add_field(name="Price", value=price)
        embed.add_field(name="Change", value=f"{change:+}")
        embed.set_image(url="attachment://stock.png")

        await ctx.send(embed=embed, file=file)

    # -------------------------
    # PORTFOLIO
    # -------------------------

    @commands.hybrid_command(
        name="portfolio",
        description="View your stock portfolio."
    )
    async def portfolio(self, ctx: commands.Context, member: discord.Member = None):

        member = member or ctx.author

        coins = load_coins()
        user = ensure_user(coins, member.id)

        pf = user.get("portfolio", {})
        stocks = load_stocks()

        desc = ""
        total = 0

        for s in STOCKS:
            qty = int(pf.get(s, 0))

            if qty > 0:
                price = int(stocks.get(s, {}).get("price", 0))
                value = qty * price
                total += value
                desc += f"{s}: {qty} shares ({value})\n"

        if desc == "":
            desc = "No stocks."

        embed = discord.Embed(
            title=f"{member.display_name}'s Portfolio",
            description=desc,
            color=discord.Color.blue()
        )

        embed.add_field(name="Total Value", value=total)

        await ctx.send(embed=embed)

    # -------------------------
    # BUY STOCK
    # -------------------------

    @commands.hybrid_command(
        name="buy",
        description="Buy shares of a stock."
    )
    async def buy(self, ctx: commands.Context, stock: str, amount: int):

        stock_names = {s.lower(): s for s in STOCKS}
        key = stock.lower().strip()

        if key not in stock_names:
            return await ctx.send("Unknown stock.")

        if amount <= 0:
            return await ctx.send("Invalid amount.")

        stock_name = stock_names[key]

        stocks = load_stocks()
        price = int(stocks.get(stock_name, {}).get("price", 0))
        cost = price * amount

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        if user["wallet"] < cost:
            return await ctx.send("Not enough coins.")

        user["wallet"] -= cost

        pf = user["portfolio"]
        pf[stock_name] = int(pf.get(stock_name, 0)) + amount

        save_coins(coins)

        tasks = self.bot.get_cog("BackgroundTasks")
        if tasks:
            tasks.record_trade(stock_name, "buy", amount)

        await ctx.send(
            f"📈 Bought **{amount}** {stock_name} shares for **{cost}** coins."
        )

    # -------------------------
    # SELL STOCK
    # -------------------------

    @commands.hybrid_command(
        name="sell",
        description="Sell shares of a stock."
    )
    async def sell(self, ctx: commands.Context, stock: str, amount: int):

        stock_names = {s.lower(): s for s in STOCKS}
        key = stock.lower().strip()

        if key not in stock_names:
            return await ctx.send("Unknown stock.")

        if amount <= 0:
            return await ctx.send("Invalid amount.")

        stock_name = stock_names[key]

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        pf = user["portfolio"]
        owned = int(pf.get(stock_name, 0))

        if owned < amount:
            return await ctx.send("Not enough shares.")

        stocks = load_stocks()
        price = int(stocks.get(stock_name, {}).get("price", 0))
        revenue = price * amount

        pf[stock_name] = owned - amount
        user["wallet"] += revenue

        save_coins(coins)

        tasks = self.bot.get_cog("BackgroundTasks")
        if tasks:
            tasks.record_trade(stock_name, "sell", amount)

        await ctx.send(
            f"📉 Sold **{amount}** {stock_name} shares for **{revenue}** coins."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))
