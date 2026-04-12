# import discord
# from discord.ext import commands
# from discord import app_commands
# from google import genai
# from google.genai import types
# from google.api_core import exceptions
# import os
# import asyncio

# # --- 1. THE BUTTONS ---
# class BookActionView(discord.ui.View):
#     def __init__(self, book_name, cog):
#         super().__init__(timeout=180)
#         self.book_name = book_name
#         self.cog = cog

#     @discord.ui.button(label="Review", style=discord.ButtonStyle.primary, emoji="📖")
#     async def review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#         await interaction.response.defer()
#         # Call the worker function directly
#         await self.cog.worker_review(interaction, self.book_name)

#     @discord.ui.button(label="Similar Books", style=discord.ButtonStyle.success, emoji="🌟")
#     async def recommend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#         await interaction.response.defer()
#         # Call the worker function directly
#         await self.cog.worker_recommend(interaction, self.book_name)

# # --- 2. THE COG ---
# class AIChat(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#         api_key = os.getenv("GEMINI_API_KEY")
#         self.client = genai.Client(api_key=api_key) if api_key else None

#     # --- CORE WORKER FUNCTIONS (The "Engine") ---
#     # These handle the actual AI logic for both buttons and commands

#     async def worker_review(self, interaction, book_name):
#         try:
#             prompt = f"You are a helpful book reviewer. Give me a short review and recommendation for: {book_name}."
#             response = await self.client.aio.models.generate_content(
#                 model='gemini-2.5-flash', contents=prompt
#             )
#             text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
#             await interaction.followup.send(f"📖 **Review for {book_name}:**\n\n{text}")
#         except Exception as e:
#             await interaction.followup.send(f"⚠️ Review Error: {str(e)[:100]}")

#     async def worker_recommend(self, interaction, genre_or_book):
#         try:
#             prompt = (
#                 f"Recommend 5 books based on: '{genre_or_book}'. "
#                 "Use this format:\n### [Number]. **Title** by *Author*\n> [One-sentence hook]\n\n"
#             )
#             response = await self.client.aio.models.generate_content(
#                 model='gemini-2.5-flash', contents=prompt
#             )
#             await interaction.followup.send(f"🌟 **Recommendations for {genre_or_book}:**\n\n{response.text}")
#         except Exception as e:
#             await interaction.followup.send(f"⚠️ Recommendation Error: {str(e)[:100]}")

#     # --- SLASH COMMANDS ---

#     @app_commands.command(name="ask", description="Ask the AI a question.")
#     async def ask(self, interaction: discord.Interaction, question: str):
#         await interaction.response.defer()
#         try:
#             response = await self.client.aio.models.generate_content(model='gemini-2.5-flash', contents=question)
#             await interaction.followup.send(response.text[:1995])
#         except Exception as e:
#             await interaction.followup.send(f"⚠️ Error: {e}")

#     @app_commands.command(name="review", description="Get a book review")
#     async def review(self, interaction: discord.Interaction, book_name: str):
#         await interaction.response.defer()
#         await self.worker_review(interaction, book_name)

#     @app_commands.command(name="recommend", description="Get book recommendations")
#     async def recommend(self, interaction: discord.Interaction, genre: str):
#         await interaction.response.defer()
#         await self.worker_recommend(interaction, genre)

#     @app_commands.command(name="image", description="Identify a book from a photo")
#     async def image(self, interaction: discord.Interaction, file: discord.Attachment):
#         await interaction.response.defer()

#         if not file.content_type.startswith("image/"):
#             await interaction.followup.send("❌ Please upload an image.")
#             return

#         try:
#             img_data = await file.read()
#             # Fixed the Pydantic validation error with types.Part
#             response = await self.client.aio.models.generate_content(
#                 model='gemini-2.5-flash',
#                 contents=[
#                     "Identify the book in this image. Return ONLY 'Title by Author'.",
#                     types.Part.from_bytes(data=img_data, mime_type=file.content_type)
#                 ]
#             )
            
#             book_id = response.text.strip()
#             view = BookActionView(book_id, self)
#             await interaction.followup.send(f"🔍 I identified: **{book_id}**\nWhat's the next move?", view=view)
#         except Exception as e:
#             await interaction.followup.send(f"⚠️ Vision Error: {str(e)[:100]}")

# async def setup(bot):
#     await bot.add_cog(AIChat(bot))

import discord
from discord.ext import commands
from discord import app_commands
from google import genai
from google.genai import types
from google.api_core import exceptions
import os
import asyncio
import aiohttp
import re

# --- 1. THE UI BUTTONS ---
class BookActionView(discord.ui.View):
    """Handles buttons specifically for books identified via image."""
    def __init__(self, book_name, cog):
        super().__init__(timeout=180)
        self.book_name = book_name
        self.cog = cog

    @discord.ui.button(label="Official Review", style=discord.ButtonStyle.primary, emoji="📖")
    async def review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.cog.worker_review(interaction, self.book_name)

    @discord.ui.button(label="Similar Books", style=discord.ButtonStyle.success, emoji="🌟")
    async def recommend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.cog.worker_recommend(interaction, self.book_name)

