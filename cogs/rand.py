import discord
import re
import asyncio
from discord.ext import commands
import sys

sys.path.append('..')

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

def setup(bot):
    bot.add_cog(rand(bot))
