import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiohttp
import urllib.parse
from keep_alive import keep_alive
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
        await self.load_extension('cogs.chatbot')
        # You can load more cogs here later!
        await self.tree.sync()

    async def on_ready(self):
        print('---------------------------')
        print(f'📚 Bot is online as {self.user.name}!')
        print('---------------------------')


async def get_game_suggestions(query: str):
    
    safe_query = urllib.parse.quote(query)
    url = f"https://store.steampowered.com/api/storesearch/?term={safe_query}&l=english&cc=US"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('total', 0) > 0:
                        # Extract just the game names from the JSON
                        games = [item['name'] for item in data['items']]
                        
                        # Remove duplicates while keeping the order, then return the top 5
                        unique_games = list(dict.fromkeys(games))
                        return unique_games[:5]
    except Exception as e:
        print(f"API Error: {e}")
        
    return []

if __name__ == "__main__":
    bot = MyBot()
    keep_alive()
  
    bot.run(TOKEN)
