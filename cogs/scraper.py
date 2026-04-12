import discord
from discord.ext import commands
from discord import app_commands
import urllib.parse
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import os
from google import genai
import aiohttp
import json
import redis.asyncio as redis
from dotenv import load_dotenv


load_dotenv()
REDIS_URL = os.getenv('REDIS_URL')
cache = redis.from_url(REDIS_URL, decode_responses=True)

class SelectionView(discord.ui.View):
    def __init__(self, game_options):
        super().__init__(timeout=60) 
        
        for game in game_options[:5]: 
            button = discord.ui.Button(label=game.strip()[:80], style=discord.ButtonStyle.success)
            button.callback = self.make_callback(game.strip())
            self.add_item(button)

    def make_callback(self, selected_game):
        async def button_callback(interaction: discord.Interaction):
            for child in self.children:
                child.disabled = True
            
            await interaction.response.edit_message(content=f"🔍 Fetching the top links for **{selected_game}**...", view=self)

            cache_key = f"game_torrent:{selected_game.strip().lower()}"
            found_links = []


            try:
                cached_data = await cache.get(cache_key)
                if cached_data:
                    print(f"⚡ CACHE HIT for {cache_key}!")
                    found_links = json.loads(cached_data)
            except Exception as e:
                print(f"⚠️ Cache read error: {e}")

            
            if not found_links:
                print("🔍 CACHE MISS. Scraping website...")
                safe_name = urllib.parse.quote(selected_game)
                url = f"https://fitgirl-repacks.site/?s={safe_name}" 
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
                                    found_links.append({"title": title, "url": final_download_link})
                                    
                                    if len(found_links) == 2:
                                        break 
                            except Exception as e:
                                print(f"Error loading {game_page_link}: {e}")
                                continue
                                
                    # --- CACHE SAVE ---
                    if found_links:
                        try:
                            await cache.set(name=cache_key, value=json.dumps(found_links), ex=86400)
                        except Exception as e:
                            print(f"⚠️ Cache write error: {e}")

                except requests.exceptions.RequestException as e:
                    await interaction.followup.send(f"⚠️ Network error occurred: {e}")
                    return

            # ==========================================
            # 3. BUILD UI
            # ==========================================
            if found_links:
                link_view = discord.ui.View()
                for link_data in found_links:
                    button_label = f"Download {link_data['title']}"[:80]
                    link_button = discord.ui.Button(label=button_label, url=link_data['url'], style=discord.ButtonStyle.link)
                    link_view.add_item(link_button)
                    
                result_embed = discord.Embed(
                    title="🎮 Download Links Found",
                    description=f"Here are the top **{len(found_links)}** result(s) for **{selected_game}**.",
                    color=discord.Color.green() 
                )
                result_embed.set_footer(text="Click the buttons below to download.")
                await interaction.followup.send(embed=result_embed, view=link_view)
            elif not found_links:
                # Only send this if the scrape finished but still found nothing
                await interaction.followup.send(f"❌ Could not find any links for **{selected_game}** in the top results.")

        return button_callback

async def scrape_site_search(base_url: str, game_name: str):

    clean_query = game_name.strip().lower()
    cache_key = f"steamrip_search:{clean_query}"
    try:
        cached_data = await cache.get(cache_key)
        if cached_data:
            print("⚡ REDIS CACHE HIT! Skipping Playwright entirely.")
            # Redis stores data as strings, so we unpack it back into a Python list
            return json.loads(cached_data)
    except Exception as e:
        print(f"⚠️ Redis read error (ignoring and scraping anyway): {e}")

    print("🔍 CACHE MISS! Firing up the invisible browser...")

    async with async_playwright() as p:
        
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"]) 
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        try:
            search_query = game_name.replace(" ", "+")
            search_url = f"{base_url}/?s={search_query}" 
            
            await page.goto(search_url, timeout=30000) 
            
            try:
                await page.wait_for_selector('div.slide', timeout=15000)
            except Exception as e:
                print(f"❌ ERROR: Timed out waiting for the games to appear!")
                await page.screenshot(path="CRASH_REPORT_search.png", full_page=True)
                return [] 
            
            elements = await page.locator('div.slide').all()
            
            results = []
            for el in elements[:7]: 
                try:
                    raw_link = await el.locator('a.all-over-thumb-link').first.get_attribute('href', timeout=1000)
                    if not raw_link:
                        continue
                    
                    image_url = await el.get_attribute('data-back-webp') or await el.get_attribute('data-back')

                    if image_url:
                        if image_url.startswith('//'):
                            image_url = f"https:{image_url}"
                        elif image_url.startswith('/'):
                            image_url = f"{base_url.rstrip('/')}{image_url}"
                        elif not image_url.startswith('http'):
                            image_url = None                    
                    
                    try:
                        title = await el.locator('.screen-reader-text').first.inner_text(timeout=1000)
                    except:
                        title = raw_link.strip('/').split('/')[-1].replace('-', ' ').title()
                        
                   
                    if raw_link and title:
                        clean_path = raw_link.replace(base_url, "").lstrip('/')
                        results.append({"title": title.strip(), "path": clean_path, "image": image_url})
                        

                except Exception as inner_e:
                    print(f"⚠️ Skipped a weirdly formatted game box.")
                    continue
                    
            if results:
                try:
                    # ex=86400 tells Redis to automatically delete this record in exactly 24 hours
                    await cache.set(name=cache_key, value=json.dumps(results), ex=172800)
                    print("💾 Saved fresh scrape results to Redis Cloud!")
                except Exception as e:
                    print(f"⚠️ Failed to save to Redis: {e}")

            print("🎉 SEARCH COMPLETE!")
            return results
            
        except Exception as e:
            print(f"❌ CRITICAL SCRAPE ERROR: {e}")
            return []
        finally:
            await browser.close()

