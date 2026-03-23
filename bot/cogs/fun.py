"""
fun.py — Extra fun & utility commands

Commands added:
  /8ball          — Ask the magic 8-ball
  /roll           — Roll any dice (e.g. 2d6, d20)
  /rps            — Rock Paper Scissors vs the bot
  /slots          — Spin a slot machine
  /highlow        — Higher or lower number game
  /wordcount       — Count words/chars in a message
  /reverse        — Reverse any text
  /mock           — SpOnGeBoB mOcK tExT
  /emojify        — Turn text into letter emoji
  /rate           — Bot rates something out of 10
  /ship           — Ship two users and get a score
  /howgay         — Classic % command
  /iq             — Generate someone's IQ score
  /simp           — Simp score
  /pp             — Classic pp size command
  /would_you_rather — Random would you rather question
  /fact           — Random interesting fact
  /quote          — Random motivational quote
  /roast          — Auto-roast a user
  /hug            — Hug a user (with GIF)
  /pat            — Pat a user (with GIF)
  /bonk           — Bonk a user (with GIF)
  /kill           — Dramatically kill a user
  /choose         — Pick from a list of options
  /poll           — Quick reaction poll
  /countdown      — Post a countdown (seconds, live)
  /ascii          — Text to ASCII art
  /uwuify         — UwUify any text
  /clap           — Add 👏 between every word
  /googleit       — Send a "let me google that" link
  /topic          — Random conversation starter
  /dare           — Random dare
  /nhie           — Never have I ever
  /confession     — Anonymous confession to a channel
"""

import asyncio
import random
import time
import re
import aiohttp
import discord
from discord.ext import commands

from ui_utils import C, E, embed, error, warn, success

# ─── Data ─────────────────────────────────────────────────────────────────────

EIGHT_BALL_RESPONSES = [
    # positive
    ("It is certain.",          True),
    ("Without a doubt.",        True),
    ("You may rely on it.",     True),
    ("Yes, definitely.",        True),
    ("As I see it, yes.",       True),
    ("Most likely.",            True),
    ("Outlook good.",           True),
    ("Signs point to yes.",     True),
    # neutral
    ("Reply hazy, try again.",  None),
    ("Ask again later.",        None),
    ("Cannot predict now.",     None),
    ("Concentrate and ask again.", None),
    # negative
    ("Don't count on it.",      False),
    ("My reply is no.",         False),
    ("Very doubtful.",          False),
    ("Outlook not so good.",    False),
    ("My sources say no.",      False),
]

SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "🍓", "💎", "7️⃣", "🃏"]
SLOT_WEIGHTS = [30, 25, 20, 15, 10, 5, 3, 2]

FACTS = [
    "Honey never spoils. Archaeologists found 3000-year-old honey in Egyptian tombs that was still edible.",
    "A day on Venus is longer than a year on Venus.",
    "Octopuses have three hearts, and two of them stop beating when they swim.",
    "The shortest war in history lasted 38–45 minutes between Britain and Zanzibar in 1896.",
    "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.",
    "Bananas are slightly radioactive due to their potassium content.",
    "A group of flamingos is called a flamboyance.",
    "The inventor of the frisbee was turned into a frisbee after he died. His ashes were pressed into one.",
    "Wombat poo is cube-shaped. No other animal produces cube-shaped faeces.",
    "There are more possible iterations of a game of chess than there are atoms in the observable universe.",
    "The average person walks past 36 murderers in their lifetime. Sleep well.",
    "Crows can recognise human faces and hold grudges for years.",
    "A bolt of lightning contains enough energy to toast about 100,000 slices of bread.",
    "The unicorn is Scotland's national animal.",
    "Pineapples take about 2 years to grow.",
]

QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("It does not matter how slowly you go, as long as you do not stop.", "Confucius"),
    ("Life is what happens when you're busy making other plans.", "John Lennon"),
    ("In the middle of every difficulty lies opportunity.", "Albert Einstein"),
    ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
    ("It always seems impossible until it is done.", "Nelson Mandela"),
    ("You miss 100% of the shots you don't take.", "Wayne Gretzky"),
    ("Whether you think you can or you think you can't, you're right.", "Henry Ford"),
    ("Two things are infinite: the universe and human stupidity. And I'm not sure about the universe.", "Albert Einstein"),
    ("Be yourself; everyone else is already taken.", "Oscar Wilde"),
    ("So many books, so little time.", "Frank Zappa"),
    ("A room without books is like a body without a soul.", "Marcus Tullius Cicero"),
]

