import discord
import traceback
import time

from .lt_logger import lt_logger
from discord import app_commands
from discord.ext import commands


class char(commands.GroupCog, group_name="char"):
    def __init__(self, bot, lt_db, channel):
        self.bot = bot
        self.db = lt_db
        self.logger = lt_logger
        self.channel = channel

    def ctx_info(self, ctx):
        return ctx.channel.category.id, ctx.guild.id, ctx.message.author.id

    async def paginate_embeds(self, Guild, embeds, ownerList):
        # check len(ownerList)
        # if len(ownerList) > 6, iterate through first 6 owners:
        # if len(ownerList) < 6, iterate through all owners:

        if len(ownerList) > 6:
            newList = ownerList[:6]
        else:
            newList = ownerList
        embed = discord.Embed(
            description=f"Character List for {Guild.name}",
            title=f"__**Character List by Owner**__",
            color=0x202020,
        )

        for owner in newList:
            characterList = self.db.get_char_by_owner(Guild.id, owner)
            charList = ""
            for char in characterList:
                try:
                    char["name"]
                    charList += f"{char['name']}\n"
                except:
                    continue

            if charList == "":
                continue

            try:
                owner_name = await Guild.fetch_member(owner)
                owner_name = owner_name.display_name
                embed.add_field(name=f"{owner_name}", value=charList.title())
            except:
                owner_name = await self.bot.fetch_user(owner)
                owner_name = owner_name.name
                embed.add_field(
                    name=f"{owner_name}",
                    value="**__[USER NO LONGER IN SERVER]__**\n\n" + charList.title(),
                )

        embeds.append(embed)
        del ownerList[:6]
        if len(ownerList) > 0:
            await self.paginate_embeds(Guild, embeds, ownerList)

    @commands.group(case_insensitive=True)
    async def char(self, ctx):
        """
        Use to display a character's profile, if one exists. All characters are saved on a per-guild basis.

        Can also be used to list a user's characters, either your own by using .char without a name, or someone else's by using .char @user.
        """

        if ctx.invoked_subcommand is None:
            try:
                try:
                    ctx.message.mentions[0]
                    await self.display(ctx)

                except:

                    if ctx.message.content.lower() == ".char":
                        await self.display(ctx)
                    else:
                        Name = ctx.message.content.lstrip(" ")
                        await self.display(ctx, Name)

            except:
                message = str(traceback.format_exc())
                await self.logger.error(
                    self,
                    message,
                    self.__class__.__name__,
                    "Character Profile",
                    ctx.message.author,
                )

    @char.command()
    async def chown(self, ctx, Name):
        Name = Name.lower()
        _, Guild, ID = self.ctx_info(ctx)
        ownerCheck = ""
        try:
            ownerCheck = self.db.char_owner(Guild, ID, Name)
        except:
            pass
            # await ctx.send(f"I don't think {Name.title()} belongs to you!")
        try:
            newOwner = ctx.message.mentions[0]
        except:
            return await ctx.send(
                "You must @ a user in order to designate a new owner."
            )

        if ownerCheck == True:
            output = self.db.change_owner(Guild, Name, newOwner.id)
        else:
            output = f"I don't think you own {Name.title()}. Make sure you're trying to change ownership of the correct character profile!"

        await ctx.send(output)

    @char.command()
    async def add(self, ctx, *, Name):
        """
        Register a user's character.
        """
        try:
            _, Guild, _ = self.ctx_info(ctx)
        except:
            ID = ctx.author.id

            Guild = self.db.get_server_proxy(ID)

        try:
            ID = ctx.message.mentions[0].id
        except:
            ID = ctx.message.author.id

        Name = Name.lower()

        output = self.db.add_char(Guild, ID, Name)
        await ctx.send(output)

    @char.command()
    async def remove(self, ctx, *, Name):
        """
        Remove a user's character from the guild.
        """
        try:
            _, Guild, ID = self.ctx_info(ctx)
        except:
            ID = ctx.author.id
            Guild = self.db.get_server_proxy(ID)

        Name = Name.lower()

        ownerCheck = ""
        try:
            ownerCheck = self.db.char_owner(Guild, ID, Name)
        except:
            pass
        if ownerCheck == True:
            output = self.db.remove_char(Guild, ID, Name)
            await ctx.send(output)
        else:
            await ctx.send(f"{Name.title()} doesn't belong to you, or doesn't exist.")

    @char.command(aliases=["set"])
    async def addfield(self, ctx, Name, field: str, *, value):
        """
        Add a field to a character, or update a field to a new value.
        """
        Name = Name.lower()
        try:
            _, Guild, ID = self.ctx_info(ctx)
        except:
            ID = ctx.author.id
            Guild = self.db.get_server_proxy(ID)

        ownerCheck = ""

        try:
            ownerCheck = self.db.char_owner(Guild, ID, Name)
        except:
            await ctx.send(f"I don't think {Name.title()} belongs to you!")
        if ownerCheck == True:

            if field == "color":

                self.db.set_field(Guild, ID, Name, field, value)
                await ctx.send(f"{Name.title()}'s {field} value has been updated!")
            elif field in {"owner", "category", "public", "name"}:
                await ctx.send(
                    f"This value, {field.capitalize()}, is used for behind-the-scenes things, and cannot be modified. Sorry for the inconvenience!"
                )
            else:
                self.db.set_field(Guild, ID, Name, field, value)
                await ctx.send(f"{Name.title()}'s {field} value has been updated!")

    @char.command(aliases=["unset"])
    async def removefield(self, ctx, Name, field):
        """
        Remove a field from a character.
        """
        Name = Name.lower()

        try:
            _, Guild, ID = self.ctx_info(ctx)
        except:
            ID = ctx.author.id
            Guild = self.db.get_server_proxy(ID)

        ownerCheck = ""

        try:
            ownerCheck = self.db.char_owner(Guild, ID, Name)
        except:
            pass
        try:
            if ownerCheck == True:
                if field == "owner" or field == "name":
                    await ctx.send("Sorry, I can't let you do that.")
                else:
                    self.db.unset_field(Guild, ID, Name, field)
                    await ctx.send(f"{field} has been removed from {Name.title()}!")
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Remove Field",
                ctx.message.author,
            )

    @char.command(hidden=True)
    async def display(self, ctx, Name=None):
        """
        Display information regarding a stored character, including all stored fields.
        """

        def check(reaction, user):
            return reaction.message.id == msg.id and user == ctx.author

        async def reaction_reset(reaction, user):
            if reaction.message.id == msg.id and user == ctx.author:
                await msg.remove_reaction(reaction, user)

        try:
            _, Guild, ID = self.ctx_info(ctx)
        except:
            ID = ctx.author.id
            Guild = self.db.get_server_proxy(ID)

        try:
            user = ctx.message.mentions[0].id
            results = self.db.get_char_by_owner(Guild, user)
        except:
            if Name == None:
                try:
                    user = ctx.message.author.id
                    results = self.db.get_char_by_owner(Guild, user)

                except:
                    message = str(traceback.format_exc())
                    await self.logger.error(
                        self,
                        message,
                        self.__class__.__name__,
                        "char",
                        ctx.message.author,
                    )
            else:
                Name = Name.lower()
                results = self.db.get_char(Guild, Name)

        Guild = self.bot.get_guild(Guild)
        embeds = []
        for output in results:

            try:
                output["name"]
            except:
                continue
            try:
                if output["description"] != "":
                    description = output["description"]
                else:
                    description = " "
            except:
                description = " "
            embed = discord.Embed(
                title="__" + output["name"].title() + "__",
                description=description,
                color=int(str(output["color"]), 16),
            )

            try:

                embed.set_footer(
                    text=f"Owned by: { await Guild.fetch_member(int(output['owner']))}"
                )
            except:
                embed.set_footer(
                    text=f"Owned by: { await self.bot.fetch_user(output['owner'])} : USER NO LONGER IN SERVER"
                )

            del (
                output["_id"],
                output["owner"],
                output["name"],
                output["color"],
                output["public"],
            )
            keys = []
            vals = []

            for i in output.items():
                keys.append(i[0]), vals.append(i[1])

            for i in range(len(output)):
                if keys[i].lower() == "image":
                    embed.set_image(url=vals[i])
                elif keys[i].lower() == "token":
                    embed.set_thumbnail(url=vals[i])

                elif keys[i].lower() == "description":
                    pass

                else:
                    embed.add_field(name=str(keys[i]), value=str(vals[i]))

            try:
                if embed:
                    embeds.append(embed)
                else:
                    await ctx.send(f"It looks like {Name} doesn't exist!")
            except:
                message = str(traceback.format_exc())
                self.logger.error(
                    self,
                    message,
                    self.__class__.__name__,
                    "Display",
                    ctx.message.author,
                )

        if len(embeds) == 1:
            msg = await ctx.send(embed=embeds[0])

            await msg.add_reaction("❌")
            timeout = time.time() + 3600

            while True:
                if time.time() > timeout:
                    await msg.clear_reactions()
                    break
                try:
                    reaction, _ = await self.bot.wait_for(
                        "reaction_add", timeout=3600.0, check=check
                    )
                    if reaction.emoji == "❌":
                        await msg.delete()
                        break
                    else:
                        await reaction_reset(reaction, user)
                except:
                    pass

        else:
            page = 0

            msg = await ctx.send(embed=embeds[page])

            await msg.add_reaction("⏪")
            await msg.add_reaction("⬅️")
            await msg.add_reaction("🟥")
            await msg.add_reaction("➡️")
            await msg.add_reaction("⏩")
            await msg.add_reaction("❌")
            timeout = time.time() + 3600

            while True:
                if time.time() > timeout:
                    await msg.clear_reactions()
                    break
                try:
                    reaction, _ = await self.bot.wait_for(
                        "reaction_add", timeout=3600.0, check=check
                    )
                    if reaction.emoji == "⬅️" and page > 0:
                        page -= 1
                        await msg.edit(embed=embeds[page])
                        await reaction_reset(reaction, ctx.author)
                    elif reaction.emoji == "➡️" and page < len(embeds) - 1:
                        page += 1
                        await msg.edit(embed=embeds[page])
                        await reaction_reset(reaction, ctx.author)
                    elif reaction.emoji == "⏪" and page > 0:
                        page = 0
                        await msg.edit(embed=embeds[page])
                        await reaction_reset(reaction, ctx.author)
                    elif reaction.emoji == "⏩" and page < len(embeds) - 1:
                        page = len(embeds) - 1
                        await msg.edit(embed=embeds[page])
                        await reaction_reset(reaction, ctx.author)
                    elif reaction.emoji == "🟥":
                        await msg.clear_reactions()
                        break
                    elif reaction.emoji == "❌":
                        await msg.delete()
                        break
                    else:
                        await reaction_reset(reaction, ctx.author)
                except:
                    pass

    @char.command()
    async def webedit(self, ctx):
        """
        Sends a link to the Little Thunder Web Editor.
        """
        await ctx.send(
            "The LT Web Editor can be found at https://webthunder.herokuapp.com/"
        )

    @char.command()
    async def directory(self, ctx, detailLevel="Default"):
        try:
            try:
                _, Guild, user = self.ctx_info(ctx)
                Guild = self.bot.get_guild(Guild)
            except:
                user = ctx.author.id
                Guild = await self.bot.fetch_guild(int(self.db.get_server_proxy(user)))

            # members = await Guild.fetch_members(limit=None).flatten()
            embeds = []

            def check(reaction, user):
                return reaction.message.id == msg.id and user == ctx.author

            async def reaction_reset(reaction, user):
                if reaction.message.id == msg.id and user == ctx.author:
                    await msg.remove_reaction(reaction, user)

            async with ctx.typing():
                characters = list(self.db.get_all_char(Guild.id))
                characters = sorted(characters, key=lambda i: i["owner"])

                owners = [character["owner"] for character in characters]
                ownerList = []
                for owner in owners:
                    if owner not in ownerList:
                        ownerList.append(owner)

                if detailLevel.lower() == "verbose":
                    for character in characters:

                        try:
                            character["name"]
                        except:
                            continue
                        try:
                            if character["description"] != "":
                                description = character["description"]
                            else:
                                description = " "
                        except:
                            description = " "
                        embed = discord.Embed(
                            title="__" + character["name"].title() + "__",
                            description=description,
                            color=int(str(character["color"]), 16),
                        )
                        try:
                            embed.set_footer(
                                text=f"Owned by: { await Guild.fetch_member(character['owner'])}"
                            )

                        except:
                            embed.set_footer(
                                text=f"Owned by: { await self.bot.fetch_user(character['owner'])} : USER NO LONGER IN SERVER"
                            )

                        del (
                            character["_id"],
                            character["owner"],
                            character["name"],
                            character["color"],
                            character["public"],
                        )
                        keys = []
                        vals = []

                        for i in character.items():
                            keys.append(i[0]), vals.append(i[1])

                        for i in range(len(character)):
                            if keys[i] == "image":
                                embed.set_image(url=vals[i])
                            elif keys[i] == "token":
                                embed.set_thumbnail(url=vals[i])

                            elif keys[i] == "description":
                                pass

                            else:
                                embed.add_field(name=str(keys[i]), value=str(vals[i]))

                        try:
                            if embed:
                                embeds.append(embed)
                            else:
                                pass
                        except:
                            message = str(traceback.format_exc())
                            self.logger.error(
                                self,
                                message,
                                self.__class__.__name__,
                                "Display",
                                ctx.message.author,
                            )
                elif detailLevel.lower() == "expanded":
                    new_embeds = await self.paginate_embeds(Guild, embeds, ownerList)

                else:

                    for owner in ownerList:
                        characterList = self.db.get_char_by_owner(Guild.id, owner)

                        charList = ""
                        for character in characterList:

                            try:
                                character["name"]

                            except:
                                continue

                            charList += str(character["name"]).title() + "\n"

                        if charList != "":
                            try:
                                member = await Guild.fetch_member(owner)
                                embed = discord.Embed(
                                    description=charList,
                                    title=member.display_name,
                                    color=member.color,
                                )
                                embed.set_thumbnail(url=member.avatar_url)
                                embeds.append(embed)
                            except:
                                member = await self.bot.fetch_user(owner)
                                embed = discord.Embed(
                                    description=charList,
                                    title=member.name,
                                )
                                embed.set_thumbnail(url=member.avatar_url)
                                embed.set_footer(
                                    text="User may no longer be in this server."
                                )
                                embeds.append(embed)

            if len(embeds) == 1:
                msg = await ctx.send(embed=embeds[0])

                await msg.add_reaction("❌")

                timeout = time.time() + 3600

                while True:
                    if time.time() > timeout:
                        await msg.clear_reactions()
                        break
                    try:
                        reaction, _ = await self.bot.wait_for(
                            "reaction_add", timeout=3600.0, check=check
                        )
                        if reaction.emoji == "❌":
                            await msg.delete()
                            break
                        else:
                            await reaction_reset(reaction, user)
                    except:
                        pass

            else:
                page = 0

                msg = await ctx.send(embed=embeds[page])

                await msg.add_reaction("⏪")
                await msg.add_reaction("⬅️")
                await msg.add_reaction("🟥")
                await msg.add_reaction("➡️")
                await msg.add_reaction("⏩")
                await msg.add_reaction("❌")
                timeout = time.time() + 3600

                while True:
                    if time.time() > timeout:
                        await msg.clear_reactions()
                        break
                    try:
                        reaction, _ = await self.bot.wait_for(
                            "reaction_add", timeout=3600.0, check=check
                        )
                        if reaction.emoji == "⬅️" and page > 0:
                            page -= 1
                            await msg.edit(embed=embeds[page])
                            await reaction_reset(reaction, ctx.author)
                        elif reaction.emoji == "➡️" and page < len(embeds) - 1:
                            page += 1
                            await msg.edit(embed=embeds[page])
                            await reaction_reset(reaction, ctx.author)
                        elif reaction.emoji == "⏪" and page > 0:
                            page = 0
                            await msg.edit(embed=embeds[page])
                            await reaction_reset(reaction, ctx.author)
                        elif reaction.emoji == "⏩" and page < len(embeds) - 1:
                            page = len(embeds) - 1
                            await msg.edit(embed=embeds[page])
                            await reaction_reset(reaction, ctx.author)
                        elif reaction.emoji == "🟥":
                            await msg.clear_reactions()
                            break
                        elif reaction.emoji == "❌":
                            await msg.delete()
                            break
                        else:
                            await reaction_reset(reaction, ctx.author)
                    except:
                        pass

        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Macro", ctx.message.author
            )


def setup(bot):
    bot.add_cog(char(bot))
