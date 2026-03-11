import discord
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

    @commands.hybrid_command(
        name="stockvalue",
        description="Check the price of a stock."
    )
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

    @commands.hybrid_command(
        name="portfolio",
        description="View your stock portfolio."
    )
    async def portfolio(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        coins = load_coins()
        user = ensure_user(coins, member.id)

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

    @commands.hybrid_command(
        name="buy",
        description="Buy shares of a stock."
    )
    async def buy(self, ctx, stock: str, amount: int):

        stock = stock.capitalize()

        if stock not in STOCKS:
            return await ctx.send("Unknown stock.")

        if amount <= 0:
            return await ctx.send("Invalid amount.")

        stocks = load_stocks()
        price = stocks[stock]["price"]

        cost = price * amount

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        if user["wallet"] < cost:
            return await ctx.send("Not enough coins.")

        user["wallet"] -= cost

        pf = user["portfolio"]
        pf[stock] = pf.get(stock, 0) + amount

        save_coins(coins)

        # notify market engine
        tasks = self.bot.get_cog("BackgroundTasks")
        if tasks:
            tasks.record_trade(stock, "buy", amount)

        await ctx.send(
            f"📈 Bought **{amount}** {stock} shares for **{cost}** coins."
        )

    # -------------------------
    # SELL STOCK
    # -------------------------

    @commands.hybrid_command(
        name="sell",
        description="Sell shares of a stock."
    )
    async def sell(self, ctx, stock: str, amount: int):

        stock = stock.capitalize()

        if stock not in STOCKS:
            return await ctx.send("Unknown stock.")

        if amount <= 0:
            return await ctx.send("Invalid amount.")

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        pf = user["portfolio"]

        owned = pf.get(stock, 0)

        if owned < amount:
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


async def setup(bot):
    await bot.add_cog(Stocks(bot))
