import time
import re
import discord
from discord.ext import commands

from config import XP_PER_MESSAGE, TOP_ROLE_NAME, WELCOME_CHANNEL_ID
from storage import (
    load_data,
    save_data,
    load_swear_jar,
    save_swear_jar,
    load_coins,
    save_coins,
)

# =========================
# AFK
# =========================
AFK_STATUS = {}  # key = f"{guild_id}-{user_id}" -> reason

# =========================
# Swear jar
# =========================
SWEAR_FINE_ENABLED = True
SWEAR_FINE_AMOUNT = 10

SWEAR_WORDS = {
    "fuck", "fucking", "shit", "bullshit", "bitch", "asshole", "bastard",
    "dick", "piss", "crap", "damn", "bloody", "wanker", "twat"
}

SWEAR_RE = re.compile(
    r"\b(" + "|".join(map(re.escape, sorted(SWEAR_WORDS, key=len, reverse=True))) + r")\b",
    re.IGNORECASE
)

SWEAR_COUNT_COOLDOWN = 2
_LAST_SWEAR_COUNT_AT = {}  # user_id -> unix timestamp


# =========================
# Helpers
# =========================
def ensure_user_coins(user_id):
    user_id = str(user_id)
    coins = load_coins()

    if user_id not in coins:
        coins[user_id] = {
            "wallet": 100,
            "bank": 0,
            "last_daily": 0,
            "last_rob": 0,
            "last_beg": 0,
            "last_bankrob": 0,
        }
        save_coins(coins)

    else:
        data = coins[user_id]
        data.setdefault("wallet", 100)
        data.setdefault("bank", 0)
        data.setdefault("last_daily", 0)
        data.setdefault("last_rob", 0)
        data.setdefault("last_beg", 0)
        data.setdefault("last_bankrob", 0)
        save_coins(coins)

    return coins


def calculate_level(xp: int) -> int:
    return int(int(xp) ** 0.5)


def add_swears(user_id: int, count: int):
    if count <= 0:
        return

    jar = load_swear_jar()
    if not isinstance(jar, dict):
        jar = {}

    jar.setdefault("total", 0)
    jar.setdefault("users", {})

    uid = str(user_id)
    jar["total"] = int(jar.get("total", 0)) + count

    jar["users"].setdefault(uid, {})
    jar["users"][uid].setdefault("count", 0)
    jar["users"][uid]["count"] = int(jar["users"][uid]["count"]) + count

    save_swear_jar(jar)


async def update_top_exp_role(guild: discord.Guild):
    data = load_data()
    gid = str(guild.id)

    if gid not in data or not data[gid]:
        return

    top_user_id, _ = max(data[gid].items(), key=lambda x: int(x[1].get("xp", 0)))
    top_member = guild.get_member(int(top_user_id))
    if not top_member:
        return

    role = discord.utils.get(guild.roles, name=TOP_ROLE_NAME)
    if not role:
        try:
            role = await guild.create_role(name=TOP_ROLE_NAME)
        except discord.Forbidden:
            return

    for member in guild.members:
        if role in member.roles and member != top_member:
            try:
                await member.remove_roles(role)
            except Exception:
                pass

    if role not in top_member.roles:
        try:
            await top_member.add_roles(role)
        except Exception:
            pass


async def update_xp(bot: commands.Bot, user_id: int, guild_id: int, xp_amount: int):
    data = load_data()
    gid = str(guild_id)
    uid = str(user_id)

    data.setdefault(gid, {})
    user = data[gid].setdefault(uid, {"xp": 0})

    prev_xp = int(user.get("xp", 0))
    prev_level = int(user.get("level", calculate_level(prev_xp)))

    user["xp"] = prev_xp + int(xp_amount)
    new_level = calculate_level(user["xp"])
    user["level"] = new_level

    save_data(data)

    guild = bot.get_guild(int(gid))
    if not guild:
        return

    # Same milestone announcement logic as original
    if new_level > prev_level and new_level % 5 == 0:
        channel = bot.get_channel(1433417692320239666)
        if channel:
            try:
                user_obj = await bot.fetch_user(user_id)
                await channel.send(f"🎉 **{user_obj.mention}** just reached level **{new_level}**! 🚀")
            except Exception:
                pass

    # Same level-role logic as original
    if new_level > prev_level and new_level % 10 == 0:
        role_name = f"Level {new_level}"
        role = discord.utils.get(guild.roles, name=role_name)

        if not role:
            try:
                role = await guild.create_role(name=role_name)
            except discord.Forbidden:
                role = None

        member = guild.get_member(int(uid))
        if role and member:
            try:
                await member.add_roles(role)
            except Exception:
                pass

    await update_top_exp_role(guild)


