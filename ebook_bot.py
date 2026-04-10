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
    print(f'📚 eBook & 🍿 Movie Bot is online as {bot.user.name}!')
    print('---------------------------')

@bot.command()
async def ebook(ctx, *, book_name: str):
    """Searches for an eBook on oceanofpdf.com and returns the top 5 results."""
    
    await ctx.send(f"📚 Searching for **{book_name.title()}** on OceanOfPDF...")
    
    safe_name = urllib.parse.quote_plus(book_name)
    search_url = f"https://oceanofpdf.com/?s={safe_name}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=15)
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
async def top10(ctx, *, movie_name: str):
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

if __name__ == "__main__":
    # Remember to replace 'YOUR_BOT_TOKEN_HERE' with your actual bot token
    bot.run('YOUR_BOT_TOKEN_HERE')
