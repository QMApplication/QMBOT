import random
import discord
from discord.ext import commands

from storage import load_coins, save_coins
from ui_utils import C, E, embed, success, error, warn

BLACKJACK_GAMES: dict[str, dict] = {}


def ensure_user(coins: dict, user_id) -> dict:
    uid = str(user_id)
    if uid not in coins:
        coins[uid] = {"wallet": 100, "bank": 0}
    return coins[uid]


# ─── Card Logic ───────────────────────────────────────────────────────────────

def draw_card() -> str:
    ranks = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    suits = ["♠","♥","♦","♣"]
    return f"{random.choice(ranks)}{random.choice(suits)}"

def card_value(card: str) -> int:
    r = card[:-1]
    if r in {"J","Q","K"}: return 10
    if r == "A":           return 11
    return int(r)

def hand_value(hand: list[str]) -> int:
    total = sum(card_value(c) for c in hand)
    aces  = sum(1 for c in hand if c[:-1] == "A")
    while total > 21 and aces:
        total -= 10
        aces  -= 1
    return total

def render_card(card: str) -> list[str]:
    rank, suit = card[:-1], card[-1]
    mid = rank.center(3)
    return ["┌─────┐", f"│{suit:<5}│", f"│ {mid} │", f"│{suit:>5}│", "└─────┘"]

def render_hidden() -> list[str]:
    return ["┌─────┐", "│░░░░░│", "│░ ? ░│", "│░░░░░│", "└─────┘"]

def combine_cards(cards: list[str], hide_second: bool = False) -> str:
    rendered = [render_card(c) if not (hide_second and i == 1) else render_hidden()
                for i, c in enumerate(cards)]
    return "\n".join("  ".join(r[row] for r in rendered) for row in range(5))


# ─── Gamble View ──────────────────────────────────────────────────────────────

