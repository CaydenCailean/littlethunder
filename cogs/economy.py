import discord
import traceback

from .lt_logger import lt_logger
from discord.ext import commands


class economy(commands.Cog):
    def __init__(self, bot, lt_db, channel):
        self.bot = bot
        self.logger = lt_logger
        self.db = lt_db
        self.channel = channel

    def ctx_info(self, ctx):
        Category = ctx.channel.category.id
        Guild = ctx.message.guild.id
        ID = ctx.message.author.id
        return Category, Guild, ID

    # allows DM of current channel to give a user money
    @commands.command(aliases=["give"])
    async def givemoney(self, ctx, amount: str, *, char: str):
        Category, Guild, ID = self.ctx_info(ctx)
        dmCheck = self.db.owner_check(Guild, Category, ID)
        if dmCheck:
            # get user's existing money, add [amount] to it, and save to db
            money = self.db.money_get(Guild, Category, char)
            try:
                int(amount)
                money["gp"] += int(amount)
            except:
                try:
                    money[f"{amount[-2]}p"] += int(amount[:-2])
                except:
                    await ctx.send("Invalid amount or currency.")
                    await self.logger.error(
                        self,
                        str(traceback.format_exc()),
                        self.__class__.__name__,
                        "Give Money",
                    )

            self.db.money_set(Guild, Category, char, money)


def setup(bot):
    bot.add_cog(economy(bot))
