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
SHOP_MAX_STOCK = 12
SHOP_RESTOCK_ADD_MIN = 1
SHOP_RESTOCK_ADD_MAX = 4


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


def ensure_shop_stock(stock: dict) -> dict:
    changed = False

    for item in SHOP_ITEMS:
        if item not in stock:
            stock[item] = random.randint(3, 8)
            changed = True

    for item in list(stock.keys()):
        if item not in SHOP_ITEMS:
            stock.pop(item, None)
            changed = True

    if changed:
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
        stock = load_shop_stock()
        stock = ensure_shop_stock(stock)

        changed = False

        for item in SHOP_ITEMS:
            current = int(stock.get(item, 0))
            add_amount = random.randint(SHOP_RESTOCK_ADD_MIN, SHOP_RESTOCK_ADD_MAX)
            new_amount = min(SHOP_MAX_STOCK, current + add_amount)

            if new_amount != current:
                stock[item] = new_amount
                changed = True

        if changed:
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