class Listeners(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # Welcome
    # -------------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            return

        embed = discord.Embed(
            title=f"Welcome to {member.guild.name} 🎓",
            description=(
                f"{member.mention}, we're glad to have you here!\n\n"
                "Make sure to check out the channels and have fun!"
            ),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    # -------------------------
    # Main message listener
    # -------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # =========================
        # Swear Jar (guild only)
        # =========================
        if message.guild:
            try:
                now_ts = time.time()
                last_ts = _LAST_SWEAR_COUNT_AT.get(message.author.id, 0)

                if now_ts - last_ts >= SWEAR_COUNT_COOLDOWN:
                    matches = SWEAR_RE.findall(message.content or "")
                    swear_count = len(matches)

                    if swear_count > 0:
                        _LAST_SWEAR_COUNT_AT[message.author.id] = now_ts
                        add_swears(message.author.id, swear_count)

                        # Optional fine, same as original behavior
                        if SWEAR_FINE_ENABLED and SWEAR_FINE_AMOUNT > 0:
                            coins = ensure_user_coins(message.author.id)
                            uid = str(message.author.id)

                            fine = SWEAR_FINE_AMOUNT * swear_count
                            wallet = int(coins[uid].get("wallet", 0))
                            taken = min(wallet, fine)
                            coins[uid]["wallet"] = wallet - taken
                            save_coins(coins)

                        jar = load_swear_jar()
                        total = int(jar.get("total", 0))

                        await message.channel.send(
                            f"🫙 {message.author.mention} added **{swear_count}** coin(s) to the swear jar! "
                            f"Server total: **{total}**",
                            delete_after=5
                        )

            except Exception as e:
                print(f"[SwearJar] failed: {type(e).__name__}: {e}")

        # =========================
        # Word filter
        # =========================
        if message.guild and "rigged" in (message.content or "").lower():
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            await message.channel.send(
                f"{message.author.mention} its fair 🔪 ",
                delete_after=5
            )
            return

        # =========================
        # AFK + XP
        # =========================
        if message.guild:
            key = f"{message.guild.id}-{message.author.id}"

            # Remove AFK if user speaks
            if key in AFK_STATUS:
                del AFK_STATUS[key]
                await message.channel.send(embed=discord.Embed(
                    description=f"{message.author.mention} is no longer AFK.",
                    color=discord.Color.red()
                ))

            # Notify if mentioning AFK users
            for user in message.mentions:
                mention_key = f"{message.guild.id}-{user.id}"
                if mention_key in AFK_STATUS:
                    reason = AFK_STATUS[mention_key]
                    await message.channel.send(embed=discord.Embed(
                        description=f"{user.display_name} is currently AFK: {reason}",
                        color=discord.Color.purple()
                    ))

            # XP update
            try:
                await update_xp(self.bot, message.author.id, message.guild.id, XP_PER_MESSAGE)
            except Exception as e:
                print(f"[XP] update_xp failed: {type(e).__name__}: {e}")

    # -------------------------
    # AFK command
    # -------------------------
    @commands.command(name="afk", help="Set your AFK status with a reason")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        if not ctx.guild:
            return await ctx.send("AFK only works in servers.")

        key = f"{ctx.guild.id}-{ctx.author.id}"
        AFK_STATUS[key] = reason

        await ctx.send(embed=discord.Embed(
            description=f"{ctx.author.mention} is now AFK: {reason}",
            color=discord.Color.green()
        ))


async def setup(bot: commands.Bot):
    await bot.add_cog(Listeners(bot))
