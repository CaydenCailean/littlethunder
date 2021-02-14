import discord
import sys
from discord.ext import commands

sys.path.append("..")
from dbinit import lt_db

class utility(commands.Cog):
    def __init__(self, bot, lt_db):
        self.bot = bot
        self.lt_db = lt_db

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
                await ctx.send("Too many messages. Enter a number less than or equal to 500.")
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
                await ctx.send("Too many messages. Enter a number less than or equal to 500.")
    
    #@commands.has_guild_permissions(administrator=True)
    #@commands.command(pass_context=True, no_pm=True)
    #async def drop(self, ctx):
    #    """
    #    Please do not use lightly.
    #    Purges all information from Little Thunder's database related to the current server.
    #    """
    #    author = ctx.message.author
    #            
    #    await ctx.send("React with a 👍 if you're absolutely sure you want to go through with this. This cannot be reversed.")
    #    
    #    def check(reaction, user):
    #        return user == ctx.message.author and str(reaction.emoji) == '👍'
    #    
    #    try:
    #        reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
    #    except:
    #        pass

    #    Guild = ctx.guild.id
    #    dropped = self.lt_db.drop_collection(Guild)
    #    await ctx.send(f"Dropped {dropped} collections from lt_db.")

def setup(bot):
    bot.add_cog(utility(bot))
