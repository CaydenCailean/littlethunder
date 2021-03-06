import discord
from discord.ext import commands


class info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx):
        """
        The goodest boi.

        Prints a small snippet about the bot to the channel.
        """
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
        embed.set_thumbnail(url="https://i.imgur.com/lacm87y.png")
        await ctx.send(embed=embed)

    @commands.command()
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
