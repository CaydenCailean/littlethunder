from click import pass_context
import discord
import traceback
import shutil
import os
import asyncio
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
    async def dm(self):
        """
        Select a subcommand to use with this command.
        """

    @dm.command()
    async def claim(self, ctx):
        """
        Claim the role of dungeon master within current channel category. Only one user can be the dungeon master for a given category.
        
        This command will fail if there is already a dungeon master in the category."""
        Category, Guild, ID = self.ctx_info(ctx)
        output = self.db.add_owner(Guild, Category, ID)
        await ctx.send(output)

    @dm.command()
    async def unclaim(self, ctx):
        """
        Unclaim current dm for category. Administrators and the Current DM are the only users able to perform this action.
        
        """
        Category, Guild, ID = self.ctx_info(ctx)
        override = ctx.message.author.permissions_in(ctx.channel).administrator
        output = self.db.remove_owner(Guild, Category, ID, override)
        await ctx.send(output)

    @dm.command()
    async def broadcast(self, ctx, *, message):
        """
        Broadcast a message to all IC Channels in a server which you are the DM for.

        This command is only available to the DM of the channel.
        """
        _, Guild, ID = self.ctx_info(ctx)
        channels = self.db.get_all_ic(Guild, ID)

        if channels != None:
            await ctx.message.delete()
            for channel in channels:

                await self.bot.get_guild(Guild).get_channel(channel).send(
                    f"[[{ctx.author.display_name.upper()} BROADCAST]] : {message}"
                )
        else:
            await ctx.send("You are not the DM for any IC Channels in this server.")

    @commands.bot_has_permissions(manage_webhooks=True)
    @dm.command()
    async def set_ic(self, ctx, Channel: Optional[discord.TextChannel]):
        """
        Set mentioned channel as in-character chat for this channel category. Only usable by DM.
        
        If no channel is mentioned, the current channel will be set as the IC channel."""
        try:
            Category, Guild, ID = self.ctx_info(ctx)
            dmCheck = self.db.owner_check(Guild, Category, ID)
            try:
                Channel = Channel.id
            except:
                Channel = ctx.channel.id
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
        except KeyError:
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

        This message can be edited by the user who sent it by replying to it with .edit in front of the new message contents. The entirety of the message sent in the reply will replace the original message.
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

                    try:
                        ref_msg = await ctx.message.channel.fetch_message(
                            ctx.message.reference.message_id
                        )
                        ref_auth = ref_msg.author
                        print(ref_auth)
                        embed = discord.Embed(
                            title=ref_auth,
                            description=ref_msg.content,
                            url=ref_msg.jump_url,
                        )
                    except:
                        pass

                    async with ClientSession() as session:
                        webhook = discord.Webhook.from_url(
                            url, adapter=discord.AsyncWebhookAdapter(session)
                        )
                        try:
                            await webhook.send(
                                content=message,
                                username=char["name"].title()
                                + f" ({str(ctx.message.author)})",
                                avatar_url=avatar,
                                embed=embed,
                            )
                        except:
                            await webhook.send(
                                content=message,
                                username=char["name"].title()
                                + f" ({str(ctx.message.author)})",
                                avatar_url=avatar,
                            )
                        await ctx.message.delete()

                except:
                    print(str(traceback.format_exc()))
                    raise Exception
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "IC Message Send"
            )

    @commands.command(aliases=["set_proxy", "set"])
    async def set_char(self, ctx, *, character):
        """
        Set default character to post as for this category's IC channel.

        Reacting to your in-character messages with a ❌ emoji will remove the message.

        This message can be edited by the user who sent it by replying to it with .edit in front of the new message contents. The entirety of the message sent in the reply will replace the original message. 
        """

        Category, Guild, ID = self.ctx_info(ctx)
        character = character.lower()
        output = self.db.set_proxy(Guild, Category, ID, character)

        if output:
            await ctx.send(
                f"{character.title()} has been set as {ctx.message.author.display_name}'s default character for this category."
            )

    @commands.command(aliases=["remove_proxy", "unset_proxy"])
    async def unset_char(self, ctx):
        """
        Remove default character for this category's IC channel.
        """

        Category, Guild, ID = self.ctx_info(ctx)
        output = self.db.remove_proxy(Guild, Category, ID)

        if output:
            await ctx.send("Default character has been removed.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Wait for a reaction to be added, then remove the message if it fits certain criteria.
        """
        user = payload.user_id

        try:
            Guild = payload.guild_id
        except:
            Guild = self.db.get_server_proxy(user)

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
                self, message, self.__class__.__name__, "DM Reactions", payload.user_id
            )

    @commands.Cog.listener("on_message")
    async def edit(self, message):
        if (
            message.author.id != self.bot.user.id
            and message.reference != None
            and message.content[0:6].lower() == ".edit "
        ):

            Category, Guild, channel = (
                message.channel.category.id,
                message.guild.id,
                message.channel,
            )

            ref_msg = await channel.fetch_message(message.reference.message_id)
            ref_auth = ref_msg.author
            character = ref_msg.author.display_name.replace(
                f" ({str(message.author)})", ""
            ).lower()
            ownerCheck = self.db.char_owner(Guild, message.author.id, character)

            async with ClientSession() as session:
                _, url = self.db.get_ic(Guild, Category)
                webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session))
                if ref_auth.id == webhook.id and ownerCheck:
                    await webhook.edit_message(
                        message_id=message.reference.message_id,
                        content=message.content.replace(".edit ", ""),
                        username=character.title() + f" ({str(message.author)})",
                        avatar_url=ref_auth.avatar_url,
                    )
                    await message.delete()

    @commands.Cog.listener("on_message")
    async def in_character(self, message):

        if message.author.id != self.bot.user.id and not message.webhook_id:
            
            Guild, Category, Channel, ID = (
                message.guild.id,
                message.channel.category_id,
                message.channel.id,
                message.author.id,
            )


            ic_channel, url = self.db.get_ic(Guild, Category)

            if ic_channel != Channel:
                return

            char = self.db.get_proxy(Guild, Category, ID)
            if not char:
                return
            
            for command in self.bot.walk_commands():
                if message.content.lower().startswith(f".{command.name}"):
                    return
                for alias in command.aliases:
                    if message.content.lower().startswith(f".{alias}"):
                        return

            if (
                message.content.lower().startswith(f".edit")
                and message.reference != None
            ):
                return

            if message.content.lower().startswith(f".ooc"):
                return


            else:

                try:
                    for file in os.walk("temp"):
                        for file in file[2]:
                            os.remove(f"temp/{file}")
                except:
                    pass

                try:
                    files = []
                    for index, attachment in enumerate(message.attachments):
                        if attachment.size > 83886080:
                            return
                        await attachment.save(f"temp/{index}_{attachment.filename}")
                        files.append(
                            discord.File(f"temp/{index}_{attachment.filename}")
                        )
                except:
                    files = None

                try:
                    try:
                        avatar = char["token"]
                    except:
                        avatar = message.author.avatar_url

                    try:
                        ref_msg = await message.channel.fetch_message(
                            message.reference.message_id
                        )
                        ref_auth = ref_msg.author
                        embed = discord.Embed(
                            title=ref_auth,
                            description=ref_msg.content,
                            url=ref_msg.jump_url,
                        )
                        try:
                            ref_img = ref_msg.attachments[0].url
                            embed.set_image(url=ref_img)
                        except:
                            pass

                    except:
                        pass
                    async with ClientSession() as session:
                        webhook = discord.Webhook.from_url(
                            url, adapter=discord.AsyncWebhookAdapter(session)
                        )
                        try:
                            await webhook.send(
                                content=message.content,
                                username=char["name"].title()
                                + f" ({str(message.author)})",
                                avatar_url=avatar,
                                embeds=[embed],
                                files=files,
                            )
                        except:

                            try:
                                await webhook.send(
                                    content=message.content,
                                    username=char["name"].title()
                                    + f" ({str(message.author)})",
                                    avatar_url=avatar,
                                    files=files,
                                )
                            except:
                                pass
                        await message.delete()

                except:
                    return


def setup(bot):
    bot.add_cog(channels(bot))
