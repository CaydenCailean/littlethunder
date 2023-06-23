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
        await self.bot.get_channel(int(self.channel)).send(embed=embed)

    async def debug(self, message, cog, command):
        embed = discord.Embed(
            title=f"DEBUG: {cog} | [{command}]", description=message, color=0x00FF0FF
        )
        await self.bot.get_channel(int(self.channel)).send(embed=embed)

#    async def error(self, message, cog, command, author):
#        try:
#            embed = discord.Embed(
#                title=f"ERROR: {cog} | [{command}]", description=message, color=0xFF0000
#            )
#            embed.set_footer(text=f"Run by {author} ")
#            await self.bot.get_channel(self.channel).send(embed=embed)
#        except:
#            print("Error logging error")
#            print(traceback.format_exc())

    async def error(self, message, cog, command, user):
        try:
            embed = discord.Embed(
                title=f"ERROR: {cog} | [{command}]", description=message, color=0xFF0000
            )
            embed.set_footer(text=f"Run by {user} ")
            channel = self.bot.get_channel(int(self.channel))
            await channel.send(embed=embed)
        except:
            print("Error logging error")
            print(traceback.format_exc())


    async def warning(self, message, cog, command):
        embed = discord.Embed(
            title=f"WARNING: {cog} | [{command}]", description=message, color=0xFFFF00
        )
        await self.bot.get_channel(int(self.channel)).send(embed=embed)

    @commands.group(hidden=True)
    @commands.is_owner()
    async def test_all(self, ctx):
        await self.info_test(ctx)
        await self.warning_test(ctx)
        await self.error_test(ctx)
        await self.debug_test(ctx)
        pass

    @test_all.command(hidden=True)
    async def info_test(self, ctx):
        await lt_logger.info(self, "This is a test", "lt_logger.py", "info_test")

    @test_all.command(hidden=True)
    @commands.is_owner()
    async def warning_test(self, ctx):
        await lt_logger.warning(self, "This is a warning", "lt_logger", "warning_test")

    @test_all.command(hidden=True)
    @commands.is_owner()
    async def debug_test(self, ctx):
        await lt_logger.debug(self, "This is a test", "logging", "debug_test")

    @test_all.command(hidden=True)
    @commands.is_owner()
    async def error_test(self, ctx):
        try:
            raise Exception("This is a test")
        except:
            message = str(traceback.format_exc())
            try:
                await lt_logger.error(self, message, self.__class__.__name__, "error_test", ctx.author)
            except:
                print(traceback.format_exc())


def setup(bot):
    bot.add_cog(lt_logger(bot))
