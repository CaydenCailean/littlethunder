import discord
import traceback

from .lt_logger import lt_logger
from discord.ext import commands


class info(commands.Cog):
    def __init__(self, bot, channel):
        self.bot = bot
        self.channel = channel
        self.logger = lt_logger

    @commands.command()
    async def info(self, ctx):
        """
        The goodest boi.

        Prints a small snippet about the bot to the channel.
        """
        try:
            embed = discord.Embed(
                title="Little Thunder", description="The Goodest Boi", color=0xFF8822
            )
            embed.add_field(name="Author", value="Cayden Cailean")
            embed.add_field(
                name="Purpose",
                value="I'm just a generally good boi. I like to roll dice, track initiative for you, and keep your characters organized.",
            )
            embed.add_field(
                name="GitHub", value="https://github.com/caydencailean/littlethunder"
            )
            embed.add_field(
                name="Donations",
                value="Donations, while not required, are greatly appreciated!\nhttps://donorbox.org/little-thunder",
            )
            embed.add_field(
                name="Paizo Community Use Disclosure",
                value="LittleThunder uses trademarks and/or copyrights owned by Paizo Inc., used under Paizo's Community Use Policy (https://paizo.com/communityuse). We are expressly prohibited from charging you to use or access this content. LittleThunder is not published, endorsed, or specifically approved by Paizo. For more information about Paizo Inc. and Paizo products, visit https://paizo.com.",
            )
            embed.add_field(
                name="Invite me!",
                value="Feel free to invite me to your own server!\n\n My invitation URL: https://discord.com/api/oauth2/authorize?client_id=674835707897839644&permissions=536881152&scope=bot"
            )
            embed.set_thumbnail(url="https://i.imgur.com/lacm87y.png")
            await ctx.send(embed=embed)
        except Exception:
            message = traceback.printstack()
            await self.logger.error(self, message, self.__name__, "info")

    @commands.command(aliases=["suggestion"])
    async def suggest(self, ctx, *, arg):
        user = ctx.message.author.name

        await ctx.channel.send(
            f"Thank you very much, {user}, your suggestion has been noted!"
        )
        await self.bot.get_guild(715969933980467260).get_channel(
            729086250882957433
        ).send(f"{user} would like to recommend: " + arg)

    @commands.command()
    async def bugreport(self, ctx, *, arg):
        user = ctx.message.author.name

        await ctx.channel.send(
            f"Thank you very much, {user}, Cayden will get the swatter!"
        )
        await self.bot.get_guild(715969933980467260).get_channel(
            730621040212049922
        ).send(f"{user} found a bug!: " + arg)


def setup(bot):
    bot.add_cog(info(bot))
