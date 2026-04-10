import discord
from discord.ext import commands
import urllib.parse
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
    """Searches for a book on Anna's Archive and returns up to 3 slow download links."""
    
    await ctx.send(f"📚 Searching for **{book_name.title()}** on Anna's Archive...")
    
    safe_name = urllib.parse.quote_plus(book_name)
    base_url = "https://annas-archive.gd"
    search_url = f"{base_url}/search?q={safe_name}"
    
    search_selector = "a[href^='/md5/']"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Step 1: Search page
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector(search_selector, timeout=15000)
            
            # Find first relevant result
            results = page.locator(search_selector)
            count = await results.count()
            
            chosen_link = None
            chosen_title = None
            
            for i in range(count):
                item = results.nth(i)
                link = await item.get_attribute("href")
                title = await item.inner_text()
                if book_name.lower() in title.lower():
                    chosen_link = link
                    chosen_title = title
                    break
            
            if not chosen_link:
                await ctx.send(f"Sorry, I couldn’t find a relevant match for **{book_name.title()}**.")
                await browser.close()
                return
            
            # Step 2: Go to book detail page
            detail_url = f"{base_url}{chosen_link}"
            await page.goto(detail_url, wait_until="domcontentloaded", timeout=30000)
            
            # Step 3: Extract slow download links from the SECOND div.mb-4
            slow_div_selector = "div.mb-4:nth-of-type(2) li a"
            await page.wait_for_selector(slow_div_selector, timeout=15000)
            
            slow_items = page.locator(slow_div_selector)
            dl_count = await slow_items.count()
            
            slow_links = []
            for i in range(min(dl_count, 3)):  # limit to top 3
                dl_item = slow_items.nth(i)
                dl_href = await dl_item.get_attribute("href")
                if dl_href:
                    if dl_href.startswith("/"):
                        dl_href = f"{base_url}{dl_href}"
                    slow_links.append(dl_href)
            
            if slow_links:
                message = f"**Slow download options for '{chosen_title.strip()}':**\n\n"
                for idx, link in enumerate(slow_links, start=1):
                    message += f"🐢 Slow Download {idx}: <{link}>\n"
                await ctx.send(message)
            else:
                await ctx.send(f"Found the book page for **{book_name.title()}**, but no slow download links were detected.")
        
        except Exception as e:
            await page.screenshot(path="debug_ebook_error.png", full_page=True)
            await ctx.send(f"⚠️ An unexpected error occurred. Screenshot saved as `debug_ebook_error.png`.")
            print(f"Playwright Error in ebook command: {e}")
            
        finally:
            await browser.close()






@bot.command()
async def stream(ctx, *, movie_name: str):
    
    safe_name = urllib.parse.quote_plus(movie_name)
    base_url = "https://westream.to/search?keyword=" 
    final_link = base_url + safe_name
    
    await ctx.send(f"🍿 Here is the stream link for **{movie_name.title()}**:\n{final_link}")

@bot.command()
async def top10(ctx, *, movie_name: str):
    """Physically types into the search bar and grabs the top 10 dynamic links."""
    
    await ctx.send(f"🔍 Firing up the invisible browser to search for **{movie_name.title()}**...")
    
    search_page_url = "https://thepiratebay.org/index.html" 
    search_bar_selector = "input[name='q']"
    results_selector = "div.browse section.col-center ol#torrents li.list-entry span.list-item.item-name.item-title a"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(search_page_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_selector(search_bar_selector, timeout=10000)
            await page.fill(search_bar_selector, movie_name)
            await page.keyboard.press("Enter")
            
            try:
                await page.wait_for_selector(results_selector, timeout=15000)
            except:
                await page.screenshot(path="debug_after_enter.png", full_page=True)
                await ctx.send(f"❌ I typed '{movie_name}' and hit Enter, but the list never appeared. I saved a `debug_after_enter.png` so we can see what happened!")
                await browser.close()
                return
                
            total_elements = await page.locator(results_selector).count()
            limit = min(10, total_elements)
            
            message_lines = [f"**Top {limit} results for '{movie_name.title()}':**\n"]
            
            for i in range(limit):
                element = page.locator(results_selector).nth(i)
                title = await element.inner_text()
                link = await element.get_attribute('href')
                
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
    bot.run('BOT_TOKEN')