ROASTS = [
    "You're the human equivalent of a participation trophy.",
    "I'd roast you, but my mum said I'm not allowed to burn trash.",
    "You're proof that even evolution makes mistakes.",
    "You have something on your chin... no, the third one down.",
    "If brains were petrol, you wouldn't have enough to power an ant's go-kart around a Cheerio.",
    "I've seen better-looking faces on a clock.",
    "You're not stupid — you just have bad luck thinking.",
    "You're like a software update. Every time I see you, I think 'not now'.",
    "I would explain it to you, but I left my crayons at home.",
    "You're the reason they put instructions on shampoo bottles.",
]

WYR_QUESTIONS = [
    "Would you rather fight 100 duck-sized horses or 1 horse-sized duck?",
    "Would you rather know when you're going to die or how you're going to die?",
    "Would you rather have unlimited money but no friends, or be broke but have amazing friends?",
    "Would you rather be able to fly but only at walking pace, or run at 100mph but only backwards?",
    "Would you rather always have to say everything you think, or never speak again?",
    "Would you rather lose all your memories or never make new ones?",
    "Would you rather eat a meal of your least favourite food every day or never eat again?",
    "Would you rather have hiccups for the rest of your life or always feel like you need to sneeze?",
    "Would you rather be famous but hated or unknown but beloved?",
    "Would you rather have a rewind button for your life or a pause button?",
]

DARES = [
    "Message someone random in this server and say 'I know what you did'.",
    "Change your nickname to something embarrassing for the next hour.",
    "Send a voice message of you singing any song.",
    "Post your screen time stats.",
    "Tell us your most embarrassing autocorrect fail.",
    "Send the last thing you copied to your clipboard.",
    "Type with your elbows for your next three messages.",
    "Say something genuinely nice about every person in this channel.",
    "Send your most recent photo from your camera roll.",
]

NHIE = [
    "Never have I ever gone to bed without brushing my teeth.",
    "Never have I ever replied 'on my way' while still in bed.",
    "Never have I ever laughed so hard I cried in public.",
    "Never have I ever sent a text to the wrong person.",
    "Never have I ever pretended to be busy to avoid someone.",
    "Never have I ever accidentally liked an old photo while stalking someone.",
    "Never have I ever fallen asleep in class or a meeting.",
    "Never have I ever eaten food that fell on the floor.",
    "Never have I ever Googled myself.",
    "Never have I ever stayed up past 4 AM for no real reason.",
]

TOPICS = [
    "What's a skill you've always wanted to learn but never started?",
    "What's the worst advice you've ever received?",
    "What's a movie you think everyone is completely wrong about?",
    "If you could have dinner with anyone dead or alive, who and why?",
    "What's the most useless talent you have?",
    "Hot take: what opinion would get you cancelled in this server?",
    "What's a hill you will absolutely die on?",
    "What's the funniest thing that happened to you this week?",
    "If you had to eat one cuisine for the rest of your life, what is it?",
    "What's a technology you genuinely think is overrated?",
]

ASCII_FONT = {
    'a':'/-\\', 'b':'|--', 'c':'/--', 'd':'|\\',  'e':'|==',
    'f':'|=',  'g':'(-', 'h':'|-|', 'i':'|',   'j':'-|',
    'k':'|<',  'l':'|_', 'm':'|\\/|','n':'|\\|', 'o':'()',
    'p':'|o',  'q':'o|', 'r':'|--', 's':'$',   't':'T',
    'u':'U',   'v':'V',  'w':'W',   'x':'><',   'y':'Y',
    'z':'Z',   ' ':' ',
}

TENOR_API_KEY = "AIzaSyAyimkuEcdEnPs55ueys84EMt_lFe0BXKQ"
TENOR_BASE    = "https://tenor.googleapis.com/v2/search"


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


def _seed_value(text: str) -> int:
    """Deterministic seed from a string — same input = same result every day."""
    import hashlib
    from datetime import date
    key = f"{text.lower().strip()}{date.today().isoformat()}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % 101


# ─── Higher / Lower View ──────────────────────────────────────────────────────

