# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# Core
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

# Railway tip:
# If you add a Railway Volume mounted at /data, set DATA_DIR=/data in Railway variables
DATA_DIR = os.getenv("DATA_DIR", "./data")

# =========================
# Aternos (if used elsewhere)
# =========================
AT_USER = os.getenv("ATERNOS_USERNAME")
AT_PASS = os.getenv("ATERNOS_PASSWORD")
ATERNOS_SUBDOMAIN = os.getenv("ATERNOS_SUBDOMAIN")

# =========================
# Guild / Channels / Roles
# =========================
COVER_BOT_ID = 684773505157431347
COVER_INVITE_URL = "https://top.gg/bot/684773505157431347/invite?campaign=210-3"
RESTRICT_GUILD_NAME = "QMUL - Unofficial"

ANNOUNCEMENT_CHANNEL_ID = 1433248053665726547
WELCOME_CHANNEL_ID = 1433248053665726546
MARKET_ANNOUNCE_CHANNEL_ID = 1433412796531347586
SUGGESTION_CHANNEL_ID = 1433413006842396682

TOP_ROLE_NAME = "🌟 EXP Top"

# =========================
# Economy / XP
# =========================
INTEREST_RATE = 0.02
INTEREST_INTERVAL = 3600

DIVIDEND_RATE = 0.01
DIVIDEND_INTERVAL = 86400

XP_PER_MESSAGE = 10

# Zip backup
PACKAGE_USER_ID = 734468552903360594
PACKAGE_FILES = [
    "data.json",
    "coins.json",
    "trivia_stats.json",
    "beg_stats.json",
    "prayer_notif_state.json",
    "ramadan_post_state.json",
    "swear_jar.json",
    "sticker.json",
]

# Shop / items
SHOP_ITEMS = ["Anime body pillow", "Oreo plush", "Rtx5090", "Crash token", "Imran's nose"]
ITEM_PRICES = {
    "Anime body pillow": 30000,
    "Oreo plush": 15000,
    "Rtx5090": 150000,
    "Crash token": 175000,
    "Imran's nose": 999999,
}
CRASH_TOKEN_NAME = "Crash token"

# Stocks
STOCKS = ["Oreobux", "QMkoin", "Seelsterling", "Fwizfinance", "BingBux"]

# Bankrob tuning
ALWAYS_BANKROB_USER_ID = 734468552903360594
BANKROB_STEAL_MIN_PCT = 0.12
BANKROB_STEAL_MAX_PCT = 0.28
BANKROB_MIN_STEAL = 100
BANKROB_MAX_STEAL_PCT_CAP = 0.40

# =========================
# Minecraft (for mc cog)
# =========================
MC_NAME = "QMUL Survival"
MC_ADDRESS = "185.206.150.153"
MC_JAVA_PORT = None  # keep None unless you're 100% sure
MC_MODRINTH_URL = ""
MC_MAP_URL = ""
MC_RULES_URL = ""
MC_DISCORD_URL = "https://discord.gg/6PxXwS7c"
MC_VERSION = "1.20.10"
MC_LOADER = "Fabric"
MC_MODPACK_NAME = "QMUL Survival Pack"
MC_WHITELISTED = False
MC_REGION = "UK / London"
MC_NOTES = [
    "Be respectful — no griefing.",
    "No x-ray / cheating clients.",
    "Ask an admin if you need help.",
]
MC_SHOW_BEDROCK = False
MC_BEDROCK_PORT = 22165
