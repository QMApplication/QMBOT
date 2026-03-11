import random
import discord
from discord.ext import commands

from storage import load_coins, save_coins


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)

BLACKJACK_GAMES: dict[str, dict] = {}


def ensure_user(coins: dict, user_id: int | str) -> dict:
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0
        }

    return coins[uid]


# -------------------------
# CARD LOGIC
# -------------------------

def draw_card() -> str:
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    suits = ["♠", "♥", "♦", "♣"]
    return f"{random.choice(ranks)}{random.choice(suits)}"


def card_value(card: str) -> int:
    rank = card[:-1]

    if rank in {"J", "Q", "K"}:
        return 10
    if rank == "A":
        return 11
    return int(rank)


def hand_value(hand: list[str]) -> int:
    total = sum(card_value(card) for card in hand)
    aces = sum(1 for card in hand if card[:-1] == "A")

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


# -------------------------
# CARD RENDERING
# -------------------------

def render_card(card: str) -> list[str]:
    rank = card[:-1]
    suit = card[-1]

    middle = rank.center(3)

    return [
        "┌─────┐",
        f"│{suit:<5}│",
        f"│ {middle} │",
        f"│{suit:>5}│",
        "└─────┘",
    ]


def render_hidden_card() -> list[str]:
    return [
        "┌─────┐",
        "│     │",
        "│  ♔  │",
        "│     │",
        "└─────┘",
    ]


def combine_cards(cards: list[str], hide_second: bool = False) -> str:

    rendered_cards = []

    for i, card in enumerate(cards):

        if hide_second and i == 1:
            rendered_cards.append(render_hidden_card())
        else:
            rendered_cards.append(render_card(card))

    lines = []

    for row in range(5):
        lines.append("  ".join(card[row] for card in rendered_cards))

    return "\n".join(lines)


def wrap_cards(cards: list[str], hide_second=False, per_row=3):

    rows = []

    for i in range(0, len(cards), per_row):

        chunk = cards[i:i + per_row]

        if hide_second and i == 0:
            rows.append(combine_cards(chunk, hide_second=True))
        else:
            rows.append(combine_cards(chunk))

    return "\n\n".join(rows)


# -------------------------
# GAMBLE VIEW
# -------------------------

class GambleView(discord.ui.View):

    def __init__(self, *, author_id, coins, user, bet):
        super().__init__(timeout=20)
        self.author_id = author_id
        self.coins = coins
        self.user = user
        self.bet = bet

    async def interaction_check(self, interaction):

        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This gamble isn't for you.",
                ephemeral=True
            )
            return False

        return True

    async def on_timeout(self):

        for child in self.children:
            child.disabled = True

    async def _finish(self, interaction, choice):

        result = random.choice(["red", "black"])

        if choice == result:

            winnings = self.bet * 2
            self.user["wallet"] += winnings

            lines = [
                "Result",
                "------",
                f"Choice  | {choice.title()}",
                f"Spin    | {result.title()}",
                f"Win     | +{winnings}",
                f"Wallet  | {self.user['wallet']}",
            ]

        else:

            lines = [
                "Result",
                "------",
                f"Choice  | {choice.title()}",
                f"Spin    | {result.title()}",
                f"Lose    | -{self.bet}",
                f"Wallet  | {self.user['wallet']}",
            ]

        save_coins(self.coins)

        embed = discord.Embed(
            title="Gamble",
            description="```text\n" + "\n".join(lines) + "\n```",
            color=EMBED_COLOR
        )

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Red", style=discord.ButtonStyle.danger)
    async def red_button(self, interaction, button):
        await self._finish(interaction, "red")

    @discord.ui.button(label="Black", style=discord.ButtonStyle.secondary)
    async def black_button(self, interaction, button):
        await self._finish(interaction, "black")


# -------------------------
# BLACKJACK VIEW
# -------------------------