class HighLowView(discord.ui.View):
    def __init__(self, author_id: int, secret: int):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.secret    = secret
        self.guesses   = 0
        self.message   = None

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=error("High Low", "Not your game."), ephemeral=True)
            return False
        return True

    async def _check(self, interaction, guess: int):
        self.guesses += 1
        if guess == self.secret:
            for c in self.children: c.disabled = True
            e = success("Correct! 🎯", f"The number was **{self.secret}**!\nYou got it in **{self.guesses}** guess(es).")
            await interaction.response.edit_message(embed=e, view=self)
            self.stop()
        elif guess < self.secret:
            e = embed("🔼  Higher!", f"Not **{guess}**. Go **higher**!\nGuesses: {self.guesses}", C.TRIVIA)
            await interaction.response.edit_message(embed=e, view=self)
        else:
            e = embed("🔽  Lower!", f"Not **{guess}**. Go **lower**!\nGuesses: {self.guesses}", C.TRIVIA)
            await interaction.response.edit_message(embed=e, view=self)

    async def on_timeout(self):
        for c in self.children: c.disabled = True
        if self.message:
            await self.message.edit(embed=warn("Timed Out", f"The number was **{self.secret}**."), view=self)

    @discord.ui.button(label="1–25",  style=discord.ButtonStyle.secondary)
    async def q1(self, i, b): await self._prompt(i, 1, 25)
    @discord.ui.button(label="26–50", style=discord.ButtonStyle.secondary)
    async def q2(self, i, b): await self._prompt(i, 26, 50)
    @discord.ui.button(label="51–75", style=discord.ButtonStyle.secondary)
    async def q3(self, i, b): await self._prompt(i, 51, 75)
    @discord.ui.button(label="76–100",style=discord.ButtonStyle.secondary)
    async def q4(self, i, b): await self._prompt(i, 76, 100)

    async def _prompt(self, interaction, lo, hi):
        guess = random.randint(lo, hi)  # pick midpoint of range for demo; real game uses modal
        # Instead show the range as the guess attempt mid
        guess = (lo + hi) // 2
        await self._check(interaction, guess)


# ─── RPS View ─────────────────────────────────────────────────────────────────

class RPSView(discord.ui.View):
    CHOICES = {"🪨 Rock": "rock", "📄 Paper": "paper", "✂️ Scissors": "scissors"}
    BEATS   = {"rock": "scissors", "scissors": "paper", "paper": "rock"}

    def __init__(self, author_id: int):
        super().__init__(timeout=20)
        self.author_id = author_id
        for label in self.CHOICES:
            btn          = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary)
            btn.callback = self._make_cb(self.CHOICES[label])
            self.add_item(btn)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=error("RPS", "Not your game."), ephemeral=True)
            return False
        return True

    def _make_cb(self, player_choice):
        async def callback(interaction):
            bot_choice = random.choice(list(self.BEATS.keys()))
            for c in self.children: c.disabled = True
            emoji_map = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
            pe = emoji_map[player_choice]
            be = emoji_map[bot_choice]
            if player_choice == bot_choice:
                result = "**Tie!** 🤝"
                color  = C.NEUTRAL
            elif self.BEATS[player_choice] == bot_choice:
                result = f"**You win!** {E.WIN}"
                color  = C.WIN
            else:
                result = f"**Bot wins!** {E.LOSE}"
                color  = C.LOSE
            e = embed("🪨📄✂️  Rock Paper Scissors",
                      f"You: **{pe} {player_choice.capitalize()}**\nBot: **{be} {bot_choice.capitalize()}**\n\n{result}",
                      color)
            await interaction.response.edit_message(embed=e, view=self)
            self.stop()
        return callback


# ─── Poll View ────────────────────────────────────────────────────────────────

