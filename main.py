import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        # Load the scraping commands from the cogs folder
        await self.load_extension('cogs.scraper')
        # You can load more cogs here later!
        await self.tree.sync()

    async def on_ready(self):
        print('---------------------------')
        print(f'📚 Bot is online as {self.user.name}!')
        print('---------------------------')

if __name__ == "__main__":
    bot = MyBot()
    # Run the bot using the hidden token
    bot.run(TOKEN)