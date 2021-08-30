import discord
import traceback

from .lt_logger import lt_logger
from .rpg import rpg
from aiohttp import ClientSession
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands
from typing import Optional


class channels(commands.Cog):
    def __init__(self, bot, lt_db, channel):
        self.bot = bot
        self.db = lt_db
        self.channel = channel
        self.logger = lt_logger
        self.rpg = rpg

    def ctx_info(self, ctx):
        return ctx.channel.category.id, ctx.guild.id, ctx.message.author.id

    @commands.group(case_insensitive=True)
    async def dm(self, ctx):
        """
        Select a subcommand to use with this command.
        """

    @dm.command()
    async def claim(self, ctx):
        """
        Claim the role of dungeon master within current channel category. Only one user can be the dungeon master for a given category.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        output = self.db.add_owner(Guild, Category, ID)
        await ctx.send(output)

    @dm.command()
    async def unclaim(self, ctx):
        """Unclaim current dm for category. Administrators and the Current DM are the only users able to perform this action."""
        Category, Guild, ID = self.ctx_info(ctx)
        override = ctx.message.author.permissions_in(ctx.channel).administrator
        output = self.db.remove_owner(Guild, Category, ID, override)
        await ctx.send(output)

    @commands.bot_has_permissions(manage_webhooks=True)
    @dm.command()
    async def set_ic(self, ctx, Channel: Optional[discord.TextChannel]):
        """Set mentioned channel as in-character chat for this channel category. Only usable by DM."""
        try:
            Category, Guild, ID = self.ctx_info(ctx)
            dmCheck = self.db.owner_check(Guild, Category, ID)
            Channel = Channel.id
            if dmCheck == True:
                try:
                    try:
                        _, url = self.db.get_ic(Guild, Category)
                    except:
                        pass
                    if url != None:
                        webhooks = await self.bot.get_channel(Channel).webhooks()
                        for webhook in webhooks:
                            if webhook.url == url:
                                await webhook.delete()
                    webhook = await self.bot.get_channel(Channel).create_webhook(
                        name=f"IC-{ctx.channel.name}"
                    )
                    output = self.db.set_ic(Guild, Category, ID, Channel, webhook.url)
                except:
                    raise Exception
                if output == True:
                    await ctx.send(
                        f'{ctx.message.channel_mentions[0].mention} has been added as the IC channel for the "{ctx.channel.category}" category.'
                    )
            else:
                await ctx.send(
                    f'It looks like you\'re not the owner of the "{ctx.channel.category}" category.'
                )
        except KeyError as e:
            await ctx.send(
                f'It looks like you\'re not the owner of the "{ctx.channel.category}" category.'
            )

        except:
            message = str(traceback.format_exc())
            await self.logger.error(self, message, self.__class__.__name__, "DM Set IC")

    @commands.bot_has_permissions(manage_webhooks=True)
    @commands.command(case_insensitive=True)
    async def ic(self, ctx, character, *, message):
        """
        Send an in-character message to the current IC channel.

        This message can be deleted by the user who sent it by reacting to it with a ❌ emoji.

        This message can be edited by the user who sent it by replying to it. The entirety of the message sent in the reply will replace the original message.
        """

        try:
            Category, Guild, ID = self.ctx_info(ctx)
            character = character.lower()
            ic, url = self.db.get_ic(Guild, Category)

            if ic != None:
                try:
                    char = self.db.get_one_char(Guild, character, ID)
                    try:
                        avatar = char["token"]
                    except:
                        avatar = ctx.author.avatar_url
                    async with ClientSession() as session:
                        webhook = discord.Webhook.from_url(
                            url, adapter=discord.AsyncWebhookAdapter(session)
                        )
                        await webhook.send(
                            content=message,
                            username=char["name"].title(),
                            avatar_url=avatar,
                        )
                        await ctx.message.delete()
                except:
                    await ctx.send("It looks like something's gone wrong...")
                    raise Exception
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "IC Message Send"
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Wait for a reaction to be added, then remove the message if it fits certain criteria.
        """
        Guild = payload.guild_id
        user = payload.user_id

        message = (
            await self.bot.get_guild(Guild)
            .get_channel(payload.channel_id)
            .fetch_message(payload.message_id)
        )

        try:
            if (
                message.author.bot
                and message.author != self.bot.user
                and payload.emoji.name == "❌"
            ):
                character = message.author.display_name.lower()
                ownerCheck = self.db.char_owner(Guild, int(user), character)
                if ownerCheck == True:
                    await message.delete()

        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "DM Reactions"
            )

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.id != self.bot.user.id and message.reference != None:
            Category, Guild, channel = (
                message.channel.category.id,
                message.guild.id,
                message.channel,
            )

            ref_msg = await channel.fetch_message(message.reference.message_id)
            ref_auth = ref_msg.author
            character = ref_msg.author.display_name.lower()
            ownerCheck = self.db.char_owner(Guild, message.author.id, character)

        async with ClientSession() as session:
            _, url = self.db.get_ic(Guild, Category)
            webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session))
            if ref_auth.id == webhook.id and ownerCheck:
                await webhook.edit_message(
                    message_id=message.reference.message_id,
                    content=message.content,
                    username=character.title(),
                    avatar_url=ref_auth.avatar_url,
                )
                await message.delete()


def setup(bot):
    bot.add_cog(channels(bot))
