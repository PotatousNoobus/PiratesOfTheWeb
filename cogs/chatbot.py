

# import discord
# from discord.ext import commands
# from discord import app_commands
# from google import genai
# from google.api_core import exceptions # Required for catching Rate Limits
# import os
# import asyncio

# class AIChat(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#         api_key = os.getenv("GEMINI_API_KEY")
#         if api_key:
#             # We use the aio property for non-blocking calls
#             self.client = genai.Client(api_key=api_key)
#         else:
#             print("⚠️ WARNING: GEMINI_API_KEY not found!")
#             self.client = None

#     @app_commands.command(name="ask", description="Ask the AI a question.")
#     async def ask(self, interaction: discord.Interaction, question: str):
#         await interaction.response.defer()
#         if not self.client:
#             await interaction.followup.send("❌ AI is not configured. Missing API key.")
#             return

#         try:
#             response = await self.client.aio.models.generate_content(
#                 model='gemini-2.5-flash', 
#                 contents=question
#             )
#             reply_text = response.text[:1995]
#             await interaction.followup.send(reply_text)
#         except Exception as e:
#             await interaction.followup.send(f"⚠️ The AI encountered an error: {e}")

#     @app_commands.command(name="review", description="Asks the AI for a book review")
#     async def review(self, interaction: discord.Interaction, book_name: str):
#         await interaction.response.defer()
#         if not self.client:
#             await interaction.followup.send("❌ AI is not configured.")
#             return

#         await interaction.followup.send(f"🤖 Analyzing **{book_name.title()}**...")

#         try:
#             prompt = f"You are a helpful book reviewer. Give me a short review and recommendation for: {book_name}."
#             response = await self.client.aio.models.generate_content(
#                 model='gemini-2.5-flash', 
#                 contents=prompt
#             )
            
#             if response.text:
#                 review_text = response.text
#                 if len(review_text) > 1900:
#                     review_text = review_text[:1900] + "..."
#                 await interaction.followup.send(f"📖 **AI Review for {book_name.title()}:**\n\n{review_text}")
#             else:
#                 await interaction.followup.send("⚠️ The AI didn't return any text.")

#         except Exception as e:
#             error_message = str(e)
#             if "503" in error_message:
#                 await interaction.followup.send("⏳ Google's AI servers are a bit overloaded. Try again in a minute!")
#             else:
#                 await interaction.followup.send(f"⚠️ The AI encountered an unexpected error: {error_message}")

#     @app_commands.command(name="recommend", description="Recommends 5 books based on a genre")
#     async def recommend(self, interaction: discord.Interaction, genre: str):
#         await interaction.response.defer()
        
#         if not self.client:
#             await interaction.followup.send("❌ AI is not configured.")
#             return

#         await interaction.followup.send(f"📚 Scouting for the best **{genre.title()}** books...")

#         for attempt in range(3):
#             try:
#                 # We give the AI a very specific Markdown template to follow
#                 prompt = (
#                     f"Recommend exactly 5 books in the '{genre}' genre. "
#                     "Use the following exact format for each book:\n\n"
#                     "### [Number]. **Title** by *Author*\n"
#                     "> [One-sentence hook here]\n\n"
#                     "Ensure there is a double newline between each book recommendation."
#                 )

#                 response = await self.client.aio.models.generate_content(
#                     model='gemini-2.0-flash',
#                     contents=prompt
#                 )

#                 if response.text:
#                     # Clean up the output and send
#                     final_text = response.text.strip()
#                     await interaction.followup.send(f"🌟 **Top 5 {genre.title()} Recommendations:**\n\n{final_text}")
#                     return 
#                 else:
#                     await interaction.followup.send("⚠️ Gemini returned an empty list.")
#                     return

#             except exceptions.ResourceExhausted:
#                 if attempt < 2:
#                     await asyncio.sleep(5)
#                     continue
#                 else:
#                     await interaction.followup.send("⚠️ Rate limit reached.")
            
#             except Exception as e:
#                 if "503" in str(e) and attempt < 2:
#                     await asyncio.sleep(5)
#                     continue
#                 else:
#                     await interaction.followup.send(f"⚠️ An error occurred: {str(e)}")
#                     break

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

# --- 1. THE BUTTONS ---
class BookActionView(discord.ui.View):
    def __init__(self, book_name, cog):
        super().__init__(timeout=180)
        self.book_name = book_name
        self.cog = cog

    @discord.ui.button(label="Review", style=discord.ButtonStyle.primary, emoji="📖")
    async def review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # Call the worker function directly
        await self.cog.worker_review(interaction, self.book_name)

    @discord.ui.button(label="Similar Books", style=discord.ButtonStyle.success, emoji="🌟")
    async def recommend_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # Call the worker function directly
        await self.cog.worker_recommend(interaction, self.book_name)

# --- 2. THE COG ---
class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None

    # --- CORE WORKER FUNCTIONS (The "Engine") ---
    # These handle the actual AI logic for both buttons and commands

    async def worker_review(self, interaction, book_name):
        try:
            prompt = f"You are a helpful book reviewer. Give me a short review and recommendation for: {book_name}."
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash', contents=prompt
            )
            text = response.text[:1900] + "..." if len(response.text) > 1900 else response.text
            await interaction.followup.send(f"📖 **Review for {book_name}:**\n\n{text}")
        except Exception as e:
            await interaction.followup.send(f"⚠️ Review Error: {str(e)[:100]}")

    async def worker_recommend(self, interaction, genre_or_book):
        try:
            prompt = (
                f"Recommend 5 books based on: '{genre_or_book}'. "
                "Use this format:\n### [Number]. **Title** by *Author*\n> [One-sentence hook]\n\n"
            )
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash', contents=prompt
            )
            await interaction.followup.send(f"🌟 **Recommendations for {genre_or_book}:**\n\n{response.text}")
        except Exception as e:
            await interaction.followup.send(f"⚠️ Recommendation Error: {str(e)[:100]}")

    # --- SLASH COMMANDS ---

    @app_commands.command(name="ask", description="Ask the AI a question.")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        try:
            response = await self.client.aio.models.generate_content(model='gemini-2.5-flash', contents=question)
            await interaction.followup.send(response.text[:1995])
        except Exception as e:
            await interaction.followup.send(f"⚠️ Error: {e}")

    @app_commands.command(name="review", description="Get a book review")
    async def review(self, interaction: discord.Interaction, book_name: str):
        await interaction.response.defer()
        await self.worker_review(interaction, book_name)

    @app_commands.command(name="recommend", description="Get book recommendations")
    async def recommend(self, interaction: discord.Interaction, genre: str):
        await interaction.response.defer()
        await self.worker_recommend(interaction, genre)

    @app_commands.command(name="image", description="Identify a book from a photo")
    async def image(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer()

        if not file.content_type.startswith("image/"):
            await interaction.followup.send("❌ Please upload an image.")
            return

        try:
            img_data = await file.read()
            # Fixed the Pydantic validation error with types.Part
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    "Identify the book in this image. Return ONLY 'Title by Author'.",
                    types.Part.from_bytes(data=img_data, mime_type=file.content_type)
                ]
            )
            
            book_id = response.text.strip()
            view = BookActionView(book_id, self)
            await interaction.followup.send(f"🔍 I identified: **{book_id}**\nWhat's the next move?", view=view)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Vision Error: {str(e)[:100]}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
