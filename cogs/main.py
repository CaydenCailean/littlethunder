import discord

from .lt_logger import lt_logger
from discord.ext import commands


class main(commands.Cog):
    def __init__(self, bot, channel):
        self.bot = bot
        self.logger = lt_logger
        self.channel = channel

    # when bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        try:
            await self.bot.change_presence(
                activity=discord.Game(name=f"games in {len(self.bot.guilds)} servers!")
            )
            await self.logger.info(
                self, f"{self.bot.user.name} is now online", "Main", "Startup"
            )
        except:
            await self.logger.error(
                self,
                str(traceback.format_exc()),
                "Main",
                "on_ready",
                self.bot.user,
            )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"Missing required argument: {error.param.name}", delete_after=5
            )

            await self.logger.warning(
                self,
                f"Missing required argument: {error.param.name}",
                f"{ctx.cog.__class__.__name__}",
                f"{ctx.message.content.split(' ')[0]}",
            )
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(
                f"You don't have permission to use this command", delete_after=5
            )


def setup(bot):
    bot.add_cog(main(bot))
