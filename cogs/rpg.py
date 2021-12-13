import dice
import discord
import re
import traceback
import time

from .lt_logger import lt_logger
from aiohttp import ClientSession
from discord import Webhook, AsyncWebhookAdapter
from discord.ext import commands


class rpg(commands.Cog):
    def __init__(self, bot, lt_db, channel):
        self.bot = bot
        self.db = lt_db
        self.channel = channel
        self.logger = lt_logger

    def ctx_info(self, ctx):
        return ctx.channel.category.id, ctx.guild.id, ctx.message.author.id



    async def macro_list(self, ctx, input):
        try:
            Total, embed = self.diceroll(ctx, input)
            await ctx.send(embed=embed)

            return Total
        except:
            message = str(traceback.format_exc())
            await self.logger.error(self, message, self.__class__.__name__, "Macro", ctx.message.author.name)
            await ctx.send("Didn't work!")

    def diceroll(self, ctx, input):
        try:
            input, discFooter = input.split("#", 1)
        except:
            pass
        isPlus = input.find("+")
        isMinus = input.find("-")

        outList = "placeHolder"
        outResults = []
        Total = 0

        try:
            if isPlus == -1 and isMinus == -1:
                try:
                    diceNum, diceVal = input.split("d")
                    if diceNum == "":
                        diceNum = "1"
                    try:
                        outList = dice.roll(input)
                    except Exception as e:
                        raise e

                except ValueError as e:
                    raise e

                try:
                    outList = dice.roll(input)
                except Exception as e:
                    raise Exception

                for i in outList:
                    Total += i
                    outResults.append(i)

            if isPlus != -1 or isMinus != -1:
                expr = re.split("[+-]", input)[0]

                diceNum, diceVal = expr.split("d")
                if diceNum == "":
                    diceNum = "1"

                outResults = dice.roll(expr)

                posmod = 0
                negmod = 0

                bonus = re.findall(r"(\+\d+)(?:(?!d))", input)

                for i in bonus:
                    posmod += int(i)

                bonusDice = re.findall(r"\+\d*d\d+", input)
                for i in bonusDice:
                    idiceNum, idiceVal = i.split("d")

                    if idiceNum == "+":
                        idiceNum = "1"
                    if int(idiceNum) > 100 or int(idiceVal) > 1000:
                        raise Exception(
                            "That's too many numbers. The limit to this value is 100d1000."
                        )
                    else:
                        outResults.extend(dice.roll(i))

                malus = re.findall(r"(\-\d+)(?:(?!d))", input)

                for i in malus:
                    negmod += int(i)

                malusDice = re.findall(r"\-\d*d\d+", input)
                for i in malusDice:
                    output = dice.roll(i)
                    idiceNum, idiceVal = i.split("d")

                    if idiceNum == "-":
                        idiceNum = "1"
                    if int(idiceNum) > 100 or int(idiceVal) > 1000:
                        raise Exception(
                            "That's too many numbers. The limit to this value is 100d1000."
                        )
                    else:
                        for i in output:
                            outResults.append(str(i))

                for i in outResults:
                    Total += int(i)
                Total += posmod
                Total += negmod

                if int(diceNum) > 100 or int(diceVal) > 1000:
                    raise Exception(
                        "That's too many numbers. The limit to this value is 100d1000."
                    )

            commentText = f"Rolling {input}"

            embed = discord.Embed(
                title=f"Results for {ctx.message.author.display_name}",
                description=commentText,
                color=ctx.message.author.color,
            )
            try:
                embed.set_footer(text=discFooter)
            except:
                pass

            embed.add_field(name="Results", value=outResults)
            embed.add_field(name="Total", value=Total)

            return Total, embed
        except Exception as e:
            raise e

    @commands.group(
        case_insensitive=True,
        invoke_without_command=True,
        aliases=["r", "roll", "dice"],
    )
    async def d(self, ctx, *, input: str):

        """
        Rolls dice using #d# format, with a maximum of 100d1000.

        You may add or subtract flat modifiers or dice by appending them to your initial #d# roll.

        Comments may be added to a dice output by appending the command with #, followed by the content of the comment you wish to be shown.
        """
        if ctx.invoked_subcommand is None:

            if input.find("!") != -1:
                _, Guild, ID = self.ctx_info(ctx)

                label = input.replace("!", "", 1)
                macro = self.db.dice_get(ID, Guild, label)

                [await self.macro_list(ctx, input) for input in macro]

            else:
                try:
                    Total, embed = self.diceroll(ctx, input)
                    await ctx.send(embed=embed)
                    return Total
                except:
                    message = str(traceback.format_exc())
                    await lt_logger.error(
                        self, message, self.__class__.__name__, "Macro", ctx.message.author.name
                    )

    @d.command(pass_context=True)
    async def save(self, ctx, Alias):
        """
        Saves a dice expression as a variable.

        Example:
        .d save Attack_Longsword 1d20+8
        """
        _, Guild, User = self.ctx_info(ctx)

        for line in ctx.message.content.splitlines():
            line = line.replace(f".d save {Alias} ", "")
            self.db.dice_add(User, Guild, Alias, line)

        await ctx.send(f"The {Alias} macro has been updated.")

    @d.command(pass_context=True)
    async def delete(self, ctx, Alias):
        """
        Removes a dice variable.

        Example:
        .d delete Attack_Longsword
        """
        _, Guild, User = self.ctx_info(ctx)
        outMessage = self.db.dice_delete(User, Guild, Alias)
        await ctx.send(outMessage)

    @commands.command(pass_context=True)
    async def ready(self, ctx, Alias, *, Value):
        """
        Readies an action's dice. Preserves comments through value
        """
        if ctx.invoked_subcommand == None:
            _, Guild, ID = self.ctx_info(ctx)
            outMessage = self.db.ready_set(ID, Guild, Alias, Value)
            await ctx.send(outMessage)

    @commands.command(pass_context=True)
    async def trigger(self, ctx, Alias):
        """
        Triggers a readied action.
        """
        pattern = r"(#\d|\D*)$"

        _, Guild, _ = self.ctx_info(ctx)
        trigger = self.db.ready_trigger(Guild, Alias.lower())
        User = self.bot.get_user(trigger["User"])

        check = re.search(pattern, trigger["Value"])

        if trigger != None:
            try:
                if check.group(1).find("#") == -1:

                    ctx.message.content = (
                        ctx.message.content
                        + " # "
                        + trigger["Value"]
                        + f": Being rolled for {User.display_name}"
                    )
                else:
                    start, end = trigger["Value"].split("#")
                    ctx.message.content = (
                        "# "
                        + end
                        + " :: "
                        + start
                        + f": Being rolled for {User.display_name}"
                    )

            except:
                ctx.message.content
                pass
            await self.d(ctx, trigger["Value"])
        else:
            await ctx.send(f"It looks like {Alias} was never readied.")

    @d.command(pass_context=True)
    async def ready_remove(self, ctx, Alias):
        """
        WIP. Do not use.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        dmCheck = self.db.owner_check(Guild, Category, ID)
        playerCheck = self.db.ready_get(ID, Guild, Alias.lower())
        if dmCheck == True or playerCheck == True:
            outMessage = self.db.ready_remove(Guild, Alias.lower())
            await ctx.send(outMessage)
        else:
            await ctx.send("Looks like either that doesn't exist, or you don't own it.")

    @commands.group(case_insensitive=True)
    async def init(self, ctx):
        """
        The init command keeps track of initiative within a channel category.

        Without a subcommand, this command will show the current initiative block.
        """
        if ctx.invoked_subcommand is None:
            try:
                Category, Guild, _ = self.ctx_info(ctx)
                initraw = self.db.init_get(Guild, Category)
                turnNum = int(self.db.turn_get(Guild, Category))

                for i in range(turnNum - 1):
                    moveEntry = initraw[0]
                    del initraw[0]
                    initraw.append(moveEntry)
                try:
                    mentionMe = initraw[0].get("ID")
                    char = initraw[0].get("Name")
                except:
                    pass

                output = ""
                for i in initraw:
                    del i["ID"], i["_id"]
                    outstring = f"{list(i.values())[0]} : {list(i.values())[1]}"
                    output += outstring + "\n"
                embed = discord.Embed(
                    Title=f"Initiative for {ctx.channel.category}", colour=0x00FF00
                )
                embed.add_field(name="Initiative", value=output)

                try:
                    await ctx.send(embed=embed)
                except Exception as e:
                    await ctx.send(
                        "Before requesting an initiative table, make sure initiative has been added."
                    )
                    raise e
                return mentionMe, char

            except:
                message = str(traceback.format_exc())
                await self.logger.error(
                    self, message, self.__class__.__name__, "Initiative", ctx.message.author.name
                )

    @init.command(pass_context=True, aliases=["display"])
    async def show(self, ctx):
        """
        Show current initiative block, and ping the owner of whichever combatant is currently up.
        """
        mentionMe, char = await self.init(ctx)
        await ctx.send(f"Hey, <@{mentionMe}>, {char} is up.")

    @init.command(aliases=["add"])
    async def new(self, ctx, name, dieRoll, mention=None):
        """
        Add a Combatant to the initiative table.

        Syntax:
        .init add [name] [dice]
        """

        Category, Guild, _ = self.ctx_info(ctx)
        try:
            try:
                float(dieRoll)
                outcome = float(dieRoll)
            except:
                try:
                    Total, embed = self.diceroll(ctx, dieRoll)
                    outcome = float(Total)
                except:
                    message = str(traceback.format_exc())
                    await lt_logger.error(
                        self, message, self.__class__.__name__, "Macro", ctx.message.author.name
                    )
            if mention != None:
                mention = mention.replace("<@!", "").replace(">", "")
            else:
                mention = ctx.message.author.id
            try:
                await ctx.send(embed=embed)
            except:
                pass
            try:
                self.db.init_add(Guild, Category, name, mention, outcome)
                await ctx.send(f"{name} has been added to the initiative counter.")
            except Exception as e:
                raise e
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Add Initiative Entry", ctx.message.author.name
            )

    @init.command(pass_context=True, aliases=["remove"])
    async def kill(self, ctx, name):
        """
        DM Only.

        Remove a combant from the initiative tracker.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        try:
            dmCheck = self.db.owner_check(Guild, Category, ID)
            initraw = self.db.init_get(Guild, Category)
            turnNum = int(self.db.turn_get(Guild, Category))

            if dmCheck == True:
                self.db.init_remove(Guild, Category, name)
                if turnNum == len(initraw):
                    self.db.turn_next(Guild, Category)
                await ctx.send(f"{name} has been removed from the initiative count.")
                await self.init(ctx)
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Remove Initiative Entry", ctx.message.author.name
            )

    @init.command()
    async def end(self, ctx):
        """
        DM Only.

        Clears the initiative table altogether. This cannot be undone.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        try:
            check = self.db.owner_check(Guild, Category, ID)
            if check == True:
                self.db.init_clear(Guild, Category)
                await ctx.send(
                    "Combat has ended, and the initiative table has been wiped clean!"
                )
            else:
                await ctx.send(
                    "It doesn't look like you're the DM here, so you probably don't need to worry about this one."
                )

        except:
            message = str(traceback.format_exc())
            await self.logger.error(self, message, self.__class__.__name__, "End Init", ctx.message.author.name)

    @init.command(aliases=["pass"])
    async def next(self, ctx):
        """
        Moves the initiative count to the next combatant.
        """

        Category, Guild, ID = self.ctx_info(ctx)
        initraw = self.db.init_get(Guild, Category)
        turnNum = self.db.turn_get(Guild, Category)
        current = initraw[turnNum - 1]["ID"]
        dmCheck = ""
        try:
            dmCheck = self.db.owner_check(Guild, Category, ID)
        except:
            pass
        if int(ID) == int(current) or dmCheck == True:
            self.db.turn_next(Guild, Category)
            await self.show(ctx)

        else:
            await ctx.send("I don't think it's your turn yet!")

    @init.command()
    async def delay(self, ctx, newInit):
        """
        Moves an existing combatant to a new initiative total.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        initraw = self.db.init_get(Guild, Category)
        turnNum = self.db.turn_get(Guild, Category)
        current = initraw[turnNum - 1]["ID"]
        Name = initraw[turnNum - 1]["Name"]
        dmCheck = self.db.owner_check(Guild, Category, ID)
        if int(ID) == int(current) or dmCheck == True:
            self.db.init_delay(Guild, Category, Name, newInit)

        else:
            await ctx.send("I don't think it's your turn yet!")
        await self.show(ctx)

    @init.command()
    async def setturn(self, ctx, newPos):
        """
        DM Only.

        Sets the current turn to an existing combatant, either by iniative total or combatant name.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        initraw = self.db.init_get(Guild, Category)
        dmCheck = self.db.owner_check(Guild, Category, ID)
        if dmCheck == True:
            try:
                newPos = int(newPos)
            except:
                pass

            if type(newPos) == str:
                for x in initraw:
                    if x["Name"] == newPos:
                        newPos = int(initraw.index(x)) + 1
                        break
                self.db.turn_set(Guild, Category, newPos)

            if type(newPos) == float and len(initraw) >= newPos:
                self.db.turn_set(Guild, Category, newPos)

            await self.show(ctx)
        else:
            await ctx.send("It looks like you have no power here.")

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
                    self, message, self.__class__.__name__, "Character Profile", ctx.message.author.name
                )

    @char.command()
    async def add(self, ctx, *, Name):
        """
        Register a user's character.
        """
        _, Guild, _ = self.ctx_info(ctx)

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
        _, Guild, ID = self.ctx_info(ctx)

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
        _, Guild, ID = self.ctx_info(ctx)
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
        _, Guild, ID = self.ctx_info(ctx)
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
                self, message, self.__class__.__name__, "Remove Field", ctx.message.author.name
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
            _, Guild, _ = self.ctx_info(ctx)
        except:
            await ctx.send("This command doesn't work in DMs!")

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
                        self, message, self.__class__.__name__, "char", ctx.message.author.name
                    )
            else:
                Name = Name.lower()
                results = self.db.get_char(Guild, Name)

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

            embed.set_footer(text=f"Owned by: { await self.bot.fetch_user(output['owner'])}")

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
                    await ctx.send(f"It looks like {Name} doesn't exist!")
            except:
                message = str(traceback.format_exc())
                self.logger.error(self, message, self.__class__.__name__, "Display", ctx.message.author.name)

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
            Guild = await self.bot.fetch_guild(ctx.guild.id)
            user = ctx.message.author.id
            #members = await Guild.fetch_members(limit=None).flatten()
            embeds = []

            def check(reaction, user):
                return reaction.message.id == msg.id and user == ctx.author

            async def reaction_reset(reaction, user):
                if reaction.message.id == msg.id and user == ctx.author:
                    await msg.remove_reaction(reaction, user)
            async with ctx.typing():
                characters = list(self.db.get_all_char(Guild.id))
                characters = (sorted(characters, key = lambda i: i['owner']))

                owners = [character['owner'] for character in characters]
                ownerList = []
                for owner in owners:
                    if owner not in ownerList:
                        ownerList.append(owner)

                for owner in ownerList:
                    charList = self.db.get_char_by_owner(Guild.id, owner)


                if detailLevel.lower() != "verbose":

                    owners = [character['owner'] for character in characters]
                    for owner in owners:
                        if owner not in ownerList:
                            ownerList.append(owner)

                    for owner in ownerList:
                        characterList = self.db.get_char_by_owner(Guild.id, owner)

                        charList = ''
                        for character in characterList:

                            try:
                                character["name"]

                            except:
                                continue

                            charList += (str(character["name"]).title() + '\n')

                        if charList != '':  
                            try: 
                                member = await self.bot.fetch_user(owner) 
                                embed = discord.Embed(description=charList, title=member.display_name, color=member.color)
                                embed.set_thumbnail(url=member.avatar_url)
                                embeds.append(embed)
                            except:
                                continue

                else:
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

                        embed.set_footer(text=f"Owned by: { await self.bot.fetch_user(character['owner'])}")

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
                            self.logger.error(self, message, self.__class__.__name__, "Display", ctx.message.author.name)





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



        except Exception as e:
            message = str(traceback.format_exc())
            await self.logger.error(self, message, self.__class__.__name__, "Macro", ctx.message.author.name)
            

def setup(bot):
    bot.add_cog(rpg(bot))
