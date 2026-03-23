"""
extras.py — Jam-packed extras cog

Commands:
  Fun / Games
    /tictactoe     - 2-player TicTacToe
    /hangman       - Classic hangman game
    /scramble      - Unscramble a word
    /numguess      - Number guessing with live hints
    /truthordare   - Truth or Dare picker with buttons
    /typerace      - Speed typing challenge
    /rhyme         - Rhyme a word (API)
    /define        - Dictionary definition
    /urban         - Urban Dictionary lookup
    /wikipedia     - Wikipedia summary
    /translate     - Translate text (LibreTranslate)
    /weather       - Current weather for any city
    /crypto        - Crypto price lookup
    /meme          - Random meme from Reddit
    /dog           - Random dog image
    /cat           - Random cat image
    /fox           - Random fox image
    /duck          - Random duck image
    /coinflipcount - How many flips to get N heads
    /passwordgen   - Generate a strong random password
    /dice_stats    - Probability stats for a dice expression

  Social
    /cuddle        - Cuddle someone (GIF)
    /poke          - Poke someone (GIF)
    /slap          - Slap someone (GIF)
    /bite          - Bite someone (GIF)
    /kick_person   - Kick (the action, not moderation) (GIF)
    /wave          - Wave at someone (GIF)
    /highfive      - High five someone (GIF)
    /cry           - Post a crying GIF
    /laugh         - Post a laughing GIF
    /dance         - Post a dancing GIF
    /smug          - Smug face GIF
    /blush         - Blush GIF
    /facepalm      - Facepalm GIF
    /sleep         - Sleep GIF

  Economy extras
    /gamblestreak  - Check your gambling win streak
    /richcheck     - How close to broke are you
    /moneycount    - Combined server total coins in circulation
    /transfer      - Move coins between wallet and bank for another user (admin)
    /giveaway      - Start a coin giveaway in channel

  Misc utility
    /timer         - Set a countdown timer that pings you
    /remindme      - Remind you of something in X minutes
    /math          - Evaluate a maths expression safely
    /base64enc     - Base64 encode
    /base64dec     - Base64 decode
    /hash          - Hash text with MD5/SHA256
    /color         - Preview a hex colour
    /length        - String length
    /charinfo      - Info about a Unicode character
    /snowflake     - Decode a Discord Snowflake ID
    /avatar        - Show a user's full avatar
    /serverinfo    - Server stats card
    /userinfo      - User info card
    /botinfo       - Bot stats
    /uptime        - Bot uptime
    /ping          - Latency check
    /randomuser    - Pick a random server member
    /randomchannel - Pick a random channel
"""

import asyncio
import base64
import hashlib
import math
import operator
import os
import random
import re
import string
import time
import unicodedata
from datetime import datetime, timezone

import aiohttp
import discord
from discord.ext import commands

from ui_utils import C, E, embed, error, warn, success

TENOR_API_KEY = "AIzaSyAyimkuEcdEnPs55ueys84EMt_lFe0BXKQ"
TENOR_BASE    = "https://tenor.googleapis.com/v2/search"

BOT_START_TIME = time.time()

# ── Wordlist for scramble / hangman ───────────────────────────────────────────
WORD_LIST = [
    "python", "discord", "server", "channel", "keyboard", "monitor",
    "elephant", "rainbow", "football", "library", "blanket", "jupiter",
    "triangle", "volcano", "symphony", "paradox", "quantum", "lantern",
    "crumpet", "biscuit", "penguin", "dolphin", "mystery", "cabinet",
    "whisper", "freckle", "gazelle", "horizon", "journey", "kingdom",
    "lantern", "meadow",  "narwhal", "origami", "platoon", "quarrel",
    "rampage", "satchel", "tangerine", "ukulele", "vanilla", "weasel",
    "xylophone", "yardstick", "zeppelin",
]

HANGMAN_STAGES = [
    "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```",
]

TRUTH_QUESTIONS = [
    "What's the most embarrassing thing you've done in public?",
    "What's your most irrational fear?",
    "Have you ever ghosted someone? Who?",
    "What's the worst lie you've ever told and got away with?",
    "Who in this server do you have a crush on?",
    "What's something you've done that you've never told anyone?",
    "What's the pettiest thing you've ever done to get revenge?",
    "Have you ever been banned from anything? What?",
    "What's the most money you've ever wasted on something stupid?",
    "What's your most embarrassing childhood memory?",
    "What do you secretly judge people for?",
    "Have you ever cheated in a game or exam?",
    "What's the weirdest dream you've ever had?",
    "What's your most controversial food opinion?",
    "Have you ever faked being sick to avoid something?",
]

DARE_LIST = [
    "Send a voice message of you doing your best animal impression.",
    "Change your nickname to 'I Love [last person you messaged]' for 30 minutes.",
    "Post your camera roll photo from exactly 6 months ago.",
    "Send the most cursed meme you have saved.",
    "Type your next 3 messages with your eyes closed.",
    "Post a 10-second voice memo of you singing happy birthday.",
    "Tag someone random and say something genuinely kind about them.",
    "Send your screen time from this week.",
    "React to the last 5 messages in the server with random emoji.",
    "Write a 3-line poem about the person above you.",
    "DM someone 'I think we need to talk' and wait 2 minutes before saying it's a dare.",
    "Post your Spotify Wrapped or top-played song.",
]

SAFE_MATH_OPS = {
    "+": operator.add, "-": operator.sub,
    "*": operator.mul, "/": operator.truediv,
    "**": operator.pow, "%": operator.mod,
    "//": operator.floordiv,
}

TYPING_SENTENCES = [
    "The quick brown fox jumps over the lazy dog",
    "Pack my box with five dozen liquor jugs",
    "How vexingly quick daft zebras jump",
    "The five boxing wizards jump quickly",
    "Sphinx of black quartz judge my vow",
    "Crazy Fredrick bought many very exquisite opal jewels",
    "We promptly judged antique ivory buckles for the next prize",
    "A mad boxer shot a quick gloved jab to the jaw of his dizzy opponent",
    "Sixty zippers were quickly picked from the woven jute bag",
    "Back in my quaint garden jaunty zinnias vie with flaunting phlox",
]

# active games  uid -> state
_hangman_games:  dict[str, dict] = {}
_scramble_games: dict[str, dict] = {}
_typerace_games: dict[str, dict] = {}
_reminders:      list[dict]      = []


# ── Helpers ───────────────────────────────────────────────────────────────────

async def fetch_gif(query: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                TENOR_BASE,
                params={"q": query, "key": TENOR_API_KEY, "limit": 20,
                        "media_filter": "gif", "contentfilter": "medium"},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as r:
                if r.status != 200:
                    return None
                data    = await r.json()
                results = data.get("results", [])
                if not results:
                    return None
                chosen = random.choice(results[:10])
                media  = chosen.get("media_formats", {})
                gif    = media.get("gif") or media.get("mediumgif") or media.get("tinygif") or {}
                return gif.get("url")
    except Exception:
        return None


async def fetch_json(url: str, **params) -> dict | None:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, timeout=aiohttp.ClientTimeout(total=6)) as r:
                if r.status != 200:
                    return None
                return await r.json()
    except Exception:
        return None


