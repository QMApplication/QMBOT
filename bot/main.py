# main.py
import discord
from discord.ext import commands
from config import TOKEN

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.voice_states = True
INTENTS.members = True

class QMULBot(commands.Bot):
    async def setup_hook(self):
        """
        Load all cogs here.
        You’ll create these files under ./cogs/ next.
        """
        extensions = [
            # listeners first so on_message works
            "cogs.listeners",

            # core features (you’ll add these as you split)
            "cogs.economy",
            "cogs.trivia",
            "cogs.games",
            "cogs.marriage",
            "cogs.admin",
            "cogs.mc",
            "cogs.coverbot",

            # background tasks last
            "cogs.tasks",
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"[Cog] Loaded {ext}")
            except Exception as e:
                # Don’t crash on missing cogs while you’re migrating
                print(f"[Cog] Skipped {ext}: {type(e).__name__}: {e}")

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
