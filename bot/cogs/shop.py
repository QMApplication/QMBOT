import discord
from discord.ext import commands

from storage import load_coins, save_coins, load_inventory, save_inventory
from config import SHOP_ITEMS, ITEM_PRICES


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


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


class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # SHOP
    # -------------------------

    @commands.hybrid_command(
        name="shop",
        description="View the shop."
    )
    async def shop(self, ctx: commands.Context):
        lines = []

        for item in SHOP_ITEMS:
            price = ITEM_PRICES.get(item, 0)
            lines.append(f"• **{item}**  |  `{price}`")

        embed = discord.Embed(
            title="Shop",
            description="\n".join(lines) if lines else "No items available.",
            color=EMBED_COLOR
        )
        embed.set_footer(text="Item prices")

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

        price = ITEM_PRICES[item]

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        if user["wallet"] < price:
            return await ctx.send("Not enough coins.")

        inv = load_inventory()
        user_inv = ensure_inventory(inv, ctx.author.id)

        user["wallet"] -= price
        user_inv[item] = user_inv.get(item, 0) + 1

        save_coins(coins)
        save_inventory(inv)

        embed = discord.Embed(
            title="Purchase Complete",
            description=f"Bought **{item}**.",
            color=EMBED_COLOR
        )
        embed.add_field(name="Cost", value=f"`{price}`", inline=True)
        embed.add_field(name="Wallet", value=f"`{user['wallet']}`", inline=True)

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

        lines = []

        for item, qty in user_inv.items():
            lines.append(f"• **{item}**  |  x{qty}")

        embed = discord.Embed(
            title=f"{member.display_name} — Inventory",
            description="\n".join(lines),
            color=EMBED_COLOR
        )
        embed.set_footer(text="Stored items")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
