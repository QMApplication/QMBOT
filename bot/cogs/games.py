import random
import discord
from discord.ext import commands

from storage import load_coins, save_coins


EMBED_COLOR = discord.Color.from_rgb(34, 40, 49)


def ensure_user(coins: dict, user_id: int | str) -> dict:
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0
        }

    return coins[uid]


BLACKJACK_GAMES: dict[str, dict] = {}


def draw_card() -> int:
    cards = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
    return random.choice(cards)


def hand_value(hand: list[int]) -> int:
    total = sum(hand)
    aces = hand.count(11)

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # COINFLIP
    # -------------------------

    @commands.hybrid_command(
        name="coinflip",
        description="Flip a coin."
    )
    async def coinflip(self, ctx: commands.Context):
        result = random.choice(["Heads", "Tails"])

        embed = discord.Embed(
            title="Coin Flip",
            description=f"Result: **{result}**",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

    # -------------------------
    # GAMBLE
    # -------------------------

    @commands.hybrid_command(
        name="gamble",
        description="Gamble coins for a 50/50 chance."
    )
    async def gamble(self, ctx: commands.Context, amount: str):
        coins = load_coins()
        user = ensure_user(coins, ctx.author.id)

        wallet = int(user["wallet"])

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

        win = random.choice([True, False])

        if win:
            winnings = bet * 2
            user["wallet"] += winnings

            embed = discord.Embed(
                title="Gamble Result",
                description=f"You won **{winnings}** coins.",
                color=EMBED_COLOR
            )
            embed.add_field(name="Wallet", value=f"`{user['wallet']}`", inline=False)
        else:
            embed = discord.Embed(
                title="Gamble Result",
                description=f"You lost **{bet}** coins.",
                color=EMBED_COLOR
            )
            embed.add_field(name="Wallet", value=f"`{user['wallet']}`", inline=False)

        save_coins(coins)
        await ctx.send(embed=embed)

    # -------------------------
    # BLACKJACK START
    # -------------------------

    @commands.hybrid_command(
        name="blackjack",
        description="Start a blackjack game."
    )
    async def blackjack(self, ctx: commands.Context, bet: str):
        uid = str(ctx.author.id)

        coins = load_coins()
        user = ensure_user(coins, uid)

        wallet = int(user["wallet"])

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

        player_total = hand_value(player)

        if player_total == 21:
            dealer_total = hand_value(dealer)

            while dealer_total < 17:
                dealer.append(draw_card())
                dealer_total = hand_value(dealer)

            if dealer_total != 21:
                winnings = amount * 2
                user["wallet"] += winnings
                result_msg = f"Natural blackjack. You won **{winnings}** coins."
                color = EMBED_COLOR
            else:
                user["wallet"] += amount
                result_msg = f"Push. Both hands hit blackjack. Your **{amount}** coins were returned."
                color = EMBED_COLOR

            save_coins(coins)
            del BLACKJACK_GAMES[uid]

            embed = discord.Embed(
                title="Blackjack Result",
                description=(
                    f"Your hand: `{player}`  ({player_total})\n"
                    f"Dealer hand: `{dealer}`  ({dealer_total})\n\n"
                    f"{result_msg}"
                ),
                color=color
            )
            embed.add_field(name="Wallet", value=f"`{user['wallet']}`", inline=False)
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="Blackjack",
            description=(
                f"Your hand: `{player}`  ({player_total})\n"
                f"Dealer hand: `[{dealer[0]}, ?]`\n\n"
                "Use `hit` or `stand`."
            ),
            color=EMBED_COLOR
        )
        embed.add_field(name="Bet", value=f"`{amount}`", inline=False)

        await ctx.send(embed=embed)

    # -------------------------
    # HIT
    # -------------------------

    @commands.hybrid_command(
        name="hit",
        description="Draw another card in blackjack."
    )
    async def hit(self, ctx: commands.Context):
        uid = str(ctx.author.id)

        if uid not in BLACKJACK_GAMES:
            return await ctx.send("No blackjack game running.")

        game = BLACKJACK_GAMES[uid]
        game["player"].append(draw_card())

        value = hand_value(game["player"])

        if value > 21:
            busted_hand = list(game["player"])
            bet = int(game["bet"])
            del BLACKJACK_GAMES[uid]

            embed = discord.Embed(
                title="Blackjack Result",
                description=(
                    f"Your hand: `{busted_hand}`  ({value})\n\n"
                    f"Bust. You lost **{bet}** coins."
                ),
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="Blackjack",
            description=(
                f"Your hand: `{game['player']}`  ({value})\n\n"
                "Use `hit` or `stand`."
            ),
            color=EMBED_COLOR
        )

        await ctx.send(embed=embed)

    # -------------------------
    # STAND
    # -------------------------

    @commands.hybrid_command(
        name="stand",
        description="Stand in blackjack and let the dealer play."
    )
    async def stand(self, ctx: commands.Context):
        uid = str(ctx.author.id)

        if uid not in BLACKJACK_GAMES:
            return await ctx.send("No blackjack game running.")

        game = BLACKJACK_GAMES[uid]

        player_hand = list(game["player"])
        dealer_hand = list(game["dealer"])
        bet = int(game["bet"])

        player_val = hand_value(player_hand)

        while hand_value(dealer_hand) < 17:
            dealer_hand.append(draw_card())

        dealer_val = hand_value(dealer_hand)

        coins = load_coins()
        user = ensure_user(coins, uid)

        if dealer_val > 21 or player_val > dealer_val:
            winnings = bet * 2
            user["wallet"] += winnings
            msg = f"You won **{winnings}** coins."
        elif player_val == dealer_val:
            user["wallet"] += bet
            msg = f"Push. Your **{bet}** coins were returned."
        else:
            msg = "Dealer wins."

        save_coins(coins)
        del BLACKJACK_GAMES[uid]

        embed = discord.Embed(
            title="Blackjack Result",
            description=(
                f"Your hand: `{player_hand}`  ({player_val})\n"
                f"Dealer hand: `{dealer_hand}`  ({dealer_val})\n\n"
                f"{msg}"
            ),
            color=EMBED_COLOR
        )
        embed.add_field(name="Wallet", value=f"`{user['wallet']}`", inline=False)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
