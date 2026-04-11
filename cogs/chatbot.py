import discord
from discord.ext import commands
from discord import app_commands
from google import genai
import os

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Configure the API using the key from your .env file
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            #genai.configure(api_key=api_key)
           # self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.client = genai.Client(api_key=api_key)
        else:
            print("⚠️ WARNING: GEMINI_API_KEY not found!")
            self.client = None

    @app_commands.command(name="ask", description="Ask the AI a question.")
    async def ask(self, interaction: discord.Interaction, question: str):
        # AI generation can take a few seconds, so we defer just like the scrapers!
        await interaction.response.defer()
        
        if not self.client:
            await interaction.followup.send("❌ AI is not configured. Missing API key.")
            return

        try:
            # Send the user's question to the AI
            response = self.client.models.generate_content(model='gemini-2.5-flash', contents=question)
            
            # Discord messages have a strict 2000 character limit.
            # We slice the response to ensure it doesn't crash the bot if the AI writes an essay.
            reply_text = response.text[:1995] 
            
            await interaction.followup.send(reply_text)
            
        except Exception as e:
            await interaction.followup.send(f"⚠️ The AI encountered an error: {e}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))