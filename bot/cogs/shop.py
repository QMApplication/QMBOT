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


EMBED_COLOR = discord.Color.from_rgb(68, 34, 102)

SHOP_RESTOCK_MINUTES = 30


MAX_STOCK = {
    "Anime body pillow": 10,
    "Oreo plush": 10,
    "Rtx5090": 8,
    "Crash token": 3,
}


def make_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR
    )


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


def generate_shop_stock() -> dict:

    prices = [ITEM_PRICES[i] for i in SHOP_ITEMS]

    min_price = min(prices)
    max_price = max(prices)

    stock = {}

    for item in SHOP_ITEMS:

        price = ITEM_PRICES[item]

        score = 1 - ((price - min_price) / (max_price - min_price))
        score = max(0, min(1, score))

        max_item_stock = MAX_STOCK.get(item, 5)

        appear_chance = 0.15 + (score * 0.85)

        if random.random() > appear_chance:
            stock[item] = 0
            continue

        upper = max(1, int(round(1 + score * (max_item_stock - 1))))
        stock[item] = random.randint(1, upper)

    return stock


def ensure_shop_stock(stock: dict) -> dict:

    changed = False

    for item in SHOP_ITEMS:
        if item not in stock:
            changed = True

    for item in list(stock.keys()):
        if item not in SHOP_ITEMS:
            stock.pop(item)
            changed = True

    if changed:
        stock = generate_shop_stock()
        save_shop_stock(stock)

    return stock


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.restock.start()

    def cog_unload(self):
        self.restock.cancel()

    # -------------------------
    # RESTOCK LOOP
    # -------------------------

    @tasks.loop(minutes=SHOP_RESTOCK_MINUTES)
    async def restock(self):

        new_stock = generate_shop_stock()
        save_shop_stock(new_stock)

    @restock.before_loop
    async def before_restock(self):
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

        ordered_items = sorted(SHOP_ITEMS, key=lambda x: ITEM_PRICES[x])

        rows = []

        for item in ordered_items:

            price = ITEM_PRICES[item]
            qty = stock.get(item, 0)

            row = (
                f"{item[:16].ljust(16)} | "
                f"{str(qty).rjust(3)} | "
                f"{str(price).rjust(6)}"
            )

            rows.append(row)

        table = (
            "```text\n"
            "Item            |Qty |Price\n"
            "---------------------------\n"
            f"{chr(10).join(rows)}\n"
            "```"
        )

        embed = discord.Embed(
            title="Shop",
            description=table,
            color=EMBED_COLOR
        )

        embed.set_footer(text="Restocks every 30 minutes")

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
            return await ctx.send(embed=make_embed("Shop", "Item not found."))

        price = ITEM_PRICES[item]

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        if user["wallet"] < price:
            return await ctx.send(embed=make_embed("Shop", "Not enough coins."))

        stock = load_shop_stock()
        stock = ensure_shop_stock(stock)

        current_stock = stock.get(item, 0)

        if current_stock <= 0:
            return await ctx.send(embed=make_embed("Shop", "That item is out of stock."))

        inv = load_inventory()
        user_inv = ensure_inventory(inv, ctx.author.id)

        user["wallet"] -= price
        user_inv[item] = user_inv.get(item, 0) + 1
        stock[item] = current_stock - 1

        save_coins(coins)
        save_inventory(inv)
        save_shop_stock(stock)

        embed = discord.Embed(
            title="Purchase Complete",
            description=f"Bought **{item}**",
            color=EMBED_COLOR
        )

        embed.add_field(name="Cost", value=f"`{price}`")
        embed.add_field(name="Stock Left", value=f"`{stock[item]}`")
        embed.add_field(name="¢ Wallet", value=f"`{user['wallet']}`")

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
            return await ctx.send(embed=make_embed("Inventory", "Inventory empty."))

        rows = []

        for item, qty in user_inv.items():

            row = (
                f"{item[:16].ljust(16)} | "
                f"{str(qty).rjust(3)}"
            )

            rows.append(row)

        table = (
            "```text\n"
            "Item            |Qty\n"
            "--------------------\n"
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


async def setup(bot):
    await bot.add_cog(Shop(bot))