class GambleView(discord.ui.View):
    def __init__(self, *, author_id, coins, user, bet):
        super().__init__(timeout=20)
        self.author_id = author_id
        self.coins = coins
        self.user  = user
        self.bet   = bet
        self.message = None

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(embed=error("Gamble", "This isn't your bet."), ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        self.user["wallet"] += self.bet
        save_coins(self.coins)
        e = warn("Timed Out", f"You didn't choose in time. Your **{self.bet:,}** coins were refunded.")
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(embed=e, view=self)

    async def _finish(self, interaction, choice):
        result = random.choice(["red", "black"])
        for child in self.children:
            child.disabled = True
        if choice == result:
            self.user["wallet"] += self.bet * 2
            e = embed(f"{E.WIN}  Winner!", f"🎰 **{result.capitalize()}** — correct!\n\n{E.COIN} You won **{self.bet*2:,}** coins!", C.WIN)
        else:
            e = embed(f"{E.LOSE}  Wrong Colour!", f"🎰 It was **{result.capitalize()}** — you guessed **{choice}**.\n\n{E.COIN} Lost **{self.bet:,}** coins.", C.LOSE)
        e.add_field(name=f"{E.WALLET} Wallet", value=f"`{self.user['wallet']:,}`", inline=False)
        save_coins(self.coins)
        await interaction.response.edit_message(embed=e, view=self)
        self.stop()

    @discord.ui.button(label="🔴  Red",   style=discord.ButtonStyle.danger)
    async def red_button(self, interaction, button):
        await self._finish(interaction, "red")

    @discord.ui.button(label="⚫  Black", style=discord.ButtonStyle.secondary)
    async def black_button(self, interaction, button):
        await self._finish(interaction, "black")


# ─── Blackjack View ───────────────────────────────────────────────────────────

class BlackjackView(discord.ui.View):
    def __init__(self, *, author_id):
        super().__init__(timeout=60)
        self.author_id = str(author_id)

    async def interaction_check(self, interaction):
        if str(interaction.user.id) != self.author_id:
            await interaction.response.send_message(embed=error("Blackjack", "This isn't your game."), ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        BLACKJACK_GAMES.pop(self.author_id, None)

    def build_embed(self, game, reveal_dealer=False, result_text=None):
        p_val = hand_value(game["player"])
        d_val = hand_value(game["dealer"])
        p_cards = combine_cards(game["player"])
        d_cards = combine_cards(game["dealer"], hide_second=not reveal_dealer)
        d_label = f"Dealer  ({d_val})" if reveal_dealer else f"Dealer  ({card_value(game['dealer'][0])} + ?)"
        desc = (
            f"**Your Hand  ({p_val})**\n```\n{p_cards}\n```\n"
            f"**{d_label}**\n```\n{d_cards}\n```"
        )
        if result_text:
            desc += f"\n{result_text}"
        e = embed(f"{E.CARDS}  Blackjack", desc, C.GAMES)
        e.add_field(name="Bet", value=f"`{game['bet']:,}` {E.COIN}", inline=True)
        return e

    async def _end(self, interaction, e):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=e, view=self)
        self.stop()

    @discord.ui.button(label="Hit 👊",  style=discord.ButtonStyle.primary)
    async def hit(self, interaction, button):
        game = BLACKJACK_GAMES.get(self.author_id)
        if not game:
            return
        game["player"].append(draw_card())
        total = hand_value(game["player"])
        if total > 21:
            coins = load_coins()
            user  = ensure_user(coins, self.author_id)
            e     = self.build_embed(game, result_text=f"\n{E.LOSE} **Bust!**  You went over 21 and lost **{game['bet']:,}** coins.")
            e.color = C.LOSE
            e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=False)
            BLACKJACK_GAMES.pop(self.author_id)
            return await self._end(interaction, e)
        await interaction.response.edit_message(embed=self.build_embed(game), view=self)

    @discord.ui.button(label="Stand ✋", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction, button):
        game = BLACKJACK_GAMES.get(self.author_id)
        if not game:
            return
        p_val = hand_value(game["player"])
        while hand_value(game["dealer"]) < 17:
            game["dealer"].append(draw_card())
        d_val = hand_value(game["dealer"])
        coins = load_coins()
        user  = ensure_user(coins, self.author_id)
        bet   = int(game["bet"])
        if d_val > 21 or p_val > d_val:
            user["wallet"] += bet * 2
            result = f"\n{E.WIN} **You win!**  +{bet*2:,} coins."
            color  = C.WIN
        elif d_val == p_val:
            user["wallet"] += bet
            result = f"\n🤝 **Push!**  Your **{bet:,}** coins are returned."
            color  = C.NEUTRAL
        else:
            result = f"\n{E.LOSE} **Dealer wins.**  -{bet:,} coins."
            color  = C.LOSE
        save_coins(coins)
        e = self.build_embed(game, reveal_dealer=True, result_text=result)
        e.color = color
        e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=False)
        BLACKJACK_GAMES.pop(self.author_id)
        await self._end(interaction, e)


# ─── Cog ──────────────────────────────────────────────────────────────────────