class BlackjackView(discord.ui.View):

    def __init__(self, *, author_id):
        super().__init__(timeout=60)
        self.author_id = str(author_id)

    async def interaction_check(self, interaction):

        if str(interaction.user.id) != self.author_id:
            await interaction.response.send_message(
                "This blackjack game isn't for you.",
                ephemeral=True
            )
            return False

        return True

    async def on_timeout(self):

        for child in self.children:
            child.disabled = True

    def build_embed(self, game, reveal_dealer=False, result_text=None):

        player = game["player"]
        dealer = game["dealer"]

        player_total = hand_value(player)
        dealer_total = hand_value(dealer)

        player_cards = wrap_cards(player)
        dealer_cards = wrap_cards(dealer, hide_second=not reveal_dealer)

        if reveal_dealer:
            dealer_label = f"Dealer Hand ({dealer_total})"
        else:
            dealer_label = f"Dealer Hand ({card_value(dealer[0])}+?)"

        desc = (
            f"**Your Hand ({player_total})**\n"
            f"```text\n{player_cards}\n```\n"
            f"**{dealer_label}**\n"
            f"```text\n{dealer_cards}\n```"
        )

        if result_text:
            desc += f"\n{result_text}"

        embed = discord.Embed(
            title="Blackjack",
            description=desc,
            color=EMBED_COLOR
        )

        embed.add_field(name="Bet", value=f"`{game['bet']}`")

        return embed

    async def finish_game(self, interaction, embed):

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)

        self.stop()

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit_button(self, interaction, button):

        game = BLACKJACK_GAMES.get(self.author_id)

        if not game:
            return

        game["player"].append(draw_card())

        player_total = hand_value(game["player"])

        if player_total > 21:

            coins = load_coins()
            user = ensure_user(coins, self.author_id)

            embed = self.build_embed(
                game,
                result_text=f"**Bust.** You lost **{game['bet']}** coins."
            )

            embed.add_field(
                name="¢ Wallet",
                value=f"`{user['wallet']}`",
                inline=False
            )

            BLACKJACK_GAMES.pop(self.author_id)

            return await self.finish_game(interaction, embed)

        embed = self.build_embed(game)

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand_button(self, interaction, button):

        game = BLACKJACK_GAMES.get(self.author_id)

        if not game:
            return

        player_val = hand_value(game["player"])

        while hand_value(game["dealer"]) < 17:
            game["dealer"].append(draw_card())

        dealer_val = hand_value(game["dealer"])

        coins = load_coins()
        user = ensure_user(coins, self.author_id)

        bet = int(game["bet"])

        if dealer_val > 21 or player_val > dealer_val:

            winnings = bet * 2
            user["wallet"] += winnings

            result = f"**You won {winnings} coins.**"

        elif dealer_val == player_val:

            user["wallet"] += bet

            result = f"**Push.** Your **{bet}** coins were returned."

        else:

            result = "**Dealer wins.**"

        save_coins(coins)

        embed = self.build_embed(
            game,
            reveal_dealer=True,
            result_text=result
        )

        embed.add_field(
            name="¢ Wallet",
            value=f"`{user['wallet']}`",
            inline=False
        )

        BLACKJACK_GAMES.pop(self.author_id)

        await self.finish_game(interaction, embed)


# -------------------------
# COMMANDS
# -------------------------

class Games(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="coinflip",
        description="Flip a coin."
    )
    async def coinflip(self, ctx):

        result = random.choice(["Heads", "Tails"])

        embed = discord.Embed(
            title="Coin Flip",
            description=f"Result: **{result}**",
            color=EMBED_COLOR
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="gamble",
        description="Bet on red or black."
    )
    async def gamble(self, ctx, amount: str):

        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        wallet = user["wallet"]

        if amount.lower() == "all":
            bet = wallet
        else:

            if not amount.isdigit():
                return await ctx.send("Enter a number or `all`.")

            bet = int(amount)

        if bet <= 0:
            return await ctx.send("Invalid bet.")

        if wallet < bet:
            return await ctx.send("Not enough coins.")

        user["wallet"] -= bet
        save_coins(coins)

        embed = discord.Embed(
            title="Place Your Bet",
            description=f"Bet: **{bet}** coins\n\nChoose **Red** or **Black**.",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="¢ Wallet",
            value=f"`{user['wallet']}`",
            inline=False
        )

        view = GambleView(
            author_id=ctx.author.id,
            coins=coins,
            user=user,
            bet=bet
        )

        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="blackjack",
        description="Start a blackjack game."
    )
    async def blackjack(self, ctx, bet: str):

        uid = str(ctx.author.id)

        coins = load_coins()
        user = ensure_user(coins, uid)

        wallet = user["wallet"]

        if bet.lower() == "all":
            amount = wallet
        else:

            if not bet.isdigit():
                return await ctx.send("Enter a number or `all`.")

            amount = int(bet)

        if amount <= 0:
            return await ctx.send("Invalid bet.")

        if wallet < amount:
            return await ctx.send("Not enough coins.")

        if uid in BLACKJACK_GAMES:
            return await ctx.send("You already have a game running.")

        player = [draw_card(), draw_card()]
        dealer = [draw_card(), draw_card()]

        user["wallet"] -= amount
        save_coins(coins)

        BLACKJACK_GAMES[uid] = {
            "player": player,
            "dealer": dealer,
            "bet": amount
        }

        view = BlackjackView(author_id=ctx.author.id)

        embed = view.build_embed(BLACKJACK_GAMES[uid])

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Games(bot))
