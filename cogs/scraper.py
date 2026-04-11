import discord
from discord.ext import commands
from discord import app_commands
import urllib.parse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import os
from google import genai

class GameSelectionView(discord.ui.View):
    def __init__(self, game_options):
        super().__init__(timeout=60) 
        
        for game in game_options[:5]: 
            button = discord.ui.Button(label=game.strip()[:80], style=discord.ButtonStyle.primary)
            button.callback = self.make_callback(game.strip())
            self.add_item(button)

    def make_callback(self, selected_game):
        async def button_callback(interaction: discord.Interaction):
            for child in self.children:
                child.disabled = True
            
            await interaction.response.edit_message(content=f"🔍 Excellent choice. Fetching links for **{selected_game}**...", view=self)

            safe_name = urllib.parse.quote(selected_game)
            url = f"https://www.fitgirl-repacks.site/?s={safe_name}" 

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'} 
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    await interaction.followup.send("❌ Something went wrong trying to reach the main website.")
                    return

                soup = BeautifulSoup(response.text, 'html.parser')
                results = soup.find_all('header', class_='entry-header', limit=5) 

                if not results:
                    await interaction.followup.send(f"No results found for '{selected_game}'.")
                    return

                message_lines = [f"**Top results for '{selected_game}':**\n"]
                
                for header in results:
                    h1_tag = header.find('h1', class_='entry-title')
                    if h1_tag and h1_tag.find('a'):
                        a_tag = h1_tag.find('a')
                        title = a_tag.text.strip()
                        game_page_link = a_tag.get('href')
                        
                        try:
                            inner_response = requests.get(game_page_link, headers=headers, timeout=10)
                            inner_soup = BeautifulSoup(inner_response.text, 'html.parser')
                            
                            target_host = "1337x" 
                            target_link_tag = inner_soup.find('a', string=lambda text: text and target_host.lower() in text.lower())
                            
                            if target_link_tag:
                                final_download_link = target_link_tag.get('href')
                                await interaction.followup.send(
                                    f"**Top result for '{selected_game}':**\n"
                                    f"🎮 **{title}**\n🔗 {target_host}: <{final_download_link}>"
                                )
                                return                    
                                
                        except Exception as e:
                            message_lines.append(f"🎮 **{title}**\n⚠️ *Error loading the game page.*\n")

                await interaction.followup.send(f"❌ Could not find a **{target_host}** link for **{selected_game}** in the top results.")
                        
            except requests.exceptions.RequestException as e:
                await interaction.followup.send(f"⚠️ Network error occurred: {e}")

        return button_callback



class Scraping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot    
        #self.bot = bot
        # Initialize Gemini so the game command can use it!
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            print("⚠️ WARNING: GEMINI_API_KEY not found in .env!")
            self.client = None   
        

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
        await interaction.response.defer()
        
        if not self.client:
            await interaction.followup.send("❌ AI is not configured. I can't generate options right now.")
            return

        ai_prompt = (
            f"The user is searching for a video game using the query: '{game_name}'. "
            f"Give me the 4 most popular or likely specific game titles they might mean. "
            f"Return ONLY a comma-separated list of the names, absolutely no other text. "
            f"Example: Resident Evil 4, Resident Evil Village, Resident Evil 2 Remake, Resident Evil 3"
        )
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=ai_prompt
            )
            
            raw_text = response.text.replace('\n', '').strip()
            game_options = [g.strip() for g in raw_text.split(',') if g.strip()]
            
            view = GameSelectionView(game_options)
            
            await interaction.followup.send(f"🤖 I found a few possibilities for **{game_name}**. Which one do you mean?", view=view)
            
        except Exception as e:
            await interaction.followup.send(f"⚠️ The AI encountered an error generating options: {e}")

    


    



    @app_commands.command()
    async def ebook(self,interaction: discord.Interaction, book_name: str):
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
                    await interaction.followup.send(
                        f"Sorry, I couldn’t find a relevant match for **{book_name.title()}**."
                    )
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
                    # Create a View with buttons
                    view = discord.ui.View()
                    for idx, link in enumerate(slow_links, start=1):
                        button = discord.ui.Button(
                            label=f"🐢 Slow Download {idx}",
                            url=link
                        )
                        view.add_item(button)

                    await interaction.followup.send(
                        f"**Download options for '{chosen_title.strip()}':**",
                        view=view
                    )
                else:
                    await interaction.followup.send(
                        f"Found the book page for **{book_name.title()}**, but no download links were detected."
                    )

            except Exception as e:
                await page.screenshot(path="debug_ebook_error.png", full_page=True)
                await interaction.followup.send(
                    f"⚠️ An unexpected error occurred. Screenshot saved as `debug_ebook_error.png`."
                )
                print(f"Playwright Error in ebook command: {e}")

            finally:
                await browser.close()


