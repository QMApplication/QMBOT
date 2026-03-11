import random
import discord
from discord.ext import commands, tasks

from storage import (
    load_coins,
    save_coins,
    load_inventory,
    save_inventory,
    load_shop_stock,
    save_shop_stock,
)
from config import SHOP_ITEMS, ITEM_PRICES


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)

SHOP_RESTOCK_MINUTES = 30
SHOP_MAX_STOCK = 10


def ensure_user(coins: dict, user_id: int | str) -> dict:
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0
        }

    return coins[uid]


def ensure_inventory(inv: dict, user_id: int | str) -> dict:
    uid = str(user_id)

    if uid not in inv:
        inv[uid] = {}

    return inv[uid]


def weighted_stock_for_price(price: int, min_price: int, max_price: int) -> int:
    """
    Cheap items restock more often and in higher amounts.
    Expensive items restock less often and in smaller amounts.

    Non-cumulative: each restock computes a fresh stock value.
    """
    if max_price <= min_price:
        return random.randint(1, SHOP_MAX_STOCK)

    # affordability score:
    # cheapest item -> 1.0
    # most expensive item -> 0.0
    score = 1.0 - ((price - min_price) / (max_price - min_price))
    score = max(0.0, min(1.0, score))

    # chance item appears at all
    # cheap items: very likely
    # expensive items: less likely
    appear_chance = 0.15 + (score * 0.85)

    if random.random() > appear_chance:
        return 0

    # max stock based on affordability
    # cheap items can go high, expensive items stay low
    upper = max(1, int(round(1 + score * (SHOP_MAX_STOCK - 1))))

    # bias distribution toward lower numbers for expensive items
    # and higher numbers for cheaper items
    if upper <= 2:
        return random.randint(1, upper)

    roll = random.random()

    if score >= 0.75:
        # cheap items: usually medium-high stock
        if roll < 0.15:
            return random.randint(1, max(1, upper // 3))
        elif roll < 0.50:
            return random.randint(max(1, upper // 3), max(1, (2 * upper) // 3))
        else:
            return random.randint(max(1, (2 * upper) // 3), upper)

    if score >= 0.40:
        # mid-priced items: usually medium or low-medium
        if roll < 0.35:
            return random.randint(1, max(1, upper // 3))
        elif roll < 0.80:
            return random.randint(max(1, upper // 3), max(1, (2 * upper) // 3))
        else:
            return random.randint(max(1, (2 * upper) // 3), upper)

    # expensive items: usually low stock
    if roll < 0.75:
        return random.randint(1, max(1, upper // 2))
    return random.randint(max(1, upper // 2), upper)


def generate_fresh_shop_stock() -> dict:
    prices = [int(ITEM_PRICES[item]) for item in SHOP_ITEMS]
    min_price = min(prices)
    max_price = max(prices)

    stock = {}

    for item in SHOP_ITEMS:
        price = int(ITEM_PRICES[item])
        stock[item] = weighted_stock_for_price(price, min_price, max_price)

    return stock


def ensure_shop_stock(stock: dict) -> dict:
    changed = False

    for item in SHOP_ITEMS:
        if item not in stock:
            changed = True

    for item in list(stock.keys()):
        if item not in SHOP_ITEMS:
            stock.pop(item, None)
            changed = True

    if changed:
        stock = generate_fresh_shop_stock()
        save_shop_stock(stock)

    return stock


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.restock_shop.start()

    def cog_unload(self):
        self.restock_shop.cancel()

    # -------------------------
    # RESTOCK LOOP
    # -------------------------

    @tasks.loop(minutes=SHOP_RESTOCK_MINUTES)
    async def restock_shop(self):
        stock = generate_fresh_shop_stock()
        save_shop_stock(stock)

    @restock_shop.before_loop
    async def before_restock_shop(self):
        await self.bot.wait_until_ready()

    # -------------------------
    # SHOP
    # -------------------------

    @commands.hybrid_command(
        name="shop",
        description="View the shop."
    )
    async def shop(self, ctx: commands.Context):
        stock = load_shop_stock()
        stock = ensure_shop_stock(stock)

        rows = []

        for item in SHOP_ITEMS:
            qty = int(stock.get(item, 0))
            price = int(ITEM_PRICES.get(item, 0))

            item_name = item[:22]
            row = (
                f"{item_name.ljust(22)} | "
                f"{str(qty).rjust(5)} | "
                f"{str(price).rjust(8)}"
            )
            rows.append(row)

        table = (
            "```text\n"
            "Item                   | Stock |    Price\n"
            "------------------------------------------\n"
            f"{chr(10).join(rows)}\n"
            "```"
        )

        embed = discord.Embed(
            title="Shop",
            description=table,
            color=EMBED_COLOR
        )
        embed.set_footer(text="Fresh restock every 30 minutes")

        await ctx.send(embed=embed)

    # -------------------------
    # BUY ITEM
    # -------------------------

    @commands.hybrid_command(
        name="buyitem",
        description="Buy an item from the shop."
    )
    async def buyitem(self, ctx: commands.Context, *, item: str):
        item = item.strip()

        if item not in SHOP_ITEMS:
            return await ctx.send("Item not found.")

        price = int(ITEM_PRICES[item])

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        if int(user["wallet"]) < price:
            return await ctx.send("Not enough coins.")

        stock = load_shop_stock()
        stock = ensure_shop_stock(stock)

        current_stock = int(stock.get(item, 0))
        if current_stock <= 0:
            return await ctx.send("That item is out of stock.")

        inv = load_inventory()
        user_inv = ensure_inventory(inv, ctx.author.id)

        user["wallet"] -= price
        user_inv[item] = int(user_inv.get(item, 0)) + 1
        stock[item] = current_stock - 1

        save_coins(coins)
        save_inventory(inv)
        save_shop_stock(stock)

        embed = discord.Embed(
            title="Purchase Complete",
            description=f"Bought **{item}**.",
            color=EMBED_COLOR
        )
        embed.add_field(name="Cost", value=f"`{price}`", inline=True)
        embed.add_field(name="Stock Left", value=f"`{stock[item]}`", inline=True)
        embed.add_field(name="¢ Wallet", value=f"`{user['wallet']}`", inline=True)

        await ctx.send(embed=embed)

    # -------------------------
    # INVENTORY
    # -------------------------

    @commands.hybrid_command(
        name="inventory",
        description="View your inventory."
    )
    async def inventory(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author

        inv = load_inventory()
        user_inv = ensure_inventory(inv, member.id)

        if not user_inv:
            return await ctx.send("Inventory empty.")

        rows = []

        for item, qty in user_inv.items():
            item_name = str(item)[:24]
            row = f"{item_name.ljust(24)} | {str(qty).rjust(5)}"
            rows.append(row)

        table = (
            "```text\n"
            "Item                     |   Qty\n"
            "--------------------------------\n"
            f"{chr(10).join(rows)}\n"
            "```"
        )

        embed = discord.Embed(
            title=f"{member.display_name} — Inventory",
            description=table,
            color=EMBED_COLOR
        )
        embed.set_footer(text="Stored items")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
