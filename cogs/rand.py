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

#region Utility

    def ctx_info(self, ctx):
        Guild = ctx.message.guild.id
        ID = ctx.message.author.id
        return Guild, ID

    def weighted(self, pairs):
        total = sum(int(pair[1]) for pair in pairs)
        r = randint(1, total)
        
        for (value, weight) in pairs:    
            r -= int(weight)
            if r <= 0:
                return value

#endregion

#region Random Tables

    @commands.group(case_insensitive=True, aliases=["rand"])
    async def random(self, ctx):
        if ctx.invoked_subcommand is None:
            Table = ctx.message.content.split(' ')[1]
            await self.get(ctx, Table)
            

    @random.command(case_insensitive=True)
    async def new(self, ctx, Table):
        Guild, ID = self.ctx_info(ctx)
        output = self.lt_db.rand_new(Guild, ID, Table)
        await ctx.send(output)

    @random.command(case_insensitive=True, aliases=['add'])
    async def add_entry(self, ctx, Table, Weight, *, Value):
        Guild, ID = self.ctx_info(ctx)
        output = self.lt_db.rand_add(Guild, ID, Table, Weight, Value)
        await ctx.send(output)

    @random.command(case_insensitive=True, aliases=['remove'])
    async def remove_entry(self, ctx, Table, *, Value):

        Guild, ID = self.ctx_info(ctx)
        output = self.lt_db.rand_remove(Guild, ID, Table, Value)
        await ctx.send(output)

    @random.command(case_insensitive=True)
    async def delete(self, ctx, Table):
        Guild, ID = self.ctx_info(ctx)
        output = self.lt_db.rand_delete(Guild, ID, Table)
        await ctx.send(output)

    @random.command(case_insensitive=True)
    async def get(self, ctx, Table):
        Guild = ctx.message.guild.id
        image_ext = ['jpg','png','jpeg','gif']
        Table = Table.lower()
        result = self.lt_db.rand_get(Guild, Table)
        result['pairs'] = [tuple(x) for x in result['pairs']]
        randout = self.weighted(result['pairs'])
        print(randout.split('.')[-1])
        try:
            embed= discord.Embed(
                title="__" + result["table"].title() + "__",
                description = f"{ctx.message.author.display_name} rolled on the {Table.title()} random table!",
                color = ctx.message.author.color
            )

            if randout[4:] == "http" and randout.split('.')[-1] in image_ext:
                embed.set_image(url=randout)

            else:
                embed.add_field(name = "Random Result", value = randout)
            await ctx.send(embed=embed)

        except:
            await ctx.send(f"It looks like {Table.title()} doesn't exist yet, or your spelling is incorrect.")

#endregion

def setup(bot):
    bot.add_cog(rand(bot))
