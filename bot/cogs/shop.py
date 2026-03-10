import discord
from discord.ext import commands

from storage import load_coins, save_coins, load_inventory, save_inventory
from config import SHOP_ITEMS, ITEM_PRICES


def ensure_user(user_id):
    coins = load_coins()
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0
        }
        save_coins(coins)

    return coins


def ensure_inventory(user_id):
    inv = load_inventory()
    uid = str(user_id)

    if uid not in inv:
        inv[uid] = {}
        save_inventory(inv)

    return inv


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # SHOP
    # -------------------------

    @commands.command()
    async def shop(self, ctx):

        desc = ""

        for item in SHOP_ITEMS:

            price = ITEM_PRICES.get(item, 0)

            desc += f"**{item}** — {price} coins\n"

        embed = discord.Embed(
            title="🛒 Shop",
            description=desc,
            color=discord.Color.green()
        )

        await ctx.send(embed=embed)

    # -------------------------
    # BUY ITEM
    # -------------------------

    @commands.command()
    async def buyitem(self, ctx, *, item: str):

        item = item.strip()

        if item not in SHOP_ITEMS:
            return await ctx.send("Item not found.")

        price = ITEM_PRICES[item]

        coins = ensure_user(ctx.author.id)
        user = coins[str(ctx.author.id)]

        if user["wallet"] < price:
            return await ctx.send("Not enough coins.")

        inv = ensure_inventory(ctx.author.id)

        user["wallet"] -= price

        inv[str(ctx.author.id)][item] = inv[str(ctx.author.id)].get(item, 0) + 1

        save_coins(coins)
        save_inventory(inv)

        await ctx.send(f"🛒 Bought **{item}**.")

    # -------------------------
    # INVENTORY
    # -------------------------

    @commands.command()
    async def inventory(self, ctx, member: discord.Member = None):

        member = member or ctx.author

        inv = ensure_inventory(member.id)

        user_inv = inv[str(member.id)]

        if not user_inv:
            return await ctx.send("Inventory empty.")

        desc = ""

        for item, qty in user_inv.items():

            desc += f"{item} x{qty}\n"

        embed = discord.Embed(
            title=f"{member.display_name}'s Inventory",
            description=desc,
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Shop(bot))
