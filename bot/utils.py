# utils.py
import os
import io
import zipfile
import re
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

# -------------------------
# Mentions: enforce exactly one mention
# -------------------------
def only_mention_target(ctx: commands.Context) -> Optional[int]:
    """
    Returns the user_id if exactly one user is mentioned, else None.
    Works even if command signature includes an optional member param.
    """
    if not ctx.message.mentions or len(ctx.message.mentions) != 1:
        return None
    return ctx.message.mentions[0].id

async def get_member_safe(guild: discord.Guild, user_id: int):
    m = guild.get_member(user_id)
    if m:
        return m
    try:
        return await guild.fetch_member(user_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None

# -------------------------
# Time helpers
# -------------------------
def utc_day_key(dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d")

def fmt_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")

# -------------------------
# Zip backup helpers (Railway-safe)
# -------------------------
def existing_files(paths: list[str]) -> list[str]:
    return [p for p in paths if p and os.path.exists(p) and os.path.isfile(p)]

def build_zip_bytes(file_paths: list[str], folder_name: str = "bot_backup") -> tuple[io.BytesIO, list[str]]:
    included = existing_files(file_paths)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in included:
            arcname = f"{folder_name}/{os.path.basename(path)}"
            z.write(path, arcname=arcname)
    buf.seek(0)
    return buf, included

# -------------------------
# Swear regex helper (optional: you can keep this in a shared_state module later)
# -------------------------
def compile_whole_word_regex(words: set[str]) -> re.Pattern:
    return re.compile(
        r"\b(" + "|".join(map(re.escape, sorted(words, key=len, reverse=True))) + r")\b",
        re.IGNORECASE
    )
