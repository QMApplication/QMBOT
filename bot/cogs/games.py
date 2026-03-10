import discord
from discord.ext import commands
import random

from storage import load_coins, save_coins


def ensure_user(user_id):
    coins = load_coins()
    uid = str(user_id)

    if uid not in coins:
        coins[uid] = {
            "wallet": 100,
            "bank": 0
        }
        save_coins(coins)

    return coins


# active blackjack sessions
BLACKJACK_GAMES = {}


def draw_card():
    cards = [2,3,4,5,6,7,8,9,10,10,10,10,11]
    return random.choice(cards)


def hand_value(hand):

    total = sum(hand)

    while total > 21 and 11 in hand:
        hand[hand.index(11)] = 1
        total = sum(hand)

    return total


class Games(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -------------------------
    # COINFLIP
    # -------------------------

    @commands.command()
    async def coinflip(self, ctx):

        result = random.choice(["Heads", "Tails"])

        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"The coin landed on **{result}**",
            color=discord.Color.blue()
        )

        await ctx.send(embed=embed)

    # -------------------------
    # GAMBLE
    # -------------------------

    @commands.command()
    async def gamble(self, ctx, amount: int):

        coins = ensure_user(ctx.author.id)
        user = coins[str(ctx.author.id)]

        if amount <= 0 or user["wallet"] < amount:
            return await ctx.send("Invalid bet.")

        user["wallet"] -= amount

        win = random.choice([True, False])

        if win:

            winnings = amount * 2
            user["wallet"] += winnings

            msg = f"🎉 You won **{winnings}** coins!"

        else:

            msg = f"💀 You lost **{amount}** coins."

        save_coins(coins)

        await ctx.send(msg)

    # -------------------------
    # BLACKJACK START
    # -------------------------

    @commands.command()
    async def blackjack(self, ctx, bet: int):

        uid = str(ctx.author.id)

        coins = ensure_user(uid)
        user = coins[uid]

        if bet <= 0:
            return await ctx.send("Invalid bet.")

        if user["wallet"] < bet:
            return await ctx.send("Not enough coins.")

        if uid in BLACKJACK_GAMES:
            return await ctx.send("You already have a game running.")

        player = [draw_card(), draw_card()]
        dealer = [draw_card(), draw_card()]

        user["wallet"] -= bet
        save_coins(coins)

        BLACKJACK_GAMES[uid] = {
            "player": player,
            "dealer": dealer,
            "bet": bet
        }

        embed = discord.Embed(
            title="🃏 Blackjack",
            description=(
                f"Your hand: {player} (**{hand_value(player)}**)\n"
                f"Dealer: [{dealer[0]}, ?]\n\n"
                "Use `!hit` or `!stand`"
            )
        )

        await ctx.send(embed=embed)

    # -------------------------
    # HIT
    # -------------------------

    @commands.command()
    async def hit(self, ctx):

        uid = str(ctx.author.id)

        if uid not in BLACKJACK_GAMES:
            return await ctx.send("No blackjack game running.")

        game = BLACKJACK_GAMES[uid]

        game["player"].append(draw_card())

        value = hand_value(game["player"])

        if value > 21:

            del BLACKJACK_GAMES[uid]

            return await ctx.send(
                f"💥 Bust! Your hand: {game['player']} (**{value}**)"
            )

        await ctx.send(
            f"Your hand: {game['player']} (**{value}**)"
        )

    # -------------------------
    # STAND
    # -------------------------

    @commands.command()
    async def stand(self, ctx):

        uid = str(ctx.author.id)

        if uid not in BLACKJACK_GAMES:
            return await ctx.send("No blackjack game running.")

        game = BLACKJACK_GAMES[uid]

        player_val = hand_value(game["player"])
        dealer = game["dealer"]

        while hand_value(dealer) < 17:
            dealer.append(draw_card())

        dealer_val = hand_value(dealer)

        coins = ensure_user(uid)
        user = coins[uid]

        bet = game["bet"]

        if dealer_val > 21 or player_val > dealer_val:

            winnings = bet * 2
            user["wallet"] += winnings

            msg = f"🎉 You win **{winnings}** coins!"

        elif player_val == dealer_val:

            user["wallet"] += bet
            msg = "🤝 Push. Bet returned."

        else:

            msg = "💀 Dealer wins."

        save_coins(coins)

        del BLACKJACK_GAMES[uid]

        embed = discord.Embed(
            title="Blackjack Result",
            description=(
                f"Your hand: {game['player']} (**{player_val}**)\n"
                f"Dealer hand: {dealer} (**{dealer_val}**)\n\n"
                f"{msg}"
            )
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Games(bot))
