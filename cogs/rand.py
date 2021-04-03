import discord
import re
import asyncio
from discord.ext import commands
import sys

sys.path.append("..")

from dbinit import lt_db


class rand(commands.Cog):
    def __init__(self, bot, lt_db):
        self.bot = bot
        self.lt_db = lt_db

    def ctx_info(self, ctx):
        Category = ctx.channel.category.id
        Guild = ctx.message.guild.id
        ID = ctx.message.author.id
        return Category, Guild, ID

    @commands.group(case_insensitive=True, aliases=["r", "rand"])
    async def random(self, ctx):
        if ctx.invoked_subcommand is None:
            return

    @random.command(case_insensitive=True)
    async def add(self, ctx, Weight, *, Value):
        return

    @random.command(case_insensitive=True)
    async def remove(self, ctx, *, Value):
        return


def setup(bot):
    bot.add_cog(rand(bot))
