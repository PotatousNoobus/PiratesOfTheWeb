# import discord
# from discord.ext import commands
# import os
# from dotenv import load_dotenv
# import aiohttp
# import urllib.parse
# from keep_alive import keep_alive
# # Load the environment variables from the .env file
# load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN')

# # Setup Bot
# intents = discord.Intents.default()
# intents.message_content = True

# class MyBot(commands.Bot):
#     def __init__(self):
#         super().__init__(command_prefix='!', intents=intents)

#     async def setup_hook(self):
#         # Load the scraping commands from the cogs folder
#         await self.load_extension('cogs.scraper')
#         await self.load_extension('cogs.chatbot')
#         # You can load more cogs here later!
#         await self.tree.sync()

#     async def on_ready(self):
#         print('---------------------------')
#         print(f'📚 Bot is online as {self.user.name}!')
#         print('---------------------------')


# async def get_game_suggestions(query: str):
    
#     safe_query = urllib.parse.quote(query)
#     url = f"https://store.steampowered.com/api/storesearch/?term={safe_query}&l=english&cc=US"
    
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url) as response:
#                 if response.status == 200:
#                     data = await response.json()
                    
#                     if data.get('total', 0) > 0:
#                         # Extract just the game names from the JSON
#                         games = [item['name'] for item in data['items']]
                        
#                         # Remove duplicates while keeping the order, then return the top 5
#                         unique_games = list(dict.fromkeys(games))
#                         return unique_games[:5]
#     except Exception as e:
#         print(f"API Error: {e}")
        
#     return []

# if __name__ == "__main__":
#     bot = MyBot()
#     keep_alive()
  
#     bot.run(TOKEN)

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

    # --- NEW: SIN CITY INTRODUCTORY RESPONSE ---
    async def on_guild_join(self, guild):
        """Triggered when the bot joins a new server."""
        
        # Find the best channel to send the welcome message
        # We try the system channel first, then fall back to any channel we can talk in
        target_channel = guild.system_channel
        if not target_channel:
            target_channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)

        if target_channel:
            # Sin City: Las Vegas themed Embed
            embed = discord.Embed(
                title="🎰 **Welcome to Sin City: Las Vegas** 🎰",
                description=(
                    "**Probing the web, tailoring book/game recommendations or sneaking up to watch free movies** "
                    "You've just invited the ultimate high-roller to your server. "
                    "What happens in this chat stays in this chat... unless it's a winning book/game recommendation.\n\n"
                    "**How to play your cards right:**\n"
                    "✨ **Use** `/ask` **for your burning questions.**\n"
                    "📖 **Use** `/review` **or** `/image` **to vet your next play.**\n"
                    "🌟 **Use** `/recommend` **to let me roll the dice for you.**\n\n"
                    "📖 **Use** `/ebook` **or** `/game_torrent` ** or ** `/movie` ** or ** `/stream` ** to crack your way to entertainment.**\n"
                    "*Good luck, kid. The house is always watching and beware of the malicious depths of the World Wide Web.*"
                ),
                color=discord.Color.red() 
            )
            embed.set_footer(text="🎰 Sin City 2026 | Let the games begin.")
            
            try:
                await target_channel.send(embed=embed)
            except discord.Forbidden:
                pass # Silently fail if we don't have permission to send

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