# --- 2. THE CHATBOT COG ---
class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Gemini setup
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        
        # Google Books setup
        self.books_api_key = os.getenv("GOOGLE_BOOKS_API_KEY")

    # --- CORE WORKER FUNCTIONS ---

    async def worker_review(self, interaction, book_name):
        """Fetches trustworthy data from Google Books API."""
        try:
            search_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{book_name}&maxResults=1"
            if self.books_api_key:
                search_url += f"&key={self.books_api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send("⚠️ Database error: Google Books API is unreachable.")
                        return
                    data = await resp.json()

            if "items" not in data:
                await interaction.followup.send(f"⚠️ Could not find official data for '**{book_name}**'.")
                return

            book_info = data["items"][0]["volumeInfo"]
            title = book_info.get("title", "Unknown Title")
            authors = ", ".join(book_info.get("authors", ["Unknown Author"]))
            rating = book_info.get("averageRating", "N/A")
            rating_count = book_info.get("ratingsCount", 0)
            description = book_info.get("description", "No official summary available.")
            link = book_info.get("infoLink", "")

            # Clean HTML tags from the description
            clean_desc = re.sub('<[^<]+?>', '', description)
            
            response_text = (
                f"📖 **Official Book Data for {title}**\n"
                f"✍️ **Author:** {authors}\n"
                f"⭐ **Rating:** {rating}/5 ({rating_count} reviews)\n\n"
                f"📑 **Summary:**\n> {clean_desc[:1500]}..." if len(clean_desc) > 1500 else f"📑 **Summary:**\n> {clean_desc}"
            )
            
            if link:
                response_text += f"\n\n🔗 [View on Google Books]({link})"

            await interaction.followup.send(response_text)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Review Error: {str(e)[:100]}")

    async def worker_recommend(self, interaction, genre_or_book):
        """Generates 5 recommendations using Gemini."""
        try:
            prompt = (
                f"Recommend exactly 5 books based on: '{genre_or_book}'. "
                "Use this format:\n### [Number]. **Title** by *Author*\n> [One-sentence hook]\n\n"
            )
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash', contents=prompt
            )
            await interaction.followup.send(f"🌟 **Recommendations based on {genre_or_book}:**\n\n{response.text}")
        except Exception as e:
            await interaction.followup.send(f"⚠️ Recommendation Error: {str(e)[:100]}")

    # --- SLASH COMMANDS ---

    @app_commands.command(name="ask", description="Ask the AI a general question")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        try:
            response = await self.client.aio.models.generate_content(model='gemini-2.5-flash', contents=question)
            await interaction.followup.send(response.text[:1995])
        except Exception as e:
            await interaction.followup.send(f"⚠️ Error: {e}")

    @app_commands.command(name="review", description="Get an official review from Google Books")
    async def review(self, interaction: discord.Interaction, book_name: str):
        await interaction.response.defer()
        await self.worker_review(interaction, book_name)

    @app_commands.command(name="recommend", description="Get 5 book recommendations")
    async def recommend(self, interaction: discord.Interaction, genre: str):
        await interaction.response.defer()
        await self.worker_recommend(interaction, genre)

    @app_commands.command(name="image", description="Identify a book cover or movie poster")
    async def image(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer()

        if not file.content_type.startswith("image/"):
            await interaction.followup.send("❌ Please upload an image file.")
            return

        try:
            img_data = await file.read()
            
            vision_prompt = (
                "Identify the media in this image. "
                "If it is a BOOK: Return exactly 'TYPE: BOOK | IDENTITY: Title by Author'. "
                "If it is a MOVIE: Return exactly 'TYPE: MOVIE | IDENTITY: Title (Year)'. "
                "Follow that with a 3-sentence description of the plot."
            )

            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    vision_prompt,
                    types.Part.from_bytes(data=img_data, mime_type=file.content_type)
                ]
            )
            
            full_res = response.text.strip()
            
            if "TYPE: BOOK" in full_res:
                lines = full_res.split("\n", 1)
                identity = lines[0].split("IDENTITY: ")[1]
                summary = lines[1] if len(lines) > 1 else "No description available."
                
                view = BookActionView(identity, self)
                await interaction.followup.send(
                    f"📚 **Book Identified:** {identity}\n"
                    f"📝 **AI Summary:** {summary}",
                    view=view
                )

            elif "TYPE: MOVIE" in full_res:
                lines = full_res.split("\n", 1)
                identity = lines[0].split("IDENTITY: ")[1]
                summary = lines[1] if len(lines) > 1 else "No description available."

                # Append your bolded message directly to the Discord send call
                await interaction.followup.send(
                    f"🎬 **Movie Identified:** {identity}\n"
                    f"🎞️ **Plot Summary:** {summary}\n\n"
                    f"**Download the movie using the command /movie.**"
                )
            else:
                await interaction.followup.send("🤔 I couldn't tell if that's a book or a movie. Try a clearer shot!")

        except Exception as e:
            await interaction.followup.send(f"⚠️ Vision Error: {str(e)[:100]}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