<<<<<<< HEAD
    @app_commands.command(name="game_direct", description="Directly grabs the download link for a game.")
    async def game_direct(self, interaction: discord.Interaction, game_name: str): 
        # 1. Defer immediately so Discord doesn't timeout
        await interaction.response.defer()
        
        # The '*' catches names with spaces
        await interaction.followup.send(f"Searching for **{game_name}**... 🔎")
        
        TARGET_WEBSITE = 'https://steamrip.com'
        final_download_link = None # We will store the scraped link here

        # 2. Start Playwright directly inside the command
        try:
            async with async_playwright() as p:
                # HACKATHON TIP: Keep headless=False while testing so you can watch it!
                # (Remember to change this to headless=True when you host it on a server)
                browser = await p.chromium.launch(headless=True) 
                page = await browser.new_page()
                
                try:
                    # Format the game name for a URL (e.g., "GTA San Andreas" -> "GTA+San+Andreas")
                    search_query = game_name.replace(" ", "+")
                    search_url = f"{TARGET_WEBSITE}/?s={search_query}" 
                    
                    # Teleport directly to the search results page
                    await page.goto(search_url, timeout=15000)
                    
                    # Wait for the specific game banner to appear
                    await page.wait_for_selector('a.all-over-thumb-link', timeout=10000)

                    # Extract the href attribute from the very first result
                    partial_link = await page.locator('a.all-over-thumb-link').first.get_attribute('href')
                    
                    # Construct the full URL for the game page
                    clean_partial = partial_link.lstrip('/')
                    full_game_url = f"{TARGET_WEBSITE}/{clean_partial}"
                    print(f"Bot found the game page: {full_game_url}")

                    # Teleport directly to the game page
                    await page.goto(full_game_url, timeout=15000)

                    # Wait for the download button to load on the game page
                    button_selector = 'a.shortc-button'
                    await page.wait_for_selector(button_selector, timeout=15000)

                    # Extract the raw link
                    raw_link = await page.locator(button_selector).first.get_attribute('href')

                    # Fix the protocol-relative URL if it starts with "//"
                    if raw_link and raw_link.startswith('//'):
                        final_download_link = f"https:{raw_link}"
                    else:
                        final_download_link = raw_link

                    print(f"Success! Final link is: {final_download_link}")

                except Exception as e:
                    print(f"Scraping failed for {game_name}: {e}")
                    # final_download_link remains None, triggering the error message below

                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f"Playwright crashed: {e}")

        # 3. Send the final result back to Discord
        if final_download_link:
            # Safety net: ensure it's an absolute link
            full_url = f"{TARGET_WEBSITE}{final_download_link}" if final_download_link.startswith('/') else final_download_link
            await interaction.followup.send(f"Found it! Here you go: {full_url}")
        else:
            await interaction.followup.send(f"Sorry, I couldn't find a link for '{game_name}'. Check the spelling or try another game!")


=======
>>>>>>> f3f8be658b6c655360bd629544c771bf193f5a4d
async def setup(bot):
    await bot.add_cog(Scraping(bot))
