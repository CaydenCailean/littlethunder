import discord
import asyncio
import sys
from discord.ext import commands


class lt_logger(commands.Cog):

    def __init__(self, bot, channel):
        self.bot=bot
        self.channel= channel
        

    async def info(self, message, cog, command):
        embed = discord.Embed(title=f"INFO: {cog} [{command}]", description=message, color=0x00ff00)
        await self.bot.get_channel(id=int(self.channel)).send(embed=embed)

    async def debug(self, message, cog, command):
        embed = discord.Embed(title=f"DEBUG: {cog} [{command}]", description=message, color=0x00ff0ff)
        await self.bot.get_channel(id=int(self.channel)).send(embed=embed)

    async def error(self, message, cog, command):
        embed = discord.Embed(title=f"ERROR: {cog} [{command}]", description=message, color=0xff0000)
        await self.bot.get_channel(id=int(self.channel)).send(embed=embed)

    async def warning(self, message, cog, command):
        embed = discord.Embed(title=f"WARNING: {cog} [{command}]", description=message, color=0xffff00)
        await self.bot.get_channel(id=int(self.channel)).send(embed=embed)

    @commands.group(hidden=True)
    @commands.is_owner()
    async def test(self, ctx):
        pass

    @test.command(hidden=True)
    async def info_test(self, ctx):
        await lt_logger.info(self, "This is a test", "lt_logger.py", "log_test")

    @test.command(hidden=True)
    @commands.is_owner()
    async def warning_test(self, ctx):
        await lt_logger.warning(self, "This is a warning", "lt_logger", "log_test")

    @test.command(hidden=True)
    @commands.is_owner()
    async def debug_test(self, ctx):
        await lt_logger.debug(self, "This is a test", "logging", "log_test")
    @test.command(hidden=True)
    @commands.is_owner()
    async def error_test(self, ctx):
        await lt_logger.error(self, "This is a test", "logging", "log_test")

def setup(bot):
    bot.add_cog(lt_logger(bot))