class Games(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── COIN FLIP ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="coinflip", description="Flip a coin. Bet optionally: /coinflip heads 200")
    async def coinflip(self, ctx, side: str = None, amount: str = None):
        result = random.choice(["Heads", "Tails"])
        emoji  = "🪙"

        if side is None:
            e = embed(f"{emoji}  Coin Flip", f"It landed on **{result}**!", C.GAMES)
            return await ctx.send(embed=e)

        side = side.strip().lower()
        if side not in ("heads", "tails"):
            return await ctx.send(embed=error("Coin Flip", "Choose **heads** or **tails**."))
        if amount is None:
            return await ctx.send(embed=error("Coin Flip", "Provide a bet: `/coinflip heads 100`"))

        coins  = load_coins()
        user   = ensure_user(coins, ctx.author.id)
        wallet = user["wallet"]
        bet    = wallet if amount.lower() == "all" else (int(amount) if amount.isdigit() else None)
        if bet is None:
            return await ctx.send(embed=error("Coin Flip", "Enter a number or `all`."))
        if bet <= 0:
            return await ctx.send(embed=error("Coin Flip", "Bet must be positive."))
        if wallet < bet:
            return await ctx.send(embed=error("Coin Flip", f"You only have `{wallet:,}` coins."))

        won = side.capitalize() == result
        if won:
            user["wallet"] += bet
            e = embed(f"{emoji}  {result} — Correct!", f"You called **{side}** and won **{bet:,}** coins! {E.WIN}", C.WIN)
        else:
            user["wallet"] -= bet
            e = embed(f"{emoji}  {result} — Wrong!", f"You called **{side}** but it was **{result}**. Lost **{bet:,}** coins.", C.LOSE)
        save_coins(coins)
        e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=False)
        await ctx.send(embed=e)

    # ── GAMBLE ────────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="gamble", description="Bet on red or black.")
    async def gamble(self, ctx, amount: str):
        coins  = load_coins()
        user   = ensure_user(coins, ctx.author.id)
        wallet = user["wallet"]
        bet    = wallet if amount.lower() == "all" else (int(amount) if amount.isdigit() else None)
        if bet is None:
            return await ctx.send(embed=error("Gamble", "Enter a number or `all`."))
        if bet <= 0:
            return await ctx.send(embed=error("Gamble", "Bet must be positive."))
        if wallet < bet:
            return await ctx.send(embed=error("Gamble", f"You only have `{wallet:,}` coins."))
        user["wallet"] -= bet
        save_coins(coins)
        e = embed(
            "🎰  Place Your Bet",
            f"Bet: **{bet:,}** {E.COIN}\n\nPick a colour — winner doubles their money!",
            C.GAMES,
        )
        e.add_field(name=f"{E.WALLET} Wallet (held)", value=f"`{user['wallet']:,}`", inline=False)
        view = GambleView(author_id=ctx.author.id, coins=coins, user=user, bet=bet)
        msg  = await ctx.send(embed=e, view=view)
        view.message = msg

    # ── BLACKJACK ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="blackjack", description="Play a hand of blackjack.")
    async def blackjack(self, ctx, bet: str):
        uid    = str(ctx.author.id)
        coins  = load_coins()
        user   = ensure_user(coins, uid)
        wallet = user["wallet"]
        amount = wallet if bet.lower() == "all" else (int(bet) if bet.isdigit() else None)
        if amount is None:
            return await ctx.send(embed=error("Blackjack", "Enter a number or `all`."))
        if amount <= 0:
            return await ctx.send(embed=error("Blackjack", "Bet must be positive."))
        if wallet < amount:
            return await ctx.send(embed=error("Blackjack", f"You only have `{wallet:,}` coins."))
        if uid in BLACKJACK_GAMES:
            return await ctx.send(embed=warn("Already Playing", "Finish your current game first."))
        player = [draw_card(), draw_card()]
        dealer = [draw_card(), draw_card()]
        user["wallet"] -= amount
        save_coins(coins)
        BLACKJACK_GAMES[uid] = {"player": player, "dealer": dealer, "bet": amount}
        if hand_value(player) == 21:
            while hand_value(dealer) < 17:
                dealer.append(draw_card())
            game = BLACKJACK_GAMES.pop(uid)
            view = BlackjackView(author_id=ctx.author.id)
            if hand_value(dealer) == 21:
                user["wallet"] += amount
                result = f"\n🤝 **Push!**  Both hit blackjack."
                color  = C.NEUTRAL
            else:
                user["wallet"] += amount * 2
                result = f"\n{E.WIN} **Natural Blackjack!**  +{amount*2:,} coins!"
                color  = C.WIN
            save_coins(coins)
            e = view.build_embed(game, reveal_dealer=True, result_text=result)
            e.color = color
            e.add_field(name=f"{E.WALLET} Wallet", value=f"`{user['wallet']:,}`", inline=False)
            return await ctx.send(embed=e)
        view = BlackjackView(author_id=ctx.author.id)
        await ctx.send(embed=view.build_embed(BLACKJACK_GAMES[uid]), view=view)


async def setup(bot):
    await bot.add_cog(Games(bot))
