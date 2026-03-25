import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Setup bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user.name}!')

@bot.command()
async def search(ctx, *, game_name: str):
    """Scrapes search results, clicks into them, and grabs a specific host link."""
    
    await ctx.send(f"🔍 Searching for **{game_name}** and fetching download links. This might take a few seconds...")

    safe_name = urllib.parse.quote(game_name)
    url = f"https://www.fitgirl-repacks.site/?s={safe_name}" 

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'} 
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        await ctx.send("❌ Something went wrong trying to reach the main website.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = soup.find_all('header', class_='entry-header', limit=5) 

    if not results:
        await ctx.send(f"No results found for '{game_name}'.")
        return

    message_lines = [f"**Top results for '{game_name}':**\n"]
    
    for header in results:
        h1_tag = header.find('h1', class_='entry-title')
        
        if h1_tag:
            a_tag = h1_tag.find('a')
            
            if a_tag:
                title = a_tag.text.strip()
                game_page_link = a_tag.get('href')
                
                # ==========================================
                # Step E: THE NEW HOST-SPECIFIC CRAWLER LOGIC
                # ==========================================
                try:
                    inner_response = requests.get(game_page_link, headers=headers, timeout=10)
                    inner_soup = BeautifulSoup(inner_response.text, 'html.parser')
                    
                    # 👇 CHANGE THIS WORD TO GRAB A DIFFERENT LINK 👇
                    # Examples: "RuTor", "OneDrive", "DataNodes", "Tapochek"
                    target_host = "1337x" 
                    
                    # This tells the bot to find the first <a> tag that contains your target_host text
                    target_link_tag = inner_soup.find('a', string=lambda text: text and target_host.lower() in text.lower())
                    
                    if target_link_tag:
                        final_download_link = target_link_tag.get('href')
                        message_lines.append(f"🎮 **{title}**\n🔗 {target_host}: <{final_download_link}>\n")
                    else:
                        message_lines.append(f"🎮 **{title}**\n❌ *Could not find a {target_host} link on this page.*\n")
                        
                except Exception as e:
                    message_lines.append(f"🎮 **{title}**\n⚠️ *Error loading the game page.*\n")

    if len(message_lines) == 1: 
        await ctx.send("Found the articles, but couldn't extract the titles or links!")
    else:
        final_message = "\n".join(message_lines)
        
        if len(final_message) > 2000:
            await ctx.send("⚠️ The results were too long for one Discord message! Try being more specific with your search.")
        else:
            await ctx.send(final_message)

# Run the bot
if __name__ == "__main__":
    bot.run('MTQ4Mzg2NTM4NjY4MzIwNzc0MQ.GdpCXE.TkMgv3gjVprPoNIHtZ5TJa5FexkTCCWC9Zv2gg')