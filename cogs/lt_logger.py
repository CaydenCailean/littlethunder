import discord
import traceback

from discord.ext import commands

# custom logger using discord as a backend


class lt_logger(commands.Cog):
    def __init__(self, bot, channel):
        self.bot = bot
        self.channel = channel

    async def info(self, message, cog, command):
        embed = discord.Embed(
            title=f"INFO: {cog} | [{command}]", description=message, color=0x00FF00
        )
        await self.bot.get_channel(id=int(self.channel)).send(embed=embed)

    async def debug(self, message, cog, command):
        embed = discord.Embed(
            title=f"DEBUG: {cog} | [{command}]", description=message, color=0x00FF0FF
        )
        await self.bot.get_channel(id=int(self.channel)).send(embed=embed)

    async def error(self, message, cog, command, author):
        embed = discord.Embed(
            title=f"ERROR: {cog} | [{command}]", description=message, color=0xFF0000
        )
        embed.set_footer(text=f"Run by {author} ")
        await self.bot.get_channel(id=int(self.channel)).send(embed=embed)

    async def warning(self, message, cog, command):
        embed = discord.Embed(
            title=f"WARNING: {cog} | [{command}]", description=message, color=0xFFFF00
        )
        await self.bot.get_channel(id=int(self.channel)).send(embed=embed)

    @commands.group(hidden=True)
    @commands.is_owner()
    async def test(self, ctx):
        pass

    @test.command(hidden=True)
    async def info_test(self, ctx):
        await lt_logger.info(self, "This is a test", "lt_logger.py", "info_test")

    @test.command(hidden=True)
    @commands.is_owner()
    async def warning_test(self, ctx):
        await lt_logger.warning(self, "This is a warning", "lt_logger", "warning_test")

    @test.command(hidden=True)
    @commands.is_owner()
    async def debug_test(self, ctx):
        await lt_logger.debug(self, "This is a test", "logging", "debug_test")

    @test.command(hidden=True)
    @commands.is_owner()
    async def error_test(self, ctx):
        try:
            raise Exception("This is a test")
        except:
            message = str(traceback.format_exc())
            await lt_logger.error(self, message, self.__class__.__name__, "error_test")


def setup(bot):
    bot.add_cog(lt_logger(bot))
