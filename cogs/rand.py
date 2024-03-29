import discord
import traceback

from .lt_logger import lt_logger
from discord.ext import commands
from random import randint


class rand(commands.Cog):
    def __init__(self, bot, lt_db, channel):
        self.bot = bot
        self.db = lt_db
        self.logger = lt_logger
        self.settings = ["deck", "public"]
        self.channel = channel

    # region Utility

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

    # endregion

    # region Random Tables

    @commands.group(case_insensitive=True, aliases=["rand"])
    async def random(self, ctx):
        """
        The Random command group surrounds the use of custom random tables which can be "rolled" on to give a random output. These tables can be weighted, or you can leave the "weight" argument at 1 for all entries for an unweighted table. Subcommands can only be used by the original creator of a table.

        If you're wishing to roll on a random table, use this command followed by the table name, i.e. `.random Table2`
        """
        if ctx.invoked_subcommand is None:
            Table = ctx.message.content.split(" ", 1)[1]
            try:
                await self.get(ctx, Table)
            except:
                message = str(traceback.format_exc())
                await self.logger.error(
                    self, message, self.__class__.__name__, "random", self.ctx.author
                )

    @random.command(case_insensitive=True)
    async def multi(self, ctx, Table, num: int):
        """
        Run multiple .random commands on the provided table.
        """
        for x in range(0, num):
            try:
                await self.get(ctx, Table)
            except:
                message = str(traceback.format_exc())
                await self.logger.error(
                    self, message, self.__class__.__name__, "random", self.ctx.author
                )

    @random.command(case_insensitive=True)
    async def list(self, ctx, scope=None):
        """
        Lists all random tables that you have created.
        """

        try:
            if scope != "all":
                tables = self.db.rand_get_owned(
                    ctx.message.author.id, ctx.message.guild.id
                )
                title = f"Random Tables owned by {ctx.message.author.display_name}"
            else:
                tables = self.db.rand_get_all(ctx.message.guild.id)
                title = "All Tables"
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "random", self.ctx.author
            )

        outString = ""
        for table in tables:
            outString += f"{table['table'].title()}\n"

        embed = discord.Embed(
            title=title,
            description=outString,
            color=0x00FF00,
        )
        await ctx.send(embed=embed)

    @random.command(case_insensitive=True)
    async def display(self, ctx, Table):
        """
        Displays a random table.
        """
        try:
            table = self.db.rand_get(ctx.message.guild.id, Table)
            print(table)
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "random", self.ctx.author
            )
        outString = "```"
        for value in table["pairs"]:
            outString += f"{value[1]} - {value[0]}\n"
        outString += "```"

        embed = discord.Embed(
            title=f"Random Table: {table['table']}",
            description=outString,
            color=0x00FF00,
        )
        await ctx.send(embed=embed)

    @random.command(case_insensitive=True)
    async def new(self, ctx, Table):
        """
        Adds a new table to the random tables for the server it is called in. Multiple word table names - "Wild Magic" for instance, must be surrounded in quotation marks.
        """
        Guild, ID = self.ctx_info(ctx)
        try:
            output = self.db.rand_new(Guild, ID, Table)
            await ctx.send(output)
        except:
            message = str(traceback.format_exc())
            await self.logger.error(self, message, self.__class__.__name__, "New Table")

    @random.command(case_insensitive=True, aliases=["add"])
    async def add_entry(self, ctx, Table, Weight, *, Value):
        """
        Adds a new weighted entry to the table. The table name requires quotation marks if it is longer than two words; the value does not.
        """
        Guild, ID = self.ctx_info(ctx)
        try:
            output = self.db.rand_add(Guild, ID, Table, Weight, Value)
            await ctx.send(output)
        except:
            message = str(traceback.format_exc())
            await self.logger.error(self, message, self.__class__.__name__, "add_entry")

    @random.command(case_insensitive=True, aliases=["remove"])
    async def remove_entry(self, ctx, Table, *, Value):
        """
        Removes a weighted entry from the table. The table name requires quotation marks if it is longer than two words; the value does not.
        """
        Guild, ID = self.ctx_info(ctx)
        output = self.db.rand_remove(Guild, ID, Table, Value)
        await ctx.send(output)

    @random.command(case_insensitive=True)
    async def delete(self, ctx, Table):
        """
        Deletes the specified table from the database. This is not reversible.
        """
        Guild, ID = self.ctx_info(ctx)
        output = self.db.rand_delete(Guild, ID, Table)
        await ctx.send(output)

    @random.command(case_insensitive=True, hidden=True)
    async def get(self, ctx, Table):

        Guild = ctx.message.guild.id
        image_ext = ["jpg", "png", "jpeg", "gif"]

        try:
            result = self.db.rand_get(Guild, Table)

            result["pairs"] = [tuple(x) for x in result["pairs"]]
            randout = self.weighted(result["pairs"])

            if result["deckMode"] == "on":
                ID = ctx.message.author.id
                mid = result["_id"]
                output = self.db.deck_draw(Guild, ID, mid, randout)
                print(output)

            embed = discord.Embed(
                title="__" + result["table"].title() + "__",
                description=f"{ctx.message.author.display_name} rolled on the {Table.title()} random table!",
                color=ctx.message.author.color,
            )

            if randout[0:4] == "http" and randout.split(".")[-1] in image_ext:
                embed.set_image(url=randout)

            else:
                embed.add_field(name="Random Result", value=randout)
            await ctx.send(embed=embed)

        except:
            await ctx.send(
                f'It looks like the "{Table}" doesn\'t exist yet, or your spelling is incorrect.'
            )
            raise Exception()

    @random.command()
    async def toggle(self, ctx, Table, Setting):
        """Toggles a designated mode for the provided random table.

        Currently settings are Public and DeckMode"""
        Guild, ID = self.ctx_info(ctx)
        try:
            output = self.db.toggle(Guild, ID, Table, Setting)
            await ctx.send(output)
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Random Table Toggle"
            )

    @random.command(aliases=["reset"])
    async def shuffle(self, ctx, Table):
        """
        Shuffle entries back into the deck in deckmode.
        """
        Guild, ID = self.ctx_info(ctx)
        try:
            output = self.db.deck_shuffle(Guild, ID, Table)
            await ctx.send(output)
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Deck Shuffle"
            )

    @random.command(aliases=["return"])
    async def return_one(self, ctx, Table, Value):
        """
        Return one entry to the deck in deckmode. WIP
        """
        Guild, ID = self.ctx_info(ctx)
        try:
            pass
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Return One"
            )


# endregion


def setup(bot):
    bot.add_cog(rand(bot))
