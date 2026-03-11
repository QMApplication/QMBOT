import io

import discord
import matplotlib.pyplot as plt
import numpy as np
from discord.ext import commands

from storage import load_coins, save_coins, load_stocks
from config import STOCKS


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


def make_embed(title: str, description: str):
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

        lines = []
        for name in STOCKS:
            price = int(stocks.get(name, {}).get("price", 0))
            lines.append(f"• **{name}**  `{price}`")

        embed = discord.Embed(
            title="Market",
            description="\n".join(lines),
            color=EMBED_COLOR
        )
        embed.set_footer(text="Live prices")

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
            return await ctx.send(embed=make_embed("Market", "Unknown stock."))

        stock_name = stock_names[key]

        stocks = load_stocks()
        data = stocks.get(stock_name)

        if not data:
            return await ctx.send(embed=make_embed("Market", "Unknown stock."))

        price = int(data.get("price", 0))
        history = data.get("history", []) or []

        change = 0
        if len(history) > 1:
            change = price - int(history[-2])

        if len(history) < 2:
            embed = discord.Embed(
                title=stock_name,
                color=EMBED_COLOR
            )
            embed.add_field(name="Price", value=f"`{price}`", inline=True)
            embed.add_field(name="Change", value=f"`{change:+}`", inline=True)
            embed.add_field(name="Chart", value="Not enough history yet.", inline=False)
            await ctx.send(embed=embed)
            return

        x = np.arange(len(history))
        y = np.array(history, dtype=float)

        fig, ax = plt.subplots(figsize=(9, 4.8), dpi=150)
        fig.patch.set_facecolor("#0d1117")
        ax.set_facecolor("#0d1117")

        ax.plot(
            x,
            y,
            color="#4a90e2",
            linewidth=2.0,
            solid_capstyle="round"
        )

        ax.fill_between(x, y, y.min(), color="#4a90e2", alpha=0.08)

        ax.grid(
            True,
            which="major",
            linestyle="-",
            linewidth=0.35,
            alpha=0.12,
            color="#ffffff"
        )

        for spine in ax.spines.values():
            spine.set_color("#3a4250")
            spine.set_linewidth(0.8)

        ax.tick_params(axis="x", colors="#aeb6c2", labelsize=8)
        ax.tick_params(axis="y", colors="#aeb6c2", labelsize=8)

        ax.set_title(f"{stock_name}  |  Price History", color="#e6edf3", fontsize=13, pad=10)
        ax.set_xlabel("Updates", color="#aeb6c2", fontsize=9, labelpad=8)
        ax.set_ylabel("Price", color="#aeb6c2", fontsize=9, labelpad=8)

        ymin = float(y.min())
        ymax = float(y.max())
        pad = max(2.0, (ymax - ymin) * 0.10 if ymax > ymin else ymax * 0.06 + 2)
        ax.set_ylim(max(0, ymin - pad), ymax + pad)

        ax.scatter([x[-1]], [y[-1]], color="#4a90e2", s=18, zorder=3)

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(
            buf,
            format="png",
            facecolor=fig.get_facecolor(),
            bbox_inches="tight"
        )
        plt.close(fig)
        buf.seek(0)

        file = discord.File(buf, filename="stock.png")

        sign = "+" if change > 0 else ""
        embed = discord.Embed(
            title=stock_name,
            description="Market View & Volatility",
            color=EMBED_COLOR
        )
        embed.add_field(name="Price", value=f"`{price}`", inline=True)
        embed.add_field(name="Change", value=f"`{sign}{change}`", inline=True)
        embed.add_field(name="History", value=f"`{len(history)} points`", inline=True)
        embed.set_image(url="attachment://stock.png")
        embed.set_footer(text="Stored market history")

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

        lines = []
        total = 0

        for s in STOCKS:
            qty = int(pf.get(s, 0))
            if qty > 0:
                price = int(stocks.get(s, {}).get("price", 0))
                value = qty * price
                total += value
                lines.append(f"• **{s}**  {qty} shares  |  `{value}`")

        if not lines:
            lines = ["No stocks."]

        embed = discord.Embed(
            title=f"{member.display_name} — Portfolio",
            description="\n".join(lines),
            color=EMBED_COLOR
        )
        embed.add_field(name="Total Value", value=f"`{total}`", inline=False)

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
            return await ctx.send(embed=make_embed("Market", "Unknown stock."))

        if amount <= 0:
            return await ctx.send(embed=make_embed("Market", "Invalid amount."))

        stock_name = stock_names[key]

        stocks = load_stocks()
        price = int(stocks.get(stock_name, {}).get("price", 0))
        cost = price * amount

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        if user["wallet"] < cost:
            return await ctx.send(embed=make_embed("Market", "Not enough coins."))

        user["wallet"] -= cost

        pf = user["portfolio"]
        pf[stock_name] = int(pf.get(stock_name, 0)) + amount

        save_coins(coins)

        tasks = self.bot.get_cog("BackgroundTasks")
        if tasks:
            tasks.record_trade(stock_name, "buy", amount)

        embed = discord.Embed(
            title="Order Filled",
            description=f"Bought **{amount}** shares of **{stock_name}**.",
            color=EMBED_COLOR
        )
        embed.add_field(name="Cost", value=f"`{cost}`", inline=True)
        embed.add_field(name="Price", value=f"`{price}` each", inline=True)

        await ctx.send(embed=embed)

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
            return await ctx.send(embed=make_embed("Market", "Unknown stock."))

        if amount <= 0:
            return await ctx.send(embed=make_embed("Market", "Invalid amount."))

        stock_name = stock_names[key]

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        pf = user["portfolio"]
        owned = int(pf.get(stock_name, 0))

        if owned < amount:
            return await ctx.send(embed=make_embed("Market", "Not enough shares."))

        stocks = load_stocks()
        price = int(stocks.get(stock_name, {}).get("price", 0))
        revenue = price * amount

        pf[stock_name] = owned - amount
        user["wallet"] += revenue

        save_coins(coins)

        tasks = self.bot.get_cog("BackgroundTasks")
        if tasks:
            tasks.record_trade(stock_name, "sell", amount)

        embed = discord.Embed(
            title="Order Filled",
            description=f"Sold **{amount}** shares of **{stock_name}**.",
            color=EMBED_COLOR
        )
        embed.add_field(name="Revenue", value=f"`{revenue}`", inline=True)
        embed.add_field(name="Price", value=f"`{price}` each", inline=True)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Stocks(bot))