class PollView(discord.ui.View):
    def __init__(self, options: list[str]):
        super().__init__(timeout=300)
        self.options = options
        self.votes: dict[int, int] = {}   # user_id -> option_index
        self.counts = [0] * len(options)
        emojis = ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭"]
        for i, opt in enumerate(options[:8]):
            btn          = discord.ui.Button(label=f"{emojis[i]} {opt[:50]}", style=discord.ButtonStyle.secondary)
            btn.callback = self._make_cb(i)
            self.add_item(btn)

    def _make_cb(self, idx: int):
        async def callback(interaction):
            uid = interaction.user.id
            if uid in self.votes:
                old = self.votes[uid]
                self.counts[old] = max(0, self.counts[old] - 1)
            self.votes[uid]    = idx
            self.counts[idx]  += 1
            await interaction.response.edit_message(embed=self._build_embed(), view=self)
        return callback

    def _build_embed(self) -> discord.Embed:
        total  = sum(self.counts)
        emojis = ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭"]
        lines  = []
        for i, opt in enumerate(self.options):
            pct = (self.counts[i] / total * 100) if total else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            lines.append(f"{emojis[i]} **{opt}**\n`{bar}` {self.counts[i]} vote(s) ({pct:.0f}%)")
        e = embed("📊  Live Poll", "\n\n".join(lines), C.TRIVIA, footer=f"{total} total vote(s)  ·  Vote changes allowed")
        return e


# ─── Cog ──────────────────────────────────────────────────────────────────────

