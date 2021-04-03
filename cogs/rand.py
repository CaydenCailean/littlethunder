import discord
import re
import asyncio
from discord.ext import commands
import sys
from random import randint

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

    def weighted(self, pairs):
        total = sum(pair[0] for pair in pairs)
        r = randint(1, total)
        for (weight, value) in pairs:
            r -= weight
            if r <= 0:
                return value

    @commands.group(case_insensitive=True, aliases=["r", "rand"])
    async def random(self, ctx):
        if ctx.invoked_subcommand is None:
            Table = ctx.message.lstrip(' ')
            self.get(ctx, Table)
            return

    @random.command(case_insensitive=True)
    async def add(self, ctx, Table):

        return

    @random.command(case_insensitive=True)
    async def remove(self, ctx, Table, *, Value):
        return

    @random.command(case_insensitive=True)
    async def delete(self, ctx, Table):
        return

    @random.command(case_insensitive=True)
    async def get(self, ctx, Table):
        return


def setup(bot):
    bot.add_cog(rand(bot))
