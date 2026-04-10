import discord
from discord.ext import commands
import urllib.parse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('---------------------------')
    print(f'📚 Bot is online as {bot.user.name}!')
    print('---------------------------')

@bot.command()
async def ebook(ctx, *, book_name: str):
    """Searches for an eBook on oceanofpdf.com and returns the top 5 results."""
    
    await ctx.send(f"📚 Searching for **{book_name.title()}** on OceanOfPDF...")
    
    safe_name = urllib.parse.quote_plus(book_name)
    search_url = f"https://oceanofpdf.com/?s={safe_name}"
    
    try:
        response = requests.get(search_url, timeout=15)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all the article entries for books
        results = soup.find_all('article', class_='post-item', limit=5)
        
        if not results:
            await ctx.send(f"Sorry, I couldn't find any results for **{book_name.title()}**.")
            return

        message_lines = [f"**Top 5 results for '{book_name.title()}':**\n"]
        
        for i, result in enumerate(results):
            title_element = result.find('h2', class_='post-title').find('a')
            title = title_element.get_text(strip=True)
            link = title_element['href']
            
            message_lines.append(f"{i+1}. **{title}**\n🔗 <{link}>\n")
            
        final_message = "\n".join(message_lines)
        await ctx.send(final_message)
        
    except requests.exceptions.RequestException as e:
        await ctx.send(f"⚠️ An error occurred while trying to connect to OceanOfPDF: {e}")
    except Exception as e:
        await ctx.send(f"⚠️ An unexpected error occurred: {e}")

@bot.command()
async def stream(ctx, *, movie_name: str):
    
    # quote_plus automatically turns spaces into '+' and handles special characters safely
    safe_name = urllib.parse.quote_plus(movie_name)
    
    # Build the exact link using the westream.to URL structure
    base_url = "https://westream.to/search?keyword=" 
    final_link = base_url + safe_name
    
    await ctx.send(f"🍿 Here is the stream link for **{movie_name.title()}**:\n{final_link}")

@bot.command()
async def movie(ctx, *, movie_name: str):
    """Physically types into the search bar and grabs the top 10 dynamic links."""
    
    await ctx.send(f"🔍 Firing up the invisible browser to search for **{movie_name.title()}**...")
    
    # 👇 1. PASTE YOUR EXACT SEARCH PAGE URL HERE 👇
    # (The URL of the page that has the empty search box we found)
    search_page_url = "https://thepiratebay.org/index.html" 
    
    # 2. The exact selectors we hunted down!
    search_bar_selector = "input[name='q']"
    results_selector = "div.browse section.col-center ol#torrents li.list-entry span.list-item.item-name.item-title a"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Step 1: Go to the page with the search box
            await page.goto(search_page_url, wait_until="domcontentloaded", timeout=30000)
            
            # Step 2: Wait for the search box, click it, type the movie, and hit Enter
            await page.wait_for_selector(search_bar_selector, timeout=10000)
            await page.fill(search_bar_selector, movie_name)
            await page.keyboard.press("Enter")
            
            # Step 3: Wait for the dynamic list to actually load on the screen
            try:
                await page.wait_for_selector(results_selector, timeout=15000)
            except:
                # 👇 WE ADDED THE SCREENSHOT DEBUGGER BACK IN 👇
                await page.screenshot(path="debug_after_enter.png", full_page=True)
                await ctx.send(f"❌ I typed '{movie_name}' and hit Enter, but the list never appeared. I saved a `debug_after_enter.png` so we can see what happened!")
                await browser.close()
                return
                
            # Step 4: Count the results and limit to 10
            total_elements = await page.locator(results_selector).count()
            limit = min(10, total_elements)
            
            message_lines = [f"**Top {limit} results for '{movie_name.title()}':**\n"]
            
            # Step 5: Loop through them and pull the text and href attributes
            for i in range(limit):
                element = page.locator(results_selector).nth(i)
                title = await element.inner_text()
                link = await element.get_attribute('href')
                
                # Fix relative links if needed
                if link and link.startswith('/'):
                    parsed_uri = urllib.parse.urlparse(search_page_url)
                    base = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
                    link = base + link
                    
                message_lines.append(f"{i+1}. **{title.strip()}**\n🔗 <{link}>\n")
                
            final_message = "\n".join(message_lines)
            await ctx.send(final_message)
            
        except Exception as e:
            print(f"Playwright Error: {e}")
            await ctx.send("⚠️ The browser hit a snag or timed out.")
            
        finally:
            await browser.close()

@bot.command()
async def game(ctx, *, game_name: str):
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

if __name__ == "__main__":
    # Remember to replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token
    bot.run('MTQ4Mzg2NTM4NjY4MzIwNzc0MQ.GdpCXE.TkMgv3gjVprPoNIHtZ5TJa5FexkTCCWC9Zv2gg')