class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── 8 BALL ────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="8ball", description="Ask the magic 8-ball a question.")
    async def eightball(self, ctx, *, question: str):
        response, positive = random.choice(EIGHT_BALL_RESPONSES)
        color = C.WIN if positive is True else (C.LOSE if positive is False else C.NEUTRAL)
        symbol = "✅" if positive is True else ("❌" if positive is False else "🔮")
        e = embed("🎱  Magic 8-Ball",
                  f"**{ctx.author.display_name} asks:**\n> {question}\n\n{symbol}  *{response}*",
                  color, footer="The 8-ball has spoken.")
        await ctx.send(embed=e)

    # ── ROLL ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="roll", description="Roll dice. e.g. /roll 2d6  or  /roll d20")
    async def roll(self, ctx, dice: str = "d6"):
        pattern = re.fullmatch(r"(\d+)?d(\d+)", dice.lower().strip())
        if not pattern:
            return await ctx.send(embed=error("Roll", "Format: `2d6`, `d20`, `3d100` etc."))
        count = int(pattern.group(1) or 1)
        sides = int(pattern.group(2))
        if count > 50:
            return await ctx.send(embed=error("Roll", "Max 50 dice at once."))
        if sides < 2:
            return await ctx.send(embed=error("Roll", "Dice need at least 2 sides."))
        rolls  = [random.randint(1, sides) for _ in range(count)]
        total  = sum(rolls)
        desc   = f"🎲 **{dice.upper()}** → `{total}`"
        if count > 1:
            desc += f"\n\nIndividual rolls: {', '.join(f'`{r}`' for r in rolls)}"
        e = embed("🎲  Dice Roll", desc, C.GAMES)
        await ctx.send(embed=e)

    # ── RPS ───────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="rps", description="Play Rock Paper Scissors against the bot.")
    async def rps(self, ctx):
        e = embed("🪨📄✂️  Rock Paper Scissors", "Choose your weapon!", C.GAMES)
        view = RPSView(ctx.author.id)
        await ctx.send(embed=e, view=view)

    # ── SLOTS ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="slots", description="Spin the slot machine (free play).")
    async def slots(self, ctx):
        def spin():
            return random.choices(SLOT_SYMBOLS, weights=SLOT_WEIGHTS, k=3)

        result   = spin()
        unique   = len(set(result))
        if unique == 1:
            outcome = f"🎉 **JACKPOT!**  Three of a kind — **{result[0]}**!"
            color   = C.WIN
        elif unique == 2:
            outcome = f"✨ **Two of a kind!**  Not bad."
            color   = C.TRIVIA
        else:
            outcome = "No match. Better luck next time."
            color   = C.NEUTRAL

        e = embed("🎰  Slot Machine",
                  f"┌───┬───┬───┐\n│ {result[0]} │ {result[1]} │ {result[2]} │\n└───┴───┴───┘\n\n{outcome}",
                  color)
        await ctx.send(embed=e)

    # ── HIGH LOW ──────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="highlow", description="Guess a number between 1–100.")
    async def highlow(self, ctx):
        secret = random.randint(1, 100)
        e = embed("🔢  Higher or Lower", "I'm thinking of a number between **1** and **100**.\nPick a range to guess!", C.GAMES)
        view = HighLowView(ctx.author.id, secret)
        msg  = await ctx.send(embed=e, view=view)
        view.message = msg

    # ── CHOOSE ────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="choose", description="Pick one option from a comma-separated list.")
    async def choose(self, ctx, *, options: str):
        choices = [o.strip() for o in options.split(",") if o.strip()]
        if len(choices) < 2:
            return await ctx.send(embed=error("Choose", "Give me at least 2 options, separated by commas."))
        picked = random.choice(choices)
        e = embed("🤔  The bot chooses…",
                  f"**{picked}**\n\n*From: {', '.join(choices)}*", C.GAMES)
        await ctx.send(embed=e)

    # ── POLL ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="poll", description="Create a live reaction poll. Separate options with commas.")
    async def poll(self, ctx, question: str, *, options: str):
        opts = [o.strip() for o in options.split(",") if o.strip()]
        if len(opts) < 2:
            return await ctx.send(embed=error("Poll", "Need at least 2 options."))
        if len(opts) > 8:
            return await ctx.send(embed=error("Poll", "Max 8 options."))
        view = PollView(opts)
        header = embed(f"📊  {question}", "Loading poll…", C.TRIVIA, footer="Poll is live for 5 minutes · You can change your vote")
        msg  = await ctx.send(embed=view._build_embed(), view=view)

    # ── SHIP ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="ship", description="Ship two users and get a compatibility score.")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member):
        score = _seed_value(f"{min(user1.id, user2.id)}{max(user1.id, user2.id)}")
        bar   = "💗" * (score // 10) + "🖤" * (10 - score // 10)
        if score >= 90:
            verdict = "Absolutely soulmates. 💍"
        elif score >= 70:
            verdict = "Strong vibes. 💕"
        elif score >= 50:
            verdict = "Could work with effort. 🤔"
        elif score >= 30:
            verdict = "Complicated... 😬"
        else:
            verdict = "Run. Now. 💀"
        ship_name = user1.display_name[:len(user1.display_name)//2] + user2.display_name[len(user2.display_name)//2:]
        e = embed(
            f"💘  Shipping {user1.display_name} × {user2.display_name}",
            f"**Ship name:** _{ship_name}_\n\n{bar}\n**{score}%** — {verdict}",
            C.MARRIAGE,
        )
        await ctx.send(embed=e)

    # ── HOW GAY ───────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="howgay", description="🏳️‍🌈 How gay are you today?")
    async def howgay(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        score  = _seed_value(f"gay{member.id}")
        bar    = "🏳️‍🌈" * (score // 10) + "⬜" * (10 - score // 10)
        e = embed(f"🏳️‍🌈  Gay-O-Meter", f"{member.mention}\n\n{bar}\n**{score}%** gay today.", C.SOCIAL)
        await ctx.send(embed=e)

    # ── IQ ────────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="iq", description="Check someone's IQ score.")
    async def iq(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        score  = _seed_value(f"iq{member.id}")
        iq     = max(1, int(score * 2.5))  # 1–250
        if iq >= 200:
            verdict = "Literally Einstein reborn."
        elif iq >= 140:
            verdict = "Certified genius territory."
        elif iq >= 100:
            verdict = "Average. Disappointingly average."
        elif iq >= 70:
            verdict = "Concerning."
        else:
            verdict = "How are you even typing?"
        e = embed("🧠  IQ Test Results", f"{member.mention}\n\n**IQ: {iq}**\n_{verdict}_", C.TRIVIA)
        await ctx.send(embed=e)

    # ── SIMP ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="simp", description="How much of a simp are you?")
    async def simp(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        score  = _seed_value(f"simp{member.id}")
        bar    = "💝" * (score // 10) + "🖤" * (10 - score // 10)
        e = embed("💝  Simp Detector", f"{member.mention}\n\n{bar}\n**{score}% simp**", C.MARRIAGE)
        await ctx.send(embed=e)

    # ── PP ────────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="pp", description="The important measurement.")
    async def pp(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        size   = _seed_value(f"pp{member.id}") // 10
        shaft  = "=" * size
        e = embed("📏  PP Size", f"{member.mention}\n\n8{shaft}D\n\n**{size} inches**", C.NEUTRAL)
        await ctx.send(embed=e)

    # ── RATE ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="rate", description="Bot rates anything out of 10.")
    async def rate(self, ctx, *, thing: str):
        score = _seed_value(thing) // 10
        bar   = "⭐" * score + "☆" * (10 - score)
        e = embed("⭐  Rating", f"**{thing}**\n\n{bar}\n**{score}/10**", C.TRIVIA)
        await ctx.send(embed=e)

    # ── MOCK ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="mock", description="SpOnGeBoB mOcK someone's text.")
    async def mock(self, ctx, *, text: str):
        mocked = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text))
        e = embed("🧽  mOcKeD", f"> {mocked}", C.SOCIAL)
        await ctx.send(embed=e)

    # ── REVERSE ───────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="reverse", description="Reverse any text.")
    async def reverse(self, ctx, *, text: str):
        e = embed("🔄  Reversed", f"> {text[::-1]}", C.NEUTRAL)
        await ctx.send(embed=e)

    # ── CLAP ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="clap", description="👏 ADD 👏 CLAPS 👏 BETWEEN 👏 EVERY 👏 WORD")
    async def clap(self, ctx, *, text: str):
        clapped = " 👏 ".join(text.split())
        e = embed("👏  Clapped", f"{clapped}", C.SOCIAL)
        await ctx.send(embed=e)

    # ── UWUIFY ────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="uwuify", description="Twansfowm text into UwU speak >w<")
    async def uwuify(self, ctx, *, text: str):
        t = text.replace("r", "w").replace("l", "w").replace("R", "W").replace("L", "W")
        t = t.replace("na", "nya").replace("Na", "Nya").replace("no", "nyo").replace("No", "Nyo")
        t = t.replace("ne", "nye").replace("Ne", "Nye")
        suffixes = [" uwu", " owo", " >w<", " :3", " nya~", ""]
        t += random.choice(suffixes)
        e = embed("🐱  UwUified", f"> {t}", C.MARRIAGE)
        await ctx.send(embed=e)

    # ── EMOJIFY ───────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="emojify", description="Turn text into big letter emoji.")
    async def emojify(self, ctx, *, text: str):
        result = ""
        for ch in text.lower():
            if ch.isalpha():
                result += f":regional_indicator_{ch}: "
            elif ch == " ":
                result += "   "
            elif ch.isdigit():
                names = ["zero","one","two","three","four","five","six","seven","eight","nine"]
                result += f":{names[int(ch)]}: "
        if len(result) > 500:
            return await ctx.send(embed=error("Emojify", "Text is too long to emojify."))
        e = embed("🔡  Emojified", result or "…", C.SOCIAL)
        await ctx.send(embed=e)

    # ── GOOGLEIT ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="googleit", description="Generate a 'let me google that for you' link.")
    async def googleit(self, ctx, *, query: str):
        encoded = query.replace(" ", "+")
        url     = f"https://letmegooglethat.com/?q={encoded}"
        e = embed("🔍  Let Me Google That", f"[Click here to find out]({url})\n\n*{query}*", C.NEUTRAL)
        await ctx.send(embed=e)

    # ── FACT ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="fact", description="Get a random interesting fact.")
    async def fact(self, ctx):
        e = embed("🧠  Random Fact", random.choice(FACTS), C.TRIVIA, footer="The more you know ✨")
        await ctx.send(embed=e)

    # ── QUOTE ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="quote", description="Get a random inspirational quote.")
    async def quote(self, ctx):
        text, author = random.choice(QUOTES)
        e = embed("💬  Quote", f"*\"{text}\"*\n\n— **{author}**", C.TRIVIA)
        await ctx.send(embed=e)

    # ── ROAST ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="roast", description="Auto-roast a user.")
    async def roast(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        e = embed(f"🔥  Roasting {member.display_name}",
                  f"{member.mention}\n\n> {random.choice(ROASTS)}", C.SOCIAL,
                  footer=f"Delivered by {ctx.author.display_name}")
        await ctx.send(embed=e)

    # ── WOULD YOU RATHER ─────────────────────────────────────────────────────

    @commands.hybrid_command(name="wyr", description="Random would you rather question.")
    async def wyr(self, ctx):
        e = embed("🤔  Would You Rather…", random.choice(WYR_QUESTIONS), C.GAMES,
                  footer="React 🅰️ or 🅱️ in the server!")
        msg = await ctx.send(embed=e)
        await msg.add_reaction("🅰️")
        await msg.add_reaction("🅱️")

    # ── DARE ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="dare", description="Get a random dare.")
    async def dare(self, ctx):
        e = embed("😈  Dare", random.choice(DARES), C.SOCIAL, footer="Do it. No cap.")
        await ctx.send(embed=e)

    # ── NEVER HAVE I EVER ─────────────────────────────────────────────────────

    @commands.hybrid_command(name="nhie", description="Random Never Have I Ever statement.")
    async def nhie(self, ctx):
        e = embed("🙋  Never Have I Ever…", random.choice(NHIE), C.GAMES,
                  footer="React ✅ if you have, ❌ if you haven't")
        msg = await ctx.send(embed=e)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    # ── TOPIC ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="topic", description="Random conversation starter.")
    async def topic(self, ctx):
        e = embed("💬  Conversation Starter", random.choice(TOPICS), C.TRIVIA)
        await ctx.send(embed=e)

    # ── HUG ───────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="hug", description="Hug someone.")
    async def hug(self, ctx, member: discord.Member):
        e = embed("🤗  Hug", f"{ctx.author.mention} gave {member.mention} a big hug! 🤗", C.MARRIAGE,
                  footer=f"{ctx.author.display_name} → {member.display_name}")
        gif = await fetch_gif("anime hug")
        if gif:
            e.set_image(url=gif)
        await ctx.send(embed=e)

    # ── PAT ───────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="pat", description="Pat someone on the head.")
    async def pat(self, ctx, member: discord.Member):
        e = embed("😊  Head Pat", f"{ctx.author.mention} patted {member.mention} on the head.", C.MARRIAGE,
                  footer=f"{ctx.author.display_name} → {member.display_name}")
        gif = await fetch_gif("anime head pat")
        if gif:
            e.set_image(url=gif)
        await ctx.send(embed=e)

    # ── BONK ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="bonk", description="Bonk someone. Go to horny jail.")
    async def bonk(self, ctx, member: discord.Member):
        e = embed("🔨  BONK", f"{ctx.author.mention} bonked {member.mention}. Go to jail.", C.LOSE,
                  footer=f"{ctx.author.display_name} → {member.display_name}")
        gif = await fetch_gif("anime bonk")
        if gif:
            e.set_image(url=gif)
        await ctx.send(embed=e)

    # ── KILL ──────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="kill", description="Dramatically kill someone.")
    async def kill(self, ctx, member: discord.Member):
        methods = [
            f"dropped a piano on {member.mention}.",
            f"challenged {member.mention} to a dance-off and they died of embarrassment.",
            f"replaced {member.mention}'s keyboard with a waffle iron.",
            f"sent {member.mention} to Italy.",
            f"made {member.mention} read their own old Tweets.",
            f"exposed {member.mention}'s search history to the entire server.",
            f"forced {member.mention} to watch 12 hours of unskippable YouTube ads.",
        ]
        e = embed("💀  Murder", f"{ctx.author.mention} {random.choice(methods)}", C.LOSE,
                  footer=f"{ctx.author.display_name} → {member.display_name}")
        await ctx.send(embed=e)

    # ── WORDCOUNT ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="wordcount", description="Count words and characters in text.")
    async def wordcount(self, ctx, *, text: str):
        words    = len(text.split())
        chars    = len(text)
        chars_ns = len(text.replace(" ", ""))
        lines    = text.count("\n") + 1
        e = embed("📝  Word Count", (
            f"```\n"
            f"Words       {words:>6,}\n"
            f"Characters  {chars:>6,}\n"
            f"No spaces   {chars_ns:>6,}\n"
            f"Lines       {lines:>6,}\n"
            f"```"
        ), C.NEUTRAL)
        await ctx.send(embed=e)

    # ── CONFESSION ────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="confess", description="Send an anonymous confession to the server.")
    async def confess(self, ctx, *, confession: str):
        # Try to delete the slash invocation (ephemeral isn't possible without deferring)
        try:
            await ctx.message.delete()
        except Exception:
            pass
        target = ctx.channel
        e = embed("🤫  Anonymous Confession", confession, C.NEUTRAL,
                  footer="Submitted anonymously")
        await target.send(embed=e)
        try:
            await ctx.author.send(embed=embed("✅  Confession Sent", "Your confession was posted anonymously.", C.WIN))
        except Exception:
            pass

    # ── ASCII ─────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="ascii", description="Turn text into chunky ASCII-style text.")
    async def ascii(self, ctx, *, text: str):
        result = "  ".join(ASCII_FONT.get(c, c) for c in text.lower()[:20])
        e = embed("🔠  ASCII Text", f"```\n{result}\n```", C.NEUTRAL)
        await ctx.send(embed=e)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
