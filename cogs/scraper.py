import discord
from discord.ext import commands
from discord import app_commands
import urllib.parse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class Scraping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot        

        

    @app_commands.command()
    async def stream(self, interaction: discord.Interaction, movie_name: str):
        await interaction.response.defer()
        safe_name = urllib.parse.quote_plus(movie_name)
        
        # Build the exact link using the westream.to URL structure
        base_url = "https://westream.to/search?keyword=" 
        final_link = base_url + safe_name
        
        await interaction.followup.send(f"🍿 Here is the stream link for **{movie_name.title()}**:\n{final_link}")

        

    @app_commands.command()
    async def movie(self, interaction: discord.Interaction, movie_name: str):
        """Physically types into the search bar and grabs the top 10 dynamic links."""
        await interaction.response.defer()
    
        await interaction.followup.send(f"🔍 Firing up the invisible browser to search for **{movie_name.title()}**...")
        
        
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
                    await page.screenshot(path="debug_after_enter.png", full_page=True)
                    await interaction.followup.send(f"❌ I typed '{movie_name}' and hit Enter, but the list never appeared. I saved a `debug_after_enter.png` so we can see what happened!")
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
                await interaction.followup.send(final_message)
                
            except Exception as e:
                print(f"Playwright Error: {e}")
                await interaction.followup.send("⚠️ The browser hit a snag or timed out.")
                
            finally:
                await browser.close()
        

    @app_commands.command()
    async def game(self, interaction: discord.Interaction, game_name: str):
        """Scrapes search results, clicks into them, and grabs a specific host link."""
        await interaction.response.defer()
        
        await interaction.followup.send(f"🔍 Searching for **{game_name}** and fetching download links. This might take a few seconds...")

        safe_name = urllib.parse.quote(game_name)
        url = f"https://www.fitgirl-repacks.site/?s={safe_name}" 

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'} 
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            await interaction.followup.send("❌ Something went wrong trying to reach the main website.")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = soup.find_all('header', class_='entry-header', limit=5) 

        if not results:
            await interaction.followup.send(f"No results found for '{game_name}'.")
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
            await interaction.followup.send("Found the articles, but couldn't extract the titles or links!")
        else:
            final_message = "\n".join(message_lines)
            
            if len(final_message) > 2000:
                await interaction.followup.send("⚠️ The results were too long for one Discord message! Try being more specific with your search.")
            else:
                await interaction.followup.send(final_message)

    @app_commands.command()
    async def ebook(self, interaction:discord.Interaction, book_name: str):
        
        await interaction.response.defer()
        
        await interaction.followup.send(f"📚 Searching for **{book_name.title()}** ...")
        
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
                    await interaction.followup.send(f"Sorry, I couldn’t find a relevant match for **{book_name.title()}**.")
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
                    message = f"**Download options for '{chosen_title.strip()}':**\n\n"
                    for idx, link in enumerate(slow_links, start=1):
                        message += f"🐢 Slow Download {idx}: <{link}>\n"
                    await interaction.followup.send(message)
                else:
                    await interaction.followup.send(f"Found the book page for **{book_name.title()}**, but no download links were detected.")
            
            except Exception as e:
                await page.screenshot(path="debug_ebook_error.png", full_page=True)
                await interaction.followup.send(f"⚠️ An unexpected error occurred. Screenshot saved as `debug_ebook_error.png`.")
                print(f"Playwright Error in ebook command: {e}")
                
            finally:
                await browser.close()

async def setup(bot):
    await bot.add_cog(Scraping(bot))