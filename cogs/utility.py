import discord
from discord.ext import commands


class utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(manage_messages=True)
    @commands.command(pass_context=True, no_pm=True, aliases=["clear", "p"])
    async def purge(self, ctx, number: int, members="everyone", *, txt=None):
        """
    Purge last n messages. Requires Manage Messages permission. 
    
    Accepts a number (n), a user, and a keyword to search for and purge messages containing it, though only the number is required.


    Examples:

    ..purge 20 - Removes last 20 messages regardless of user.
    ..purge 20 @CaydenCailean - Remove any messages in the last 20 that were written by @CaydenCailean
    ..purge 20 everyone foo - Remove any messages in the last 20 which contain the keyword "foo".
        """
        await ctx.channel.purge(limit=1)
        member_object_list = []
        if members != "everyone":
            member_list = [x.strip() for x in members.split(" , ")]
            for member in member_list:
                if "@" in member:
                    member = member[3 if "!" in member else 2 : -1]
                if member.isdigit():
                    member_object = ctx.guild.get_member(int(member))
                else:
                    member_object = ctx.guild.get_member_named(member)
                if not member_object:
                    return await ctx.send("Invalid user.")
                else:
                    member_object_list.append(member_object)

        if number < 100:
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
            await ctx.send("Too many messages. Enter a number less than 100.")


def setup(bot):
    bot.add_cog(utility(bot))
