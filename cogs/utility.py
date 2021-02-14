import discord
from discord.ext import commands

class utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                        #print(member)
                        member = int(member[3:-1])
                        print(member)
                        member_object = ctx.guild.get_member(member)
                        print(ctx.guild.get_member(member))
                        
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

            if number < 100:
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
                await ctx.send("Too many messages. Enter a number less than 100.")
    

    

def setup(bot):
    bot.add_cog(utility(bot))
