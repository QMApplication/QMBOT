# bot/storage.py
import json, os
from typing import Any

DATA_FILE = "data.json"
COOLDOWN_FILE = "cooldowns.json"
COIN_DATA_FILE = "coins.json"
SHOP_FILE = "shop_stock.json"
INVENTORY_FILE = "inventories.json"
MARRIAGE_FILE = "marriages.json"
QUEST_FILE = "quests.json"
EVENT_FILE = "events.json"
STOCK_FILE = "stocks.json"
SUGGESTION_FILE = "suggestions.json"
TRIVIA_STATS_FILE = "trivia_stats.json"
TRIVIA_STREAKS_FILE = "trivia_streaks.json"
BEG_STATS_FILE = "beg_stats.json"
SWEAR_JAR_FILE = "swear_jar.json"
STICKER_FILE = "sticker.json"

def _load_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default

def _save_json(path: str, obj: Any):
    with open(path, "w") as f:
        json.dump(obj, f, indent=4)

# Thin wrappers (keep names matching your current code)
def load_data(): return _load_json(DATA_FILE, {})
def save_data(d): _save_json(DATA_FILE, d)

def load_coins(): return _load_json(COIN_DATA_FILE, {})
def save_coins(d): _save_json(COIN_DATA_FILE, d)

def load_shop_stock(): return _load_json(SHOP_FILE, {})
def save_shop_stock(d): _save_json(SHOP_FILE, d)

def load_inventory(): return _load_json(INVENTORY_FILE, {})
def save_inventory(d): _save_json(INVENTORY_FILE, d)

def load_marriages(): return _load_json(MARRIAGE_FILE, {})
def save_marriages(d): _save_json(MARRIAGE_FILE, d)

def load_quests(): return _load_json(QUEST_FILE, {})
def save_quests(d): _save_json(QUEST_FILE, d)

def load_event(): return _load_json(EVENT_FILE, {})
def save_event(d): _save_json(EVENT_FILE, d)

def load_stocks(): return _load_json(STOCK_FILE, {})
def save_stocks(d): _save_json(STOCK_FILE, d)

def load_suggestions(): return _load_json(SUGGESTION_FILE, [])
def save_suggestions(d): _save_json(SUGGESTION_FILE, d)

def load_trivia_stats(): return _load_json(TRIVIA_STATS_FILE, {})
def save_trivia_stats(d): _save_json(TRIVIA_STATS_FILE, d)

def load_trivia_streaks(): return _load_json(TRIVIA_STREAKS_FILE, {})
def save_trivia_streaks(d): _save_json(TRIVIA_STREAKS_FILE, d)

def load_beg_stats(): return _load_json(BEG_STATS_FILE, {})
def save_beg_stats(d): _save_json(BEG_STATS_FILE, d)

def load_swear_jar(): return _load_json(SWEAR_JAR_FILE, {"total": 0, "users": {}})
def save_swear_jar(d): _save_json(SWEAR_JAR_FILE, d)

def load_stickers(): return _load_json(STICKER_FILE, {"total": 0, "users": {}, "daily": {}})
def save_stickers(d): _save_json(STICKER_FILE, d)