async def get_game_suggestions(query: str):
    safe_query = urllib.parse.quote(query)
    url = f"https://store.steampowered.com/api/storesearch/?term={safe_query}&l=english&cc=US"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('total', 0) > 0:
                        # Extract names, remove duplicates, keep top 5
                        games = [item['name'] for item in data['items']]
                        return list(dict.fromkeys(games))[:5]
    except Exception as e:
        print(f"API Error: {e}")
    return []
async def scrape_direct_download(base_url: str, relative_path: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"]) 
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        try:
            full_game_url = f"{base_url.rstrip('/')}/{relative_path}"
            await page.goto(full_game_url, timeout=15000)

            button_selector = 'a.shortc-button'
            await page.wait_for_selector(button_selector, timeout=15000)

            raw_link = await page.locator(button_selector).first.get_attribute('href')

            if raw_link:
                if raw_link.startswith('//'):
                    return f"https:{raw_link}"
                elif raw_link.startswith('/'):
                    return f"{base_url.rstrip('/')}{raw_link}"
                elif not raw_link.startswith('http'):
                    return f"https://{raw_link}"
                else:
                    return raw_link
            return None
            
        except Exception as e:
            print(f"Download scrape failed: {e}")
            return None
        finally:
            await browser.close()

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
        

    @app_commands.command(name="stream", description="Get a direct streaming link for a movie.")
    async def stream(self, interaction: discord.Interaction, movie_name: str):
        await interaction.response.defer()
        safe_name = urllib.parse.quote_plus(movie_name)
        
        
        base_url = "https://westream.to/search?keyword=" 
        final_link = base_url + safe_name
        
        
        stream_embed = discord.Embed(
            title="🍿 Stream Located",
            description=f"Found the streaming portal for **{movie_name.title()}**.",
            color=discord.Color.purple() 
        )
        
        
        stream_embed.set_footer(text="Grab your popcorn!")

       
        view = discord.ui.View()
        button_label = f"Watch {movie_name.title()}"[:80]
        stream_button = discord.ui.Button(
            label=button_label, 
            style=discord.ButtonStyle.link, 
            url=final_link
        )
        view.add_item(stream_button)
        
        await interaction.followup.send(embed=stream_embed, view=view)

    
    @app_commands.command(name="movie_torrent", description="Physically types into the search bar and grabs dynamic links.")
    async def movie_torrent(self, interaction: discord.Interaction, movie_name: str):
        await interaction.response.defer()
    
        await interaction.followup.send(f"🔍 Firing up the invisible browser to search for **{movie_name.title()}**...")
        
        cache_key = f"movie_torrent:{movie_name.strip().lower()}"
        found_movies = []

        try:
            cached_data = await cache.get(cache_key)
            if cached_data:
                print(f"⚡ CACHE HIT for {cache_key}!")
                found_movies = json.loads(cached_data)
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")

        if not found_movies:
            print("🔍 CACHE MISS. Firing up Playwright...")
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
                        file = discord.File("debug_after_enter.png")
                        await interaction.followup.send(f"❌ I couldn't find the list for '{movie_name}'.", file=file)
                        await browser.close()
                        return
                        
                    total_elements = await page.locator(results_selector).count()
                    limit = min(10, total_elements)
                    
                    for i in range(limit):
                        element = page.locator(results_selector).nth(i)
                        title = await element.inner_text()
                        link = await element.get_attribute('href')                    
                        
                        if link and link.startswith('/'):
                            parsed_uri = urllib.parse.urlparse(search_page_url)
                            base = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
                            link = base + link                        
                        
                        found_movies.append({
                            "title": title.strip(),
                            "url": link
                        })                
                    
                    
                    if found_movies:
                        try:
                            await cache.set(name=cache_key, value=json.dumps(found_movies), ex=86400)
                        except Exception as e:
                            print(f"⚠️ Cache write error: {e}")

                except Exception as e:
                    print(f"Playwright Error: {e}")
                    await interaction.followup.send("⚠️ The browser hit a snag or timed out.")
                    return
                finally:
                    await browser.close()

        
        if found_movies:
            movie_view = discord.ui.View()
            for idx, movie_data in enumerate(found_movies):                        
                button_label = f"{idx+1}. {movie_data['title']}"[:80]
                btn = discord.ui.Button(label=button_label, url=movie_data['url'], style=discord.ButtonStyle.link)
                movie_view.add_item(btn)
                
            movie_embed = discord.Embed(
                title="🍿 Movie Search Results",
                description=f"Found **{len(found_movies)}** results for **{movie_name.title()}**.",
                color=discord.Color.purple() 
            )
            movie_embed.set_footer(text="Click a button below to go to the page.")
            await interaction.followup.send(embed=movie_embed, view=movie_view)
        else:
            await interaction.followup.send(f"❌ No links were found for **{movie_name.title()}**.")
        

    @app_commands.command(name="game_torrent", description="Searches the website for a torrent link!")
    async def game_torrent(self, interaction: discord.Interaction, game_name: str):
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
            
            view = SelectionView(game_options)
            
            selection_embed = discord.Embed(
                title="🤖 Game Disambiguation",
                description=f"I found a few possibilities for **{game_name}**.\nWhich one do you mean?",
                color=discord.Color.green() 
            )
            
            
            selection_embed.set_footer(text="Select an option below to fetch links.")

            
            await interaction.followup.send(embed=selection_embed, view=view)
            
        except Exception as e:
            await interaction.followup.send(f"⚠️ The AI encountered an error generating options: {e}")


    @app_commands.command(name="ebook", description="One stop destination for all the reading material!")
    async def ebook(self, interaction: discord.Interaction, book_name: str):
        await interaction.response.defer()
        await interaction.followup.send(f"📚 Searching for **{book_name.title()}** ...")

        cache_key = f"ebook:{book_name.strip().lower()}"
        ebook_data = {} # Will hold {"title": "Book Name", "links": ["url1", "url2"]}


        try:
            cached_data = await cache.get(cache_key)
            if cached_data:
                print(f"⚡ CACHE HIT for {cache_key}!")
                ebook_data = json.loads(cached_data)
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")


        if not ebook_data:
            print("🔍 CACHE MISS. Firing up Playwright...")
            safe_name = urllib.parse.quote_plus(book_name)
            base_url = "https://annas-archive.gd"
            search_url = f"{base_url}/search?q={safe_name}"
            search_selector = "a[href^='/md5/']"

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_selector(search_selector, timeout=15000)

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

                    detail_url = f"{base_url}{chosen_link}"
                    await page.goto(detail_url, wait_until="domcontentloaded", timeout=30000)

                    slow_div_selector = "div.mb-4:nth-of-type(2) li a"
                    await page.wait_for_selector(slow_div_selector, timeout=15000)

                    slow_items = page.locator(slow_div_selector)
                    dl_count = await slow_items.count()

                    slow_links = []
                    for i in range(min(dl_count, 3)):  
                        dl_item = slow_items.nth(i)
                        dl_href = await dl_item.get_attribute("href")
                        if dl_href:
                            if dl_href.startswith("/"):
                                dl_href = f"{base_url}{dl_href}"
                            slow_links.append(dl_href)

                    # --- CACHE SAVE ---
                    if slow_links:
                        ebook_data = {
                            "title": chosen_title.strip(),
                            "links": slow_links
                        }
                        try:
                            await cache.set(name=cache_key, value=json.dumps(ebook_data), ex=86400)
                        except Exception as e:
                            print(f"⚠️ Cache write error: {e}")

                except Exception as e:
                    await page.screenshot(path="debug_ebook_error.png", full_page=True)
                    await interaction.followup.send("⚠️ An unexpected error occurred. Screenshot saved as `debug_ebook_error.png`.")
                    print(f"Playwright Error in ebook command: {e}")
                    return
                finally:
                    await browser.close()

        
        if ebook_data and ebook_data.get("links"):
            view = discord.ui.View()
            for idx, link in enumerate(ebook_data["links"], start=1):
                button = discord.ui.Button(label=f"🐢 Reliable Download {idx}", url=link)
                view.add_item(button)

            embed = discord.Embed(
                title=f"Download options for '{ebook_data['title']}'",
                description="Click one of the buttons below to download.",
                color=discord.Color.yellow()
            )
            embed.set_footer(text="Powered by Anna's Archive")
            await interaction.followup.send(embed=embed, view=view)
        else:
            await interaction.followup.send(f"Found the book page for **{book_name.title()}**, but no download links were detected.")

    @app_commands.command(name="game_direct", description="Search the website directly for game downloads")
    async def game_direct(self, interaction: discord.Interaction, game_name: str):
        
        await interaction.response.defer()
        
        TARGET_WEBSITE = 'https://steamrip.com'         
        
        website_results = await scrape_site_search(TARGET_WEBSITE, game_name)
        
        if website_results:            
            view = GameSelectionView(website_results, TARGET_WEBSITE)
            
            embed = discord.Embed(
                title=f"🔎 Found {len(website_results)} matches for '{game_name}'",
                description="Click one to grab the link:",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, view=view)
            
        else:
            embed = discord.Embed(
                title = "❗Search Failed",
                description=f"❌ I couldn't find any games matching **{game_name}**.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

async def fetch_game_links(url: str, game_name: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"]) 
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            search_query = game_name.replace(" ", "+")
            search_url = f"{url}/?s={search_query}" 
            
            await page.goto(search_url, timeout=15000)
            await page.wait_for_selector('a.all-over-thumb-link', timeout=10000)

            partial_link = await page.locator('a.all-over-thumb-link').first.get_attribute('href')
            
            clean_partial = partial_link.lstrip('/')
            full_game_url = f"{url}/{clean_partial}"
            
            await page.goto(full_game_url, timeout=15000)

            button_selector = 'a.shortc-button'
            await page.wait_for_selector(button_selector, timeout=15000)

            raw_link = await page.locator(button_selector).first.get_attribute('href')

            if raw_link:
                if raw_link.startswith('//'):
                    return f"https:{raw_link}"
                elif raw_link.startswith('/'):
                    base_url = url.rstrip('/')
                    return f"{base_url}{raw_link}"
                elif not raw_link.startswith('http'):
                    return f"https://{raw_link}"
                else:
                    return raw_link
            
            return None 

        except Exception as e:
            print(f"Scraping failed for {game_name}: {e}")
            return None
        finally:
            await browser.close()

class GameSelectionView(discord.ui.View):
    def __init__(self, game_results: list, base_url: str):
        super().__init__(timeout=120) 
        self.base_url = base_url
        self.game_results = game_results
        
        for game in game_results: 
            button = discord.ui.Button(
                label=game["title"][:80], 
                style=discord.ButtonStyle.primary, 
                custom_id=game["path"][:100] 
            )
            button.callback = self.button_clicked
            self.add_item(button)

    async def button_clicked(self, interaction: discord.Interaction):
       
        await interaction.response.defer()        
        
        selected_path = interaction.data["custom_id"]
        selected_title = "the game" 
        selected_image = None        
        
        for item in self.children:            
            if item.custom_id == selected_path:               
                selected_title = item.label               
                
                item.label = f"✅ {item.label}"
                item.style = discord.ButtonStyle.success 
                
                for game in self.game_results:
                    if game["path"] == selected_path:
                        selected_image = game["image"]
                        break
            
            item.disabled = True 
            
        
        await interaction.edit_original_response(view=self)

        await interaction.followup.send(f"🚀 Teleporting to the game page for **{selected_title}**...")

        final_link = await scrape_direct_download(self.base_url, selected_path)
        
        if final_link:
            embed = discord.Embed(
                title=f"✅ Link Extracted: {selected_title}",
                description="Your direct download is ready.",
                color=discord.Color.green()
            )

            if selected_image and selected_image.startswith('http'):                
                embed.set_image(url=selected_image)

            dl_view = discord.ui.View()
            dl_view.add_item(discord.ui.Button(label="⬇️ Download Now", url=final_link, style=discord.ButtonStyle.link))
            
            await interaction.followup.send(embed=embed, view=dl_view)
        else:
            embed = discord.Embed(
                title = "❗Error",
                description="Sorry, the scraper couldn't extract the link!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Scraping(bot))
