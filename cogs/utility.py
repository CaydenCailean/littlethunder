import discord
import traceback

from .lt_logger import lt_logger
from discord.ext import commands


class utility(commands.Cog):
    def __init__(self, bot, lt_db, channel):
        self.bot = bot
        self.db = lt_db
        self.channel = channel
        self.logger = lt_logger

    @commands.command(pass_context=True, no_pm=True, aliases=["clear", "p"])
    async def purge(self, ctx, number: int, members="everyone", *, txt=None):
        """
        Purge last n messages. Without manage_messages, the members argument is ignored, though is still required to use keywords.

        Accepts a number (n), a user, and a keyword to search for and purge messages containing it, though only the number is required.

        Examples:

        .purge 20 - Removes last 20 messages regardless of user.
        .purge 20 @CaydenCailean - Remove any messages in the last 20 that were written by @CaydenCailean
        .purge 20 everyone foo - Remove any messages in the last 20 which contain the keyword "foo".
        """
        await ctx.channel.purge(limit=1)
        try:
            if ctx.message.author.permissions_in(ctx.channel).manage_messages:
                member_object_list = []
                if members != "everyone":
                    member_list = [x.strip() for x in members.split(" , ")]
                    for member in member_list:
                        if "@" in member:
                            member = int(member[3:-1])
                            member_object = ctx.guild.get_member(member)
                        else:
                            member_object = ctx.guild.get_member_named(member)

                        if not member_object:
                            return await ctx.send("Invalid user.")
                        else:
                            member_object_list.append(member_object)

                if number < 501:
                    async for message in ctx.message.channel.history(limit=number):
                        try:
                            if txt:
                                if not txt.lower() in message.content.lower():
                                    continue
                            if member_object_list:
                                if not message.author in member_object_list:
                                    continue

                            await message.delete()
                        except discord.Forbidden:
                            await ctx.send(
                                "You do not have permissions to delete other user's messages."
                            )

                else:
                    await ctx.send(
                        "Too many messages. Enter a number less than or equal to 500."
                    )
            else:

                if number < 501:
                    async for message in ctx.message.channel.history(limit=number):
                        try:
                            if txt:
                                if not txt.lower() in message.content.lower():
                                    continue
                            if message.author != ctx.message.author:
                                continue
                            await message.delete()
                        except Exception as e:
                            await ctx.send(e)
                else:
                    await ctx.send(
                        "Too many messages. Enter a number less than or equal to 500."
                    )

        except discord.Forbidden:
            await ctx.send("I do not have permissions to purge messages.")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        try:
            await self.bot.change_presence(
                activity=discord.Game(name=f"games in {len(self.bot.guilds)} servers!")
            )
            #self.db.drop_collection(guild.id)
            await self.logger.warning(
                self,
                f"LittleThunder has been removed from {guild.name}, ID: {guild.id} ",
                self.__class__.__name__,
                "Event Listener: Removed from Guild",
            )
        except Exception as e:
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Event Listener: Removed from Guild",
            )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        try:
            self.db.create_collections(guild.id)
            await self.bot.change_presence(
                activity=discord.Game(name=f"games in {len(self.bot.guilds)} servers!")
            )
            await self.logger.info(
                self,
                f"{self.bot.user.name} has joined {guild.name}.",
                self.__class__.__name__,
                "Event Listener: Joined Guild",
            )
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Event Listener: Joined Guild"
            )


def setup(bot):
    bot.add_cog(utility(bot))