def _safe_eval(expr: str) -> float | str:
    """Evaluate a basic maths expression safely."""
    expr = expr.strip().replace("^", "**")
    # whitelist: digits, operators, parens, spaces, dot
    if not re.fullmatch(r"[\d\s\+\-\*\/\(\)\.\%\^]+", expr):
        return "Invalid expression — only numbers and operators allowed."
    try:
        result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
        return result
    except ZeroDivisionError:
        return "Cannot divide by zero."
    except Exception:
        return "Could not evaluate that expression."


def _human_uptime(seconds: float) -> str:
    s = int(seconds)
    d = s // 86400; s %= 86400
    h = s // 3600;  s %= 3600
    m = s // 60;    s %= 60
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)


def _gif_action(author: discord.Member, target: discord.Member | None,
                title: str, text: str, color=C.SOCIAL) -> discord.Embed:
    e = embed(title, text, color,
              footer=f"{author.display_name}{' → ' + target.display_name if target else ''}")
    return e


# ── TicTacToe ─────────────────────────────────────────────────────────────────

class TTTView(discord.ui.View):
    EMPTY = "⬜"; X = "❌"; O = "⭕"

    def __init__(self, p1: discord.Member, p2: discord.Member):
        super().__init__(timeout=120)
        self.players  = {p1.id: self.X, p2.id: self.O}
        self.p1       = p1
        self.p2       = p2
        self.turn     = p1.id
        self.board    = [self.EMPTY] * 9
        self.message  = None
        for i in range(9):
            btn          = discord.ui.Button(label="⬜", style=discord.ButtonStyle.secondary, row=i // 3)
            btn.callback = self._make_cb(i)
            self.add_item(btn)

    def _make_cb(self, idx: int):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id not in self.players:
                return await interaction.response.send_message(embed=error("TicTacToe", "You're not in this game."), ephemeral=True)
            if interaction.user.id != self.turn:
                return await interaction.response.send_message(embed=error("TicTacToe", "It's not your turn!"), ephemeral=True)
            if self.board[idx] != self.EMPTY:
                return await interaction.response.send_message(embed=error("TicTacToe", "That square is taken."), ephemeral=True)
            mark = self.players[self.turn]
            self.board[idx] = mark
            self.children[idx].label = mark
            self.children[idx].style = discord.ButtonStyle.danger if mark == self.X else discord.ButtonStyle.primary
            self.children[idx].disabled = True
            winner = self._check_winner()
            if winner:
                for c in self.children: c.disabled = True
                who = self.p1 if self.turn == self.p1.id else self.p2
                e = success(f"TicTacToe — {who.display_name} Wins! 🎉",
                            self._board_str())
                return await interaction.response.edit_message(embed=e, view=self)
            if self.EMPTY not in self.board:
                for c in self.children: c.disabled = True
                e = embed("TicTacToe — Draw! 🤝", self._board_str(), C.NEUTRAL)
                return await interaction.response.edit_message(embed=e, view=self)
            self.turn = self.p2.id if self.turn == self.p1.id else self.p1.id
            nxt = self.p1 if self.turn == self.p1.id else self.p2
            e = embed("TicTacToe", f"{self._board_str()}\n\n{nxt.mention}'s turn ({self.players[self.turn]})", C.GAMES)
            await interaction.response.edit_message(embed=e, view=self)
        return cb

    def _board_str(self) -> str:
        rows = [" ".join(self.board[i:i+3]) for i in range(0, 9, 3)]
        return "\n".join(rows)

    def _check_winner(self) -> bool:
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a,b,c in wins:
            if self.board[a] == self.board[b] == self.board[c] != self.EMPTY:
                return True
        return False

    async def on_timeout(self):
        for c in self.children: c.disabled = True
        if self.message:
            await self.message.edit(embed=warn("TicTacToe", "Game timed out."), view=self)


# ── Truth or Dare View ────────────────────────────────────────────────────────

class TruthOrDareView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=error("T or D", "Not your game."), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🙋 Truth", style=discord.ButtonStyle.primary)
    async def truth(self, interaction, button):
        for c in self.children: c.disabled = True
        q = random.choice(TRUTH_QUESTIONS)
        e = embed("🙋  Truth", f"> {q}", C.TRIVIA)
        await interaction.response.edit_message(embed=e, view=self)
        self.stop()

    @discord.ui.button(label="😈 Dare", style=discord.ButtonStyle.danger)
    async def dare(self, interaction, button):
        for c in self.children: c.disabled = True
        d = random.choice(DARE_LIST)
        e = embed("😈  Dare", f"> {d}", C.SOCIAL)
        await interaction.response.edit_message(embed=e, view=self)
        self.stop()


# ── Giveaway View ─────────────────────────────────────────────────────────────

class GiveawayView(discord.ui.View):
    def __init__(self, amount: int, duration: int, host_id: int):
        super().__init__(timeout=duration)
        self.amount   = amount
        self.host_id  = host_id
        self.entrants: set[int] = set()
        self.message  = None

    @discord.ui.button(label="🎉  Enter Giveaway", style=discord.ButtonStyle.success)
    async def enter(self, interaction, button):
        uid = interaction.user.id
        if uid == self.host_id:
            return await interaction.response.send_message(embed=warn("Giveaway", "You can't enter your own giveaway."), ephemeral=True)
        if uid in self.entrants:
            self.entrants.discard(uid)
            await interaction.response.send_message(embed=warn("Giveaway", "You left the giveaway."), ephemeral=True)
        else:
            self.entrants.add(uid)
            await interaction.response.send_message(embed=success("Entered!", f"You're in! {len(self.entrants)} entrant(s) so far."), ephemeral=True)
        if self.message:
            await self.message.edit(embed=self._build_embed(), view=self)

    def _build_embed(self) -> discord.Embed:
        return embed(
            "🎉  Giveaway!",
            f"Prize: **{self.amount:,}** {E.COIN} coins\n\n"
            f"Click the button to enter!\n"
            f"**{len(self.entrants)}** entrant(s) so far.",
            C.TRIVIA,
            footer="Click again to leave · Winner drawn when timer ends",
        )

    async def on_timeout(self):
        for c in self.children: c.disabled = True
        if not self.entrants:
            result = embed("🎉  Giveaway Ended", "No one entered. Sad.", C.NEUTRAL)
        else:
            winner_id = random.choice(list(self.entrants))
            from storage import load_coins, save_coins
            coins = load_coins()
            uid   = str(winner_id)
            coins.setdefault(uid, {"wallet": 100, "bank": 0})
            coins[uid]["wallet"] = int(coins[uid].get("wallet", 0)) + self.amount
            save_coins(coins)
            result = embed(
                "🎉  Giveaway Winner!",
                f"<@{winner_id}> won **{self.amount:,}** {E.COIN} coins!\n\n"
                f"{len(self.entrants)} entered.",
                C.WIN,
            )
        if self.message:
            await self.message.edit(embed=result, view=self)


# ── Cog ───────────────────────────────────────────────────────────────────────

class Extras(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ══ GAMES ════════════════════════════════════════════════════════════════

    @commands.hybrid_command(name="tictactoe", description="Play TicTacToe against another user.")
    async def tictactoe(self, ctx, opponent: discord.Member):
        if opponent == ctx.author:
            return await ctx.send(embed=error("TicTacToe", "You can't play yourself."))
        if opponent.bot:
            return await ctx.send(embed=error("TicTacToe", "Bots are terrible at TicTacToe."))
        view    = TTTView(ctx.author, opponent)
        e       = embed("TicTacToe ❌⭕",
                        f"{view._board_str()}\n\n{ctx.author.mention}'s turn (❌)",
                        C.GAMES,
                        footer=f"{ctx.author.display_name} vs {opponent.display_name}")
        msg     = await ctx.send(embed=e, view=view)
        view.message = msg

    @commands.hybrid_command(name="hangman", description="Play hangman (solo).")
    async def hangman(self, ctx):
        uid  = str(ctx.author.id)
        if uid in _hangman_games:
            return await ctx.send(embed=warn("Hangman", "You already have a game running. Guess a letter with `/guess <letter>`."))
        word = random.choice(WORD_LIST)
        _hangman_games[uid] = {"word": word, "guessed": set(), "wrong": 0}
        display = " ".join("_" if c not in set() else c for c in word)
        e = embed("🪓  Hangman",
                  f"{HANGMAN_STAGES[0]}\n\n**Word:** `{display}`\n\nGuess a letter with `/guess <letter>`",
                  C.GAMES, footer=f"6 wrong guesses allowed · Word: {len(word)} letters")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="guess", description="Guess a letter in your hangman game.")
    async def guess(self, ctx, letter: str):
        uid   = str(ctx.author.id)
        if uid not in _hangman_games:
            return await ctx.send(embed=warn("Hangman", "No active game. Start one with `/hangman`."))
        letter = letter.lower().strip()
        if len(letter) != 1 or not letter.isalpha():
            return await ctx.send(embed=error("Hangman", "One letter at a time please."))
        game   = _hangman_games[uid]
        word   = game["word"]
        guessed= game["guessed"]
        if letter in guessed:
            return await ctx.send(embed=warn("Hangman", f"You already guessed `{letter}`."))
        guessed.add(letter)
        if letter not in word:
            game["wrong"] += 1
        display = " ".join(c if c in guessed else "_" for c in word)
        wrong   = game["wrong"]
        if wrong >= 6:
            _hangman_games.pop(uid)
            e = embed("💀  You Died!",
                      f"{HANGMAN_STAGES[6]}\n\nThe word was **{word}**.", C.LOSE)
            return await ctx.send(embed=e)
        if "_" not in display:
            _hangman_games.pop(uid)
            e = success("Hangman — You Won! 🎉", f"The word was **{word}**!")
            return await ctx.send(embed=e)
        guessed_str = " ".join(sorted(guessed))
        e = embed("🪓  Hangman",
                  f"{HANGMAN_STAGES[wrong]}\n\n**Word:** `{display}`\n"
                  f"**Guessed:** {guessed_str or 'none yet'}\n"
                  f"**Wrong:** {wrong}/6",
                  C.GAMES)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="hangmanstop", description="Give up on your current hangman game.")
    async def hangmanstop(self, ctx):
        uid = str(ctx.author.id)
        if uid not in _hangman_games:
            return await ctx.send(embed=warn("Hangman", "No active game."))
        word = _hangman_games.pop(uid)["word"]
        await ctx.send(embed=embed("🪓  Gave Up", f"The word was **{word}**.", C.NEUTRAL))

    @commands.hybrid_command(name="scramble", description="Unscramble a word to win coins.")
    async def scramble(self, ctx):
        uid = str(ctx.author.id)
        if uid in _scramble_games:
            return await ctx.send(embed=warn("Scramble", "You have an active game! Type your answer."))
        word      = random.choice(WORD_LIST)
        scrambled = list(word)
        while "".join(scrambled) == word:
            random.shuffle(scrambled)
        _scramble_games[uid] = {"word": word, "start": time.time()}
        e = embed("🔀  Word Scramble",
                  f"Unscramble this word:\n\n# `{''.join(scrambled).upper()}`\n\n"
                  f"Type your answer in this channel within 30 seconds!",
                  C.GAMES, footer=f"Hint: {len(word)} letters")
        await ctx.send(embed=e)

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            _scramble_games.pop(uid, None)
            return await ctx.send(embed=warn("Scramble", f"Time's up! The word was **{word}**."))

        _scramble_games.pop(uid, None)
        elapsed = time.time() - _scramble_games.get(uid, {}).get("start", time.time())

        if msg.content.strip().lower() == word:
            reward = max(50, 200 - int(elapsed) * 3)
            from storage import load_coins, save_coins
            coins = load_coins()
            coins.setdefault(str(uid), {"wallet": 100, "bank": 0})
            coins[str(uid)]["wallet"] = int(coins[str(uid)].get("wallet", 0)) + reward
            save_coins(coins)
            await ctx.send(embed=success("Correct! 🎉", f"The word was **{word}**!\n{E.COIN} +**{reward}** coins"))
        else:
            await ctx.send(embed=error("Wrong!", f"You said **{msg.content.strip()}**.\nThe word was **{word}**."))

    @commands.hybrid_command(name="typerace", description="Speed typing challenge — fastest wins coins.")
    async def typerace(self, ctx):
        uid  = str(ctx.author.id)
        sent = random.choice(TYPING_SENTENCES)
        _typerace_games[uid] = {"sentence": sent, "start": time.time()}
        e = embed("⌨️  Type Race",
                  f"Type this sentence as fast as you can!\n\n"
                  f"```{sent}```\n"
                  f"**Ready... GO!**",
                  C.GAMES, footer="Fastest time = most coins · 60 second limit")
        await ctx.send(embed=e)

        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            _typerace_games.pop(uid, None)
            return await ctx.send(embed=warn("Type Race", "Too slow! No coins for you."))

        elapsed = time.time() - _typerace_games.pop(uid, {}).get("start", time.time())
        accuracy = sum(a == b for a, b in zip(msg.content.lower(), sent.lower())) / len(sent)

        if accuracy < 0.85:
            return await ctx.send(embed=error("Type Race", f"Too many typos ({int(accuracy*100)}% accurate). Try again!"))

        wpm    = int((len(sent.split()) / elapsed) * 60)
        reward = max(20, min(500, int(5000 / max(1, elapsed))))

        from storage import load_coins, save_coins
        coins = load_coins()
        coins.setdefault(str(uid), {"wallet": 100, "bank": 0})
        coins[str(uid)]["wallet"] = int(coins[str(uid)].get("wallet", 0)) + reward
        save_coins(coins)

        e = success("Type Race Complete! ⌨️",
                    f"**Time:** {elapsed:.2f}s\n"
                    f"**WPM:** {wpm}\n"
                    f"**Accuracy:** {int(accuracy*100)}%\n\n"
                    f"{E.COIN} +**{reward}** coins")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="truthordare", description="Truth or Dare — pick with buttons.")
    async def truthordare(self, ctx):
        e    = embed("😈  Truth or Dare", "Choose your fate…", C.SOCIAL)
        view = TruthOrDareView(ctx.author.id)
        await ctx.send(embed=e, view=view)

    # ══ SOCIAL GIF COMMANDS ═══════════════════════════════════════════════════

    async def _gif_cmd(self, ctx, member, title, text, query, color=C.SOCIAL, self_ok=False, footer_override=None):
        if not self_ok and member == ctx.author:
            return await ctx.send(embed=error(title.split("  ")[-1], "You can't do that to yourself."))
        e = _gif_action(ctx.author, member, title, text, color)
        if footer_override:
            e.set_footer(text=footer_override)
        gif = await fetch_gif(query)
        if gif:
            e.set_image(url=gif)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="cuddle", description="Cuddle someone.")
    async def cuddle(self, ctx, member: discord.Member):
        await self._gif_cmd(ctx, member, f"🤗  Cuddle", f"{ctx.author.mention} cuddled {member.mention}. Adorable.", "anime cuddle", C.MARRIAGE)

    @commands.hybrid_command(name="poke", description="Poke someone.")
    async def poke(self, ctx, member: discord.Member):
        await self._gif_cmd(ctx, member, f"👉  Poke", f"{ctx.author.mention} poked {member.mention}.", "anime poke", C.SOCIAL)

    @commands.hybrid_command(name="slap", description="Slap someone.")
    async def slap(self, ctx, member: discord.Member):
        await self._gif_cmd(ctx, member, f"👋  Slap!", f"{ctx.author.mention} slapped {member.mention}. That's gonna leave a mark.", "anime slap", C.LOSE)

    @commands.hybrid_command(name="bite", description="Bite someone.")
    async def bite(self, ctx, member: discord.Member):
        await self._gif_cmd(ctx, member, f"🦷  Bite", f"{ctx.author.mention} bit {member.mention}. Rude.", "anime bite", C.SOCIAL)

    @commands.hybrid_command(name="kick_person", description="Kick (the action) someone.")
    async def kick_person(self, ctx, member: discord.Member):
        await self._gif_cmd(ctx, member, f"🦵  Kicked!", f"{ctx.author.mention} kicked {member.mention}.", "anime kick", C.LOSE)

    @commands.hybrid_command(name="wave", description="Wave at someone.")
    async def wave(self, ctx, member: discord.Member):
        await self._gif_cmd(ctx, member, f"👋  Wave", f"{ctx.author.mention} waved at {member.mention}!", "anime wave", C.MARRIAGE)

    @commands.hybrid_command(name="highfive", description="High five someone.")
    async def highfive(self, ctx, member: discord.Member):
        await self._gif_cmd(ctx, member, f"🙌  High Five!", f"{ctx.author.mention} high-fived {member.mention}!", "anime high five", C.WIN)

    @commands.hybrid_command(name="cry", description="Post a crying GIF.")
    async def cry(self, ctx):
        e = embed("😭  Crying", f"{ctx.author.mention} is crying rn.", C.NEUTRAL)
        gif = await fetch_gif("anime cry")
        if gif: e.set_image(url=gif)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="laugh", description="Post a laughing GIF.")
    async def laugh(self, ctx):
        e = embed("😂  Laughing", f"{ctx.author.mention} is losing it.", C.WIN)
        gif = await fetch_gif("anime laughing")
        if gif: e.set_image(url=gif)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="dance", description="Post a dancing GIF.")
    async def dance(self, ctx):
        e = embed("💃  Dancing", f"{ctx.author.mention} is on the dancefloor.", C.SOCIAL)
        gif = await fetch_gif("anime dance")
        if gif: e.set_image(url=gif)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="smug", description="Post a smug face GIF.")
    async def smug(self, ctx):
        e = embed("😏  Smug", f"{ctx.author.mention} is feeling very smug.", C.SOCIAL)
        gif = await fetch_gif("anime smug")
        if gif: e.set_image(url=gif)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="blush", description="Post a blushing GIF.")
    async def blush(self, ctx):
        e = embed("😊  Blushing", f"{ctx.author.mention} is blushing.", C.MARRIAGE)
        gif = await fetch_gif("anime blush")
        if gif: e.set_image(url=gif)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="facepalm", description="Post a facepalm GIF.")
    async def facepalm(self, ctx):
        e = embed("🤦  Facepalm", f"{ctx.author.mention} can't even.", C.NEUTRAL)
        gif = await fetch_gif("anime facepalm")
        if gif: e.set_image(url=gif)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="sleep", description="Post a sleeping GIF.")
    async def sleep(self, ctx):
        e = embed("😴  Sleeping", f"{ctx.author.mention} is out cold.", C.NEUTRAL)
        gif = await fetch_gif("anime sleep")
        if gif: e.set_image(url=gif)
        await ctx.send(embed=e)

    # ══ ANIMAL IMAGES ════════════════════════════════════════════════════════

    @commands.hybrid_command(name="dog", description="Random doggo image.")
    async def dog(self, ctx):
        data = await fetch_json("https://dog.ceo/api/breeds/image/random")
        if not data:
            return await ctx.send(embed=error("Dog", "Couldn't fetch a dog right now."))
        e = embed("🐶  Doggo!", "", C.MARKET)
        e.set_image(url=data.get("message", ""))
        await ctx.send(embed=e)

    @commands.hybrid_command(name="cat", description="Random cat image.")
    async def cat(self, ctx):
        data = await fetch_json("https://api.thecatapi.com/v1/images/search")
        if not data or not isinstance(data, list):
            return await ctx.send(embed=error("Cat", "Couldn't fetch a cat right now."))
        e = embed("🐱  Kitty!", "", C.MARRIAGE)
        e.set_image(url=data[0].get("url", ""))
        await ctx.send(embed=e)

    @commands.hybrid_command(name="fox", description="Random fox image.")
    async def fox(self, ctx):
        data = await fetch_json("https://randomfox.ca/floof/")
        if not data:
            return await ctx.send(embed=error("Fox", "No fox found."))
        e = embed("🦊  Foxy!", "", C.SHOP)
        e.set_image(url=data.get("image", ""))
        await ctx.send(embed=e)

    @commands.hybrid_command(name="duck", description="Random duck image.")
    async def duck(self, ctx):
        data = await fetch_json("https://random-d.uk/api/random")
        if not data:
            return await ctx.send(embed=error("Duck", "No duck found."))
        e = embed("🦆  Quack!", "", C.TRIVIA)
        e.set_image(url=data.get("url", ""))
        await ctx.send(embed=e)

    # ══ INTERNET LOOKUPS ══════════════════════════════════════════════════════

    @commands.hybrid_command(name="define", description="Look up a word definition.")
    async def define(self, ctx, word: str):
        data = await fetch_json(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.lower()}")
        if not data or isinstance(data, dict):
            return await ctx.send(embed=error("Define", f"No definition found for **{word}**."))
        try:
            entry   = data[0]
            phonetic= entry.get("phonetic", "")
            meaning = entry["meanings"][0]
            pos     = meaning["partOfSpeech"]
            defn    = meaning["definitions"][0]["definition"]
            example = meaning["definitions"][0].get("example", "")
            desc    = f"**{pos}**\n{defn}"
            if example:
                desc += f"\n\n*\"{example}\"*"
            e = embed(f"📖  {word.capitalize()}{f'  /{phonetic}/' if phonetic else ''}",
                      desc, C.TRIVIA, footer="via Free Dictionary API")
            await ctx.send(embed=e)
        except Exception:
            await ctx.send(embed=error("Define", "Couldn't parse that definition."))

    @commands.hybrid_command(name="urban", description="Urban Dictionary lookup.")
    async def urban(self, ctx, *, term: str):
        data = await fetch_json("https://api.urbandictionary.com/v0/define", term=term)
        if not data or not data.get("list"):
            return await ctx.send(embed=error("Urban", f"Nothing found for **{term}**."))
        entry   = data["list"][0]
        defn    = entry["definition"][:800].replace("[", "").replace("]", "")
        example = entry.get("example", "")[:300].replace("[", "").replace("]", "")
        thumbs  = f"👍 {entry.get('thumbs_up',0)}  👎 {entry.get('thumbs_down',0)}"
        desc    = defn
        if example:
            desc += f"\n\n*\"{example}\"*"
        e = embed(f"📚  {term}", desc, C.SOCIAL,
                  footer=f"Urban Dictionary · {thumbs}")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="wikipedia", description="Get a Wikipedia summary.")
    async def wikipedia(self, ctx, *, query: str):
        data = await fetch_json(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
        )
        if not data or data.get("type") == "https://mediawiki.org/wiki/HyperSwitch/errors/not_found":
            return await ctx.send(embed=error("Wikipedia", f"No article found for **{query}**."))
        extract = data.get("extract", "No summary available.")[:800]
        page    = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        e = embed(f"📖  {data.get('title', query)}", extract, C.TRIVIA,
                  footer=f"Wikipedia · {page[:60] if page else ''}")
        thumb = data.get("thumbnail", {}).get("source")
        if thumb:
            e.set_thumbnail(url=thumb)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="crypto", description="Get a crypto price (e.g. bitcoin, ethereum).")
    async def crypto(self, ctx, coin: str = "bitcoin"):
        data = await fetch_json(
            "https://api.coingecko.com/api/v3/simple/price",
            ids=coin.lower(), vs_currencies="usd,gbp", include_24hr_change="true"
        )
        if not data or coin.lower() not in data:
            return await ctx.send(embed=error("Crypto", f"Coin **{coin}** not found. Try `bitcoin`, `ethereum`, `dogecoin` etc."))
        info   = data[coin.lower()]
        usd    = info.get("usd", "?")
        gbp    = info.get("gbp", "?")
        chg    = info.get("usd_24h_change", 0)
        arrow  = "📈" if chg >= 0 else "📉"
        e = embed(
            f"💰  {coin.capitalize()} Price",
            f"**USD:** ${usd:,.2f}\n**GBP:** £{gbp:,.2f}\n\n{arrow} 24h: {chg:+.2f}%",
            C.WIN if chg >= 0 else C.LOSE,
            footer="via CoinGecko · Not financial advice",
        )
        await ctx.send(embed=e)

    @commands.hybrid_command(name="weather", description="Current weather for any city.")
    async def weather(self, ctx, *, city: str):
        data = await fetch_json(
            "https://wttr.in/" + city.replace(" ", "+"),
            format="j1"
        )
        if not data:
            return await ctx.send(embed=error("Weather", f"Couldn't get weather for **{city}**."))
        try:
            cur   = data["current_condition"][0]
            desc  = cur["weatherDesc"][0]["value"]
            temp_c= cur["temp_C"]
            temp_f= cur["temp_F"]
            feels = cur["FeelsLikeC"]
            humid = cur["humidity"]
            wind  = cur["windspeedKmph"]
            rows  = [
                ("Condition", desc),
                ("Temp",      f"{temp_c}°C / {temp_f}°F"),
                ("Feels Like",f"{feels}°C"),
                ("Humidity",  f"{humid}%"),
                ("Wind",      f"{wind} km/h"),
            ]
            col_w = max(len(r[0]) for r in rows)
            table = "\n".join(f"{r[0].ljust(col_w)}  {r[1]}" for r in rows)
            e = embed(f"🌤️  Weather — {city.title()}", f"```\n{table}\n```", C.MARKET,
                      footer="via wttr.in")
            await ctx.send(embed=e)
        except Exception:
            await ctx.send(embed=error("Weather", "Couldn't parse weather data."))

    @commands.hybrid_command(name="meme", description="Random meme from Reddit.")
    async def meme(self, ctx):
        subs = ["memes", "dankmemes", "AdviceAnimals", "me_irl", "terriblefacebookmemes"]
        sub  = random.choice(subs)
        data = await fetch_json(f"https://meme-api.com/gimme/{sub}")
        if not data or data.get("nsfw"):
            return await ctx.send(embed=error("Meme", "Couldn't fetch a safe meme right now."))
        e = embed(f"😂  {data.get('title','Meme')[:100]}", "", C.SOCIAL,
                  footer=f"r/{data.get('subreddit','memes')} · {data.get('ups',0):,} upvotes")
        e.set_image(url=data.get("url", ""))
        await ctx.send(embed=e)

    # ══ UTILITY ═══════════════════════════════════════════════════════════════

    @commands.hybrid_command(name="ping", description="Check the bot's latency.")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        color   = C.WIN if latency < 100 else (C.WARN if latency < 250 else C.LOSE)
        e = embed("🏓  Pong!", f"Latency: **{latency}ms**", color)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="uptime", description="How long the bot has been running.")
    async def uptime(self, ctx):
        up = _human_uptime(time.time() - BOT_START_TIME)
        e  = embed("⏱️  Uptime", f"Running for **{up}**", C.NEUTRAL)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="botinfo", description="Bot stats and info.")
    async def botinfo(self, ctx):
        guilds  = len(self.bot.guilds)
        members = sum(g.member_count or 0 for g in self.bot.guilds)
        cmds    = len([c for c in self.bot.commands])
        up      = _human_uptime(time.time() - BOT_START_TIME)
        lat     = round(self.bot.latency * 1000)
        rows    = [
            ("Guilds",   str(guilds)),
            ("Members",  f"{members:,}"),
            ("Commands", str(cmds)),
            ("Latency",  f"{lat}ms"),
            ("Uptime",   up),
        ]
        col_w = max(len(r[0]) for r in rows)
        table = "\n".join(f"{r[0].ljust(col_w)}  {r[1]}" for r in rows)
        e = embed(f"🤖  {self.bot.user.name}", f"```\n{table}\n```", C.ADMIN)
        e.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="serverinfo", description="Server stats and info.")
    async def serverinfo(self, ctx):
        if not ctx.guild:
            return await ctx.send(embed=error("Server Info", "Server only command."))
        g      = ctx.guild
        bots   = sum(1 for m in g.members if m.bot)
        humans = g.member_count - bots
        rows   = [
            ("Name",     g.name[:30]),
            ("ID",       str(g.id)),
            ("Owner",    str(g.owner) if g.owner else "Unknown"),
            ("Members",  f"{humans:,} humans, {bots} bots"),
            ("Channels", f"{len(g.text_channels)} text, {len(g.voice_channels)} voice"),
            ("Roles",    str(len(g.roles))),
            ("Boosts",   str(g.premium_subscription_count)),
            ("Created",  g.created_at.strftime("%d %b %Y")),
        ]
        col_w = max(len(r[0]) for r in rows)
        table = "\n".join(f"{r[0].ljust(col_w)}  {r[1]}" for r in rows)
        e = embed(f"🏰  {g.name}", f"```\n{table}\n```", C.ADMIN)
        if g.icon:
            e.set_thumbnail(url=g.icon.url)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="userinfo", description="Detailed info about a user.")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        roles  = [r.mention for r in member.roles if r.name != "@everyone"][-5:]
        rows   = [
            ("Username",  str(member)),
            ("ID",        str(member.id)),
            ("Nickname",  member.nick or "None"),
            ("Joined",    member.joined_at.strftime("%d %b %Y") if member.joined_at else "Unknown"),
            ("Created",   member.created_at.strftime("%d %b %Y")),
            ("Bot",       "Yes" if member.bot else "No"),
            ("Top Role",  member.top_role.name),
        ]
        col_w = max(len(r[0]) for r in rows)
        table = "\n".join(f"{r[0].ljust(col_w)}  {r[1]}" for r in rows)
        e = embed(f"👤  {member.display_name}",
                  f"```\n{table}\n```\n**Roles:** {' '.join(roles) or 'None'}",
                  C.ADMIN)
        e.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="avatar", description="Show a user's full-size avatar.")
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        e = embed(f"🖼️  {member.display_name}'s Avatar", "", C.NEUTRAL)
        e.set_image(url=member.display_avatar.url)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Open Full Size", url=str(member.display_avatar.url)))
        await ctx.send(embed=e, view=view)

    @commands.hybrid_command(name="snowflake", description="Decode a Discord Snowflake ID.")
    async def snowflake(self, ctx, snowflake_id: str):
        try:
            sf   = int(snowflake_id)
            ts   = ((sf >> 22) + 1420070400000) / 1000
            dt   = datetime.fromtimestamp(ts, tz=timezone.utc)
            rows = [
                ("Timestamp", dt.strftime("%d %b %Y %H:%M:%S UTC")),
                ("Unix",      str(int(ts))),
                ("Worker ID", str((sf & 0x3E0000) >> 17)),
                ("Process ID",str((sf & 0x1F000) >> 12)),
                ("Increment", str(sf & 0xFFF)),
            ]
            col_w = max(len(r[0]) for r in rows)
            table = "\n".join(f"{r[0].ljust(col_w)}  {r[1]}" for r in rows)
            e = embed("❄️  Snowflake Decoded", f"```\n{table}\n```", C.NEUTRAL)
            await ctx.send(embed=e)
        except Exception:
            await ctx.send(embed=error("Snowflake", "Invalid Snowflake ID."))

    @commands.hybrid_command(name="charinfo", description="Get Unicode info about a character.")
    async def charinfo(self, ctx, character: str):
        ch = character[0]
        name = unicodedata.name(ch, "Unknown")
        cat  = unicodedata.category(ch)
        cp   = f"U+{ord(ch):04X}"
        rows = [
            ("Char",     ch),
            ("Name",     name),
            ("Category", cat),
            ("Codepoint",cp),
            ("Decimal",  str(ord(ch))),
        ]
        col_w = max(len(r[0]) for r in rows)
        table = "\n".join(f"{r[0].ljust(col_w)}  {r[1]}" for r in rows)
        e = embed(f"🔡  Character Info", f"```\n{table}\n```", C.NEUTRAL)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="color", description="Preview a hex colour.")
    async def color(self, ctx, hex_code: str):
        hex_code = hex_code.lstrip("#").strip()
        if len(hex_code) != 6 or not all(c in "0123456789abcdefABCDEF" for c in hex_code):
            return await ctx.send(embed=error("Colour", "Enter a valid 6-digit hex like `#ff6600`."))
        r, g, b = int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16)
        dc      = discord.Color.from_rgb(r, g, b)
        e = embed(f"🎨  #{hex_code.upper()}", f"**RGB:** {r}, {g}, {b}\n**Decimal:** {dc.value}", dc)
        e.set_thumbnail(url=f"https://singlecolorimage.com/get/{hex_code}/80x80")
        await ctx.send(embed=e)

    @commands.hybrid_command(name="math", description="Evaluate a maths expression.")
    async def math(self, ctx, *, expression: str):
        result = _safe_eval(expression)
        if isinstance(result, str) and not result.replace(".", "").replace("-", "").isdigit():
            return await ctx.send(embed=error("Math", result))
        e = embed("🧮  Math", f"`{expression}` = **{result}**", C.TRIVIA)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="base64enc", description="Base64 encode text.")
    async def base64enc(self, ctx, *, text: str):
        encoded = base64.b64encode(text.encode()).decode()
        e = embed("🔐  Base64 Encoded", f"```\n{encoded[:500]}\n```", C.NEUTRAL)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="base64dec", description="Base64 decode text.")
    async def base64dec(self, ctx, *, text: str):
        try:
            decoded = base64.b64decode(text.encode()).decode()
            e = embed("🔓  Base64 Decoded", f"```\n{decoded[:500]}\n```", C.NEUTRAL)
            await ctx.send(embed=e)
        except Exception:
            await ctx.send(embed=error("Base64", "Invalid Base64 input."))

    @commands.hybrid_command(name="hash", description="Hash text with MD5 or SHA256.")
    async def hash(self, ctx, algorithm: str, *, text: str):
        alg = algorithm.lower().replace("-", "")
        if alg == "md5":
            result = hashlib.md5(text.encode()).hexdigest()
        elif alg in ("sha256", "sha2"):
            result = hashlib.sha256(text.encode()).hexdigest()
        elif alg == "sha1":
            result = hashlib.sha1(text.encode()).hexdigest()
        else:
            return await ctx.send(embed=error("Hash", "Supported: `md5`, `sha1`, `sha256`"))
        e = embed(f"🔑  {algorithm.upper()} Hash", f"```\n{result}\n```", C.NEUTRAL)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="passwordgen", description="Generate a strong random password.")
    async def passwordgen(self, ctx, length: int = 16):
        if not 8 <= length <= 64:
            return await ctx.send(embed=error("Password", "Length must be between 8 and 64."))
        chars  = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
        passwd = "".join(random.SystemRandom().choice(chars) for _ in range(length))
        e = embed("🔑  Password Generated",
                  f"```\n{passwd}\n```\n*{length} characters · Never share this*",
                  C.NEUTRAL)
        try:
            await ctx.author.send(embed=e)
            await ctx.send(embed=success("Sent!", "Password sent to your DMs. 🔒"))
        except discord.Forbidden:
            await ctx.send(embed=e)

    @commands.hybrid_command(name="randomuser", description="Pick a random server member.")
    async def randomuser(self, ctx):
        if not ctx.guild:
            return await ctx.send(embed=error("Random User", "Server only."))
        humans = [m for m in ctx.guild.members if not m.bot]
        if not humans:
            return await ctx.send(embed=error("Random User", "No humans found."))
        picked = random.choice(humans)
        e = embed("🎲  Random Member", f"The chosen one is… **{picked.mention}**!", C.GAMES)
        e.set_thumbnail(url=picked.display_avatar.url)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="randomchannel", description="Pick a random text channel.")
    async def randomchannel(self, ctx):
        if not ctx.guild:
            return await ctx.send(embed=error("Random Channel", "Server only."))
        channels = ctx.guild.text_channels
        if not channels:
            return await ctx.send(embed=error("Random Channel", "No channels found."))
        picked = random.choice(channels)
        e = embed("🎲  Random Channel", f"Go chat in {picked.mention}!", C.GAMES)
        await ctx.send(embed=e)

    # ══ ECONOMY EXTRAS ════════════════════════════════════════════════════════

    @commands.hybrid_command(name="moneycount", description="Total coins in circulation server-wide.")
    async def moneycount(self, ctx):
        from storage import load_coins
        coins  = load_coins()
        wallet = sum(int(v.get("wallet", 0)) for v in coins.values())
        bank   = sum(int(v.get("bank",   0)) for v in coins.values())
        debt   = sum(int(v.get("debt",   0)) for v in coins.values())
        total  = wallet + bank
        rows   = [
            ("In Wallets", f"{wallet:,}"),
            ("In Banks",   f"{bank:,}"),
            ("Total",      f"{total:,}"),
            ("Total Debt", f"{debt:,}"),
        ]
        col_w = max(len(r[0]) for r in rows)
        table = "\n".join(f"{r[0].ljust(col_w)}  {r[1]}" for r in rows)
        e = embed(f"{E.COIN}  Server Economy Overview", f"```\n{table}\n```", C.ECONOMY)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="richcheck", description="How close to broke are you?")
    async def richcheck(self, ctx, member: discord.Member = None):
        from storage import load_coins
        member = member or ctx.author
        coins  = load_coins()
        uid    = str(member.id)
        wallet = int(coins.get(uid, {}).get("wallet", 0))
        bank   = int(coins.get(uid, {}).get("bank",   0))
        total  = wallet + bank
        all_totals = sorted(
            [int(v.get("wallet",0)) + int(v.get("bank",0)) for v in coins.values()],
            reverse=True
        )
        rank   = all_totals.index(total) + 1 if total in all_totals else len(all_totals)
        pct    = max(0, min(100, int((total / max(1, max(all_totals))) * 100)))
        bar    = "💰" * (pct // 10) + "🪙" * (10 - pct // 10)
        e = embed(
            f"💸  {member.display_name}'s Wealth Check",
            f"{bar}\n\n**{pct}%** of the richest person's wealth\n"
            f"**Rank:** #{rank} of {len(all_totals)}\n"
            f"**Total:** {total:,} coins",
            C.ECONOMY if pct > 50 else (C.WARN if pct > 20 else C.LOSE),
        )
        await ctx.send(embed=e)

    @commands.hybrid_command(name="giveaway", description="Start a coin giveaway in this channel.")
    async def giveaway(self, ctx, amount: int, duration: int = 60):
        if amount <= 0:
            return await ctx.send(embed=error("Giveaway", "Amount must be positive."))
        if not 10 <= duration <= 600:
            return await ctx.send(embed=error("Giveaway", "Duration must be 10–600 seconds."))
        from storage import load_coins, save_coins
        coins = load_coins()
        uid   = str(ctx.author.id)
        coins.setdefault(uid, {"wallet": 100, "bank": 0})
        if int(coins[uid].get("wallet", 0)) < amount:
            return await ctx.send(embed=error("Giveaway", "Not enough coins in your wallet."))
        coins[uid]["wallet"] = int(coins[uid]["wallet"]) - amount
        save_coins(coins)
        view = GiveawayView(amount, duration, ctx.author.id)
        msg  = await ctx.send(embed=view._build_embed(), view=view)
        view.message = msg
        await ctx.send(embed=embed("🎉  Giveaway Started!",
                                   f"**{amount:,}** coins up for grabs!\nEnds in **{duration}s**.",
                                   C.WIN, footer=f"Hosted by {ctx.author.display_name}"))

    # ══ TIMER / REMINDER ══════════════════════════════════════════════════════

    @commands.hybrid_command(name="remindme", description="Get a reminder in X minutes.")
    async def remindme(self, ctx, minutes: int, *, reminder: str):
        if not 1 <= minutes <= 1440:
            return await ctx.send(embed=error("Remind Me", "Minutes must be 1–1440 (24 hours max)."))
        await ctx.send(embed=success("Reminder Set! ⏰",
                                     f"I'll ping you in **{minutes} minute(s)**:\n_{reminder}_"))
        await asyncio.sleep(minutes * 60)
        try:
            await ctx.author.send(embed=embed("⏰  Reminder!", f"_{reminder}_", C.TRIVIA,
                                              footer=f"Set {minutes}m ago in {getattr(ctx.channel, 'name', 'DM')}"))
        except discord.Forbidden:
            await ctx.send(embed=embed("⏰  Reminder!", f"{ctx.author.mention} _{reminder}_", C.TRIVIA))

    @commands.hybrid_command(name="timer", description="Live countdown timer in chat (max 5 min).")
    async def timer(self, ctx, seconds: int):
        if not 5 <= seconds <= 300:
            return await ctx.send(embed=error("Timer", "Seconds must be 5–300."))
        e   = embed("⏱️  Timer", f"**{seconds}s** remaining…", C.TRIVIA)
        msg = await ctx.send(embed=e)
        start = time.time()
        while True:
            await asyncio.sleep(5)
            remaining = seconds - int(time.time() - start)
            if remaining <= 0:
                break
            e = embed("⏱️  Timer", f"**{remaining}s** remaining…", C.TRIVIA)
            try:
                await msg.edit(embed=e)
            except Exception:
                break
        e = embed("⏱️  Time's Up!", f"{ctx.author.mention} Your **{seconds}s** timer is done! 🔔", C.WIN)
        await msg.edit(embed=e)

    # ══ MISC ══════════════════════════════════════════════════════════════════

    @commands.hybrid_command(name="coinflipcount", description="Simulate flipping a coin until you get N heads in a row.")
    async def coinflipcount(self, ctx, target: int = 5):
        if not 1 <= target <= 20:
            return await ctx.send(embed=error("Coin Flip Count", "Target must be 1–20."))
        flips = 0; streak = 0
        while streak < target:
            flips += 1
            if random.random() < 0.5:
                streak += 1
            else:
                streak = 0
        e = embed("🪙  Coin Flip Streak",
                  f"It took **{flips:,}** flips to get **{target}** heads in a row!\n\n"
                  f"*Expected average: ~{int(2**(target+1)):,} flips*",
                  C.GAMES)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="dice_stats", description="Probability breakdown for a dice expression e.g. 2d6.")
    async def dice_stats(self, ctx, dice: str = "2d6"):
        pattern = re.fullmatch(r"(\d+)d(\d+)", dice.lower().strip())
        if not pattern:
            return await ctx.send(embed=error("Dice Stats", "Format: `2d6`, `3d8` etc."))
        n, s = int(pattern.group(1)), int(pattern.group(2))
        if n > 10 or s > 100:
            return await ctx.send(embed=error("Dice Stats", "Max 10 dice and d100."))
        min_r = n; max_r = n * s
        mean  = n * (s + 1) / 2
        var   = n * (s**2 - 1) / 12
        std   = math.sqrt(var)
        rows  = [
            ("Dice",    dice.upper()),
            ("Min",     str(min_r)),
            ("Max",     str(max_r)),
            ("Mean",    f"{mean:.1f}"),
            ("Std Dev", f"{std:.2f}"),
        ]
        col_w = max(len(r[0]) for r in rows)
        table = "\n".join(f"{r[0].ljust(col_w)}  {r[1]}" for r in rows)
        e = embed(f"📊  Dice Stats — {dice.upper()}", f"```\n{table}\n```", C.TRIVIA)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="length", description="Get the character length of any text.")
    async def length(self, ctx, *, text: str):
        e = embed("📏  String Length", f"`{len(text):,}` characters", C.NEUTRAL)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="toss", description="Toss a coin — heads or tails, simple and fast.")
    async def toss(self, ctx):
        result = random.choice(["Heads 🟡", "Tails ⚪"])
        e = embed("🪙  Toss", f"**{result}**", C.GAMES)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="yesno", description="Ask the bot yes or no.")
    async def yesno(self, ctx, *, question: str):
        answer = random.choice(["Yes ✅", "No ❌", "Maybe… 🤔", "Absolutely not 💀", "100% yes 🎉", "Ask again later 🎱"])
        color  = C.WIN if "yes" in answer.lower() else (C.LOSE if "no" in answer.lower() else C.NEUTRAL)
        e = embed("🎱  Yes or No?", f"**{ctx.author.display_name} asks:** {question}\n\n**{answer}**", color)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="number", description="Random number between two values.")
    async def number(self, ctx, minimum: int = 1, maximum: int = 100):
        if minimum >= maximum:
            return await ctx.send(embed=error("Number", "Minimum must be less than maximum."))
        result = random.randint(minimum, maximum)
        e = embed("🔢  Random Number", f"**{result:,}**\n\n*Between {minimum:,} and {maximum:,}*", C.GAMES)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="flip", description="Flip a table or unflip it.")
    async def flip(self, ctx):
        options = [
            "(╯°□°）╯︵ ┻━┻",
            "┬─┬ノ( º _ ºノ)",
            "(ノಠ益ಠ)ノ彡┻━┻",
            "┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻",
        ]
        await ctx.send(embed=embed("🪑  Table Flip", random.choice(options), C.LOSE))

    @commands.hybrid_command(name="aesthetics", description="Convert text to aesthetic full-width.")
    async def aesthetics(self, ctx, *, text: str):
        result = "".join(chr(ord(c) + 0xFEE0) if c.isascii() and c != " " else c for c in text)
        e = embed("✨  Aesthetics", result[:500], C.SOCIAL)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="zalgo", description="C̷o̵r̷r̵u̷p̸t̷ text with Zalgo glitch effect.")
    async def zalgo(self, ctx, *, text: str):
        zalgo_chars = [chr(i) for i in range(0x0300, 0x036F)]
        result = ""
        for ch in text[:80]:
            result += ch
            if ch.isalpha():
                result += "".join(random.choice(zalgo_chars) for _ in range(random.randint(2, 6)))
        e = embed("👁️  Z̷a̷l̶g̵o̷", result, C.LOSE)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="binary", description="Convert text to binary.")
    async def binary(self, ctx, *, text: str):
        result = " ".join(format(ord(c), "08b") for c in text[:30])
        e = embed("💻  Binary", f"```\n{result}\n```", C.NEUTRAL)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="morse", description="Convert text to Morse code.")
    async def morse(self, ctx, *, text: str):
        morse_map = {
            "a":".-","b":"-...","c":"-.-.","d":"-..","e":".","f":"..-.","g":"--.","h":"....","i":"..","j":".---",
            "k":"-.-","l":".-..","m":"--","n":"-.","o":"---","p":".--.","q":"--.-","r":".-.","s":"...","t":"-",
            "u":"..-","v":"...-","w":".--","x":"-..-","y":"-.--","z":"--..","0":"-----","1":".----","2":"..---",
            "3":"...--","4":"....-","5":".....","6":"-....","7":"--...","8":"---..","9":"----.",".":".-.-.-",
            ",":"--..--","?":"..--..","!":"-.-.--"," ":"/"
        }
        result = " ".join(morse_map.get(c.lower(), "?") for c in text[:60])
        e = embed("📡  Morse Code", f"```\n{result}\n```", C.NEUTRAL)
        await ctx.send(embed=e)

    @commands.hybrid_command(name="countdown", description="Post a big countdown message.")
    async def countdown(self, ctx, from_number: int = 10):
        if not 3 <= from_number <= 30:
            return await ctx.send(embed=error("Countdown", "Choose a number between 3 and 30."))
        msg = await ctx.send(embed=embed("⏳  Countdown", f"# {from_number}", C.TRIVIA))
        for i in range(from_number - 1, 0, -1):
            await asyncio.sleep(1)
            color = C.WIN if i <= 3 else C.TRIVIA
            await msg.edit(embed=embed("⏳  Countdown", f"# {i}", color))
        await asyncio.sleep(1)
        await msg.edit(embed=embed("🚀  GO!", "# 🎉", C.WIN))


async def setup(bot: commands.Bot):
    await bot.add_cog(Extras(bot))
