import discord
from discord.ext import commands
from discord import app_commands
from google import genai
import os

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            print("⚠️ WARNING: GEMINI_API_KEY not found!")
            self.client = None

    @app_commands.command(name="ask", description="Ask the AI a question.")
    async def ask(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        
        if not self.client:
            await interaction.followup.send("❌ AI is not configured. Missing API key.")
            return

        try:
            response = self.client.models.generate_content(model='gemini-2.5-flash', contents=question)
            
            reply_text = response.text[:1995] 
            
            await interaction.followup.send(reply_text)
            
        except Exception as e:
            await interaction.followup.send(f"⚠️ The AI encountered an error: {e}")


    @app_commands.command(name="review", description="Asks the AI for a book review")
    async def review(self, interaction:discord.Interaction, book_name: str):
        await interaction.response.defer()
        
        await interaction.followup.send(f"🤖 Analyzing **{book_name.title()}**...")

        try:
            
            prompt = f"You are a helpful book reviewer. Give me a short review and recommendation for: {book_name}."
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt
            )
            
            if response.text:
                # Discord has a 2000 character limit, this handles long reviews gracefully
                review_text = response.text
                if len(review_text) > 1900:
                    review_text = review_text[:1900] + "..."
                    
                await interaction.followup.send(f"📖 **AI Review for {book_name.title()}:**\n\n{review_text}")
            else:
                await interaction.followup.send("⚠️ The AI didn't return any text. Try again?")

        except Exception as e:
           # await interaction.followup.send(f"⚠️ An error occurred: {str(e)}")
            error_message = str(e)
            # Catch that specific 503 error
            if "503" in error_message:
                await interaction.followup.send("⏳ Google's AI servers are a bit overloaded right now. Give it a minute and try again!")
            else:
                await interaction.followup.send(f"⚠️ The AI encountered an unexpected error: {error_message}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))