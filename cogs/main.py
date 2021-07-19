import discord
import traceback
from discord.ext import commands
from .lt_logger import lt_logger

class main(commands.Cog):
    def __init__(self, bot, channel):
        self.bot = bot
        self.logger = lt_logger
        self.channel = channel
    
    #when bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name="games and rolling dice!"))
        await self.logger.info(self, f"{self.bot.user.name} is now online", "Main", "Startup")

def setup(bot):
    bot.add_cog(main(bot))