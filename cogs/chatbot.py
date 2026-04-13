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


class BookActionView(discord.ui.View):
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

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None        
        self.books_api_key = os.getenv("GOOGLE_BOOKS_API_KEY")

    def create_error_embed(self, message: str) -> discord.Embed:
        return discord.Embed(title="⚠️ Error", description=message, color=discord.Color.yellow())

    async def worker_review(self, interaction, book_name):
        """Fetches trustworthy data from Google Books API and formats as Embed."""
        try:
            search_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{book_name}&maxResults=1"
            if self.books_api_key:
                search_url += f"&key={self.books_api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as resp:
                    if resp.status != 200:
                        await interaction.followup.send(embed=self.create_error_embed("Database error: Google Books API is unreachable."))
                        return
                    data = await resp.json()

            if "items" not in data:
                await interaction.followup.send(embed=self.create_error_embed(f"Could not find official data for '**{book_name}**'."))
                return

            book_info = data["items"][0]["volumeInfo"]
            title = book_info.get("title", "Unknown Title")
            authors = ", ".join(book_info.get("authors", ["Unknown Author"]))
            rating = book_info.get("averageRating", "N/A")
            rating_count = book_info.get("ratingsCount", 0)
            description = book_info.get("description", "No official summary available.")
            link = book_info.get("infoLink", "")

           
            clean_desc = re.sub('<[^<]+?>', '', description)
            
            
            embed = discord.Embed(
                title=f"📖 Official Data: {title}", 
                description=f"**Summary:**\n> {clean_desc[:4000]}", 
                color=discord.Color.yellow()
            )
            embed.add_field(name="✍️ Author", value=authors, inline=True)
            embed.add_field(name="⭐ Rating", value=f"{rating}/5 ({rating_count} reviews)", inline=True)
            
            if link:
                embed.url = link

            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=self.create_error_embed(f"Review Error: {str(e)[:100]}"))

    async def worker_recommend(self, interaction, genre_or_book):
        try:
            prompt = (
                f"Recommend exactly 5 books based on: '{genre_or_book}'. "
                "Use this format:\n### [Number]. **Title** by *Author*\n> [One-sentence hook]\n\n"
            )
            response = await interaction.client.ai_client.chat.completions.create(model='gpt-4o-mini', messages=[{"role": "system", "content": prompt}],temperature=0.3)
            
            embed = discord.Embed(
                title=f"🌟 Recommendations: {genre_or_book.title()}",
                description=response.choices[0].message.content,
                color=discord.Color.yellow()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=self.create_error_embed(f"Recommendation Error: {str(e)[:100]}"))

    @app_commands.command(name="chat", description="Ask the AI a general question")
    async def chat(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        try:
            response = await interaction.client.ai_client.chat.completions.create(model='gpt-4o-mini', messages=[{"role": "user", "content": question}],temperature=0.3)

            embed = discord.Embed(
                title="🤖 AI Response",
                description=response.choices[0].message.content,
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=self.create_error_embed(str(e)))

    @app_commands.command(name="book_review", description="Get an official review from Google Books")
    async def book_review(self, interaction: discord.Interaction, book_name: str):
        await interaction.response.defer()
        await self.worker_review(interaction, book_name)

    @app_commands.command(name="book_recommend", description="Get 5 book recommendations")
    async def book_recommend(self, interaction: discord.Interaction, genre: str):
        await interaction.response.defer()
        await self.worker_recommend(interaction, genre)

    @app_commands.command(name="detect", description="Identify a book cover or movie poster")
    async def detect(self, interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer()

        if not file.content_type.startswith("image/"):
            await interaction.followup.send(embed=self.create_error_embed("Please upload an image file."))
            return

        try:
            
            vision_prompt = (
                "Identify the media in this image. "
                "If it is a BOOK: Return exactly 'TYPE: BOOK | IDENTITY: Title by Author'. "
                "If it is a MOVIE: Return exactly 'TYPE: MOVIE | IDENTITY: Title (Year)'. "
                "Follow that with a 3-sentence description of the plot."
            )
            response = await interaction.client.ai_client.chat.completions.create(
                model='gpt-4o-mini', 
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text", 
                                "text": vision_prompt
                            },
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": file.url # Just pass the Discord attachment URL directly!
                                }
                            }
                        ]
                    }
                ],
                temperature=0.3
            )

            
            full_res = response.choices[0].message.content.strip()
            
            if "TYPE: BOOK" in full_res:
                lines = full_res.split("\n", 1)
                identity = lines[0].split("IDENTITY: ")[1]
                summary = lines[1] if len(lines) > 1 else "No description available."
                
                embed = discord.Embed(
                    title=f"📚 Book Identified: {identity}",
                    description=f"**AI Summary:**\n{summary}",
                    color=discord.Color.yellow()
                )
                embed.set_thumbnail(url=file.url) 
                
                view = BookActionView(identity, self)
                await interaction.followup.send(embed=embed, view=view)

            elif "TYPE: MOVIE" in full_res:
                lines = full_res.split("\n", 1)
                identity = lines[0].split("IDENTITY: ")[1]
                summary = lines[1] if len(lines) > 1 else "No description available."

                embed = discord.Embed(
                    title=f"🎬 Movie Identified: {identity}",
                    description=f"**Plot Summary:**\n{summary}\n\n**Download the movie using the command `/movie`.**",
                    color=discord.Color.yellow()
                )
                embed.set_thumbnail(url=file.url)
                
                await interaction.followup.send(embed=embed)
                
            else:
                embed = discord.Embed(
                    title="🤔 Unsure",
                    description="I couldn't tell if that's a book or a movie. Try a clearer shot!",
                    color=discord.Color.yellow()
                )
                embed.set_thumbnail(url=file.url)
                await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(embed=self.create_error_embed(f"Vision Error: {str(e)[:100]}"))

async def setup(bot):
    await bot.add_cog(AIChat(bot))