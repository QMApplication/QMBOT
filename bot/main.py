# bot/main.py
import discord
from discord.ext import commands
from bot.config import TOKEN

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.voice_states = True
INTENTS.members = True

class QMULBot(commands.Bot):
    async def setup_hook(self):
        # Load cogs
        extensions = [
            "bot.cogs.listeners",
            "bot.cogs.economy",
            "bot.cogs.trivia",
            "bot.cogs.marriage",
            "bot.cogs.games",
            "bot.cogs.admin",
            "bot.cogs.mc",
            "bot.cogs.coverbot",
            "bot.cogs.tasks",
        ]
        for ext in extensions:
            await self.load_extension(ext)

bot = QMULBot(command_prefix="!", intents=INTENTS)

@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready!")

def main():
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN not set in environment.")
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
