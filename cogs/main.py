import discord
from discord.ext import commands
from .lt_logger import lt_logger

class main(commands.Cog):
    def __init__(self, bot, channel):
        self.bot = bot
        self.logger = lt_logger
        self.channel = channel

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name="games and rolling dice!"))
        await self.logger.info(self, f"{self.bot.user.name} is now online", "Main", "n/a")
        print("Logged in as " + self.bot.user.name)

def setup(bot):
    bot.add_cog(main(bot))