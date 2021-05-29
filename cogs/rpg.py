import discord
import re
import dice
import asyncio
from discord.ext import commands, tasks
import sys, traceback
from datetime import datetime

sys.path.append("..")
from dbinit import lt_db


class rpg(commands.Cog):
    def __init__(self, bot, lt_db):
        self.bot = bot
        self.lt_db = lt_db

    def ctx_info(self, ctx):
        Category = ctx.channel.category.id
        Guild = ctx.message.guild.id
        ID = ctx.message.author.id
        return Category, Guild, ID

    # region Dice

    @commands.group(
        case_insensitive=True,
        invoke_without_command=True,
        aliases=["r", "roll", "dice"],
    )
    async def d(self, ctx, input: str):

        """
        Rolls dice using #d# format, with a maximum of 100d1000.
        
        You may add or subtract flat modifiers or dice by appending them to your initial #d# roll.
        
        Comments may be added to a dice output by appending the command with #, followed by the content of the comment you wish to be shown.
        """
        if ctx.invoked_subcommand is None:

            if input.find("!") != -1:
                Guild = ctx.message.guild.id
                ID = ctx.message.author.id

                try:
                    input, sep, extra = re.split(r"([+|-])", input, maxsplit=1)
                    label = input.replace("!", "", 1)

                    input = self.lt_db.dice_get(ID, Guild, input.replace("!", ""))
                    inputDice = input
                    input = input + sep + str(extra)
                    commentText = f"Rolling {label} : {inputDice} + {str(extra)}"

                except:
                    label = input.replace("!", "", 1)
                    input = self.lt_db.dice_get(ID, Guild, input.replace("!", ""))
                    commentText = f"Rolling {label} : {input}"

            try:
                isPlus = input.find("+")
                isMinus = input.find("-")

                outList = "placeHolder"
                outResults = []
                Total = 0

                if isPlus == -1 and isMinus == -1:
                    try:
                        diceNum, diceVal = input.split("d")
                    except ValueError as e:
                        raise Exception("Make sure your expression is in #d# format.")

                    if diceNum == "":
                        diceNum = "1"
                    try:
                        outList = dice.roll(input)
                    except:
                        traceback.print_stack()
                    
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
                try:
                    commentText
                except:
                    commentText = f"Rolling {input}"
                try:
                    discFooter = re.search(r"#(.+)", ctx.message.content)
                    discFooter = f"\n{discFooter.group(0).replace('#', '')}"
                except Exception as e:
                    print(e)
                
                embed = discord.Embed(
                    title=f"Results for {ctx.message.author.display_name}",
                    description=commentText,
                    color=ctx.message.author.color,
                )
                if discFooter != None:
                    embed.set_footer(text=discFooter)
                else:
                    pass

                embed.add_field(name="Results", value=outResults)
                embed.add_field(name="Total", value=Total)   
                await ctx.send(embed=embed)
                return int(Total)
            except Exception as e:
                if str(e).find("not enough values") != -1:
                    await ctx.send("Not enough values.")
                elif str(e).find("400 bad request"):
                    await ctx.send(
                        "Either your dice phrase was not formatted correctly or you are rolling too many dice. Please try again."
                    )
                    print(e)
                return Total

    @d.command(pass_context=True)
    async def save(self, ctx, Alias, Value):
        """
        Saves a dice expression as a variable.

        Example:
        .d save Attack_Longsword 1d20+8
        """
        Guild = ctx.message.guild.id
        User = ctx.message.author.id
        self.lt_db.dice_add(User, Guild, Alias, Value)
        await ctx.send(
            f"{ctx.message.author.display_name} has added the variable {Alias} with the dice expression of {Value}."
        )

    @d.command(pass_context=True)
    async def delete(self, ctx, Alias):
        """
        Removes a dice variable.
        
        Example:
        .d delete Attack_Longsword
        """
        Guild = ctx.message.guild.id
        User = ctx.message.author.id
        outMessage = self.lt_db.dice_delete(User, Guild, Alias)
        await ctx.send(outMessage)

    # endregion

    # region Readied actions

    @commands.command(pass_context=True)
    async def ready(self, ctx, Alias, *, Value):
        """
        Readies an action's dice. Preserves comments through value
        """
        if ctx.invoked_subcommand == None:
            _, Guild, ID = self.ctx_info(ctx)
            outMessage = self.lt_db.ready_set(ID, Guild, Alias, Value)
            await ctx.send(outMessage)

    @commands.command(pass_context=True)
    async def trigger(self, ctx, Alias):
        """
        Triggers a readied action.
        """
        pattern = r"(#\d|\D*)$"

        Guild = ctx.message.guild.id
        trigger = self.lt_db.ready_trigger(Guild, Alias.lower())
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
        dmCheck = self.lt_db.owner_check(Guild, Category, ID)
        playerCheck = self.lt_db.ready_get(ID, Guild, Alias.lower())
        if dmCheck == True or playerCheck == True:
            outMessage = self.lt_db.ready_remove(Guild, Alias.lower())
            await ctx.send(outMessage)
        else:
            await ctx.send("Looks like either that doesn't exist, or you don't own it.")

    # endregion

    # region Initiative

    @commands.group(case_insensitive=True)
    async def init(self, ctx):
        """
        The init command keeps track of initiative within a channel category. 

        Without a subcommand, this command will show the current initiative block.
        """
        if ctx.invoked_subcommand is None:
            Category, Guild, _ = self.ctx_info(ctx)
            initraw = self.lt_db.init_get(Guild, Category)
            turnNum = int(self.lt_db.turn_get(Guild, Category))

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
            except:
                await ctx.send(
                    "Before requesting an initiative table, make sure initiative has been added."
                )

            return mentionMe, char

    @init.command(pass_context=True, aliases=["display"])
    async def show(self, ctx):
        """
        Show current initiative block, and ping the owner of whichever combatant is currently up.
        """
        mentionMe, char = await self.init(ctx)
        await ctx.send(f"Hey, <@{mentionMe}>, {char} is up.")

    @init.command(aliases=["add"])
    async def new(self, ctx, name, dieRoll):
        """
        Add a Combatant to the initiative table.

        Syntax:
        .init add [name] [dice]
        """

        Category, Guild, ID = self.ctx_info(ctx)
        try:
            float(dieRoll)
            outcome = float(dieRoll)
        except:
            outcome = float(await rpg.d(self, ctx, dieRoll))
        try:
            ID = ctx.message.mentions[0].id
        except:
            ID = ctx.message.author.id
        await ctx.send(f"{name} has been added to the initiative counter.")
        self.lt_db.init_add(Guild, Category, name, ID, outcome)

    @init.command(pass_context=True, aliases=["remove"])
    async def kill(self, ctx, name):
        """
        DM Only.

        Remove a combant from the initiative tracker.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        dmCheck = self.lt_db.owner_check(Guild, Category, ID)
        initraw = self.lt_db.init_get(Guild, Category)
        turnNum = int(self.lt_db.turn_get(Guild, Category))

        if dmCheck == True:
            self.lt_db.init_remove(Guild, Category, name)
            if turnNum == len(initraw):
                self.lt_db.turn_next(Guild, Category)
            await ctx.send(f"{name} has been removed from the initiative count.")
            await self.init(ctx)

    @init.command()
    async def end(self, ctx):
        """
        DM Only.

        Clears the initiative table altogether. This cannot be undone.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        check = self.lt_db.owner_check(Guild, Category, ID)
        if check == True:
            self.lt_db.init_clear(Guild, Category)
            await ctx.send(
                "Combat has ended, and the initiative table has been wiped clean!"
            )
        else:
            await ctx.send(
                "It doesn't look like you're the DM here, so you probably don't need to worry about this one."
            )

    @init.command(aliases=["pass"])
    async def next(self, ctx):
        """
        Moves the initiative count to the next combatant.
        """

        Category, Guild, ID = self.ctx_info(ctx)
        initraw = self.lt_db.init_get(Guild, Category)
        turnNum = self.lt_db.turn_get(Guild, Category)
        current = initraw[turnNum - 1]["ID"]
        dmCheck = ""
        try:
            dmCheck = self.lt_db.owner_check(Guild, Category, ID)
        except:
            pass
        if int(ID) == int(current) or dmCheck == True:
            self.lt_db.turn_next(Guild, Category)
            await self.show(ctx)

        else:
            await ctx.send("I don't think it's your turn yet!")

    @init.command()
    async def delay(self, ctx, newInit):
        """
        Moves an existing combatant to a new initiative total.
        """
        Category, Guild, ID = self.ctx_info(ctx)
        initraw = self.lt_db.init_get(Guild, Category)
        turnNum = self.lt_db.turn_get(Guild, Category)
        current = initraw[turnNum - 1]["ID"]
        Name = initraw[turnNum - 1]["Name"]
        dmCheck = self.lt_db.owner_check(Guild, Category, ID)
        if int(ID) == int(current) or dmCheck == True:
            self.lt_db.init_delay(Guild, Category, Name, newInit)

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
        initraw = self.lt_db.init_get(Guild, Category)
        dmCheck = self.lt_db.owner_check(Guild, Category, ID)
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
                self.lt_db.turn_set(Guild, Category, newPos)

            if type(newPos) == int and len(initraw) >= newPos:
                self.lt_db.turn_set(Guild, Category, newPos)

            await self.show(ctx)
        else:
            await ctx.send("It looks like you have no power here.")

    # endregion

    # region DM Claim

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
        output = self.lt_db.add_owner(Guild, Category, ID)
        await ctx.send(output)

    @dm.command()
    async def unclaim(self, ctx):
        """Unclaim current dm for category. Administrators and the Current DM are the only users able to perform this action."""
        Category, Guild, ID = self.ctx_info(ctx)
        override = ctx.message.author.permissions_in(ctx.channel).administrator
        output = self.lt_db.remove_owner(Guild, Category, ID, override)
        await ctx.send(output)

    # endregion

    # region Character Profiles

    @commands.group(case_insensitive=True)
    async def char(self, ctx):
        """
        Use to display a character's profile, if one exists. Subcommands cover the creation and alteration of character profiles.

        All characters are saved on a per-guild basis.
        """

        if ctx.invoked_subcommand is None:
            Name = ctx.message.content.lstrip(" ")
            await self.display(ctx, Name)

    @char.command()
    async def add(self, ctx, *, Name):
        """
        Register a user's character.
        """
        _, Guild, ID = self.ctx_info(ctx)

        try:
            ID = ctx.message.mentions[0].id
        except:
            ID = ctx.message.author.id

        Name = Name.lower()

        output = self.lt_db.add_char(Guild, ID, Name)
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
            ownerCheck = self.lt_db.char_owner(Guild, ID, Name)
        except:
            pass
        if ownerCheck == True:
            output = self.lt_db.remove_char(Guild, ID, Name)
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
        field = field.lower()
        ownerCheck = ""
        try:
            ownerCheck = self.lt_db.char_owner(Guild, ID, Name)
        except:
            await ctx.send(f"I don't think {Name.title()} belongs to you!")
        if ownerCheck == True:

            if field == "color":

                self.lt_db.set_field(Guild, ID, Name, field, value)
                await ctx.send(f"{Name.title()}'s {field} value has been updated!")
            elif field in {"owner", "category", "public", "name"}:
                await ctx.send(
                    f"This value, {field.capitalize()}, is used for behind-the-scenes things, and cannot be modified. Sorry for the inconvenience!"
                )
            else:
                self.lt_db.set_field(Guild, ID, Name, field, value)
                await ctx.send(f"{Name.title()}'s {field} value has been updated!")

    @char.command(aliases=["unset"])
    async def removefield(self, ctx, Name, field):
        """
        Remove a field from a character.
        """
        Name = Name.lower()
        _, Guild, ID = self.ctx_info(ctx)
        field = field.lower()
        ownerCheck = ""

        try:
            ownerCheck = self.lt_db.char_owner(Guild, ID, Name)
        except:
            pass
        if ownerCheck == True:
            if field == "owner" or field == "name":
                await ctx.send("Sorry, I can't let you do that.")
            else:
                self.lt_db.unset_field(Guild, ID, Name, field)
                await ctx.send(f"{field} has been removed from {Name.title()}!")

    @char.command(hidden=True)
    async def display(self, ctx, Name):
        """
        Display information regarding a stored character, including all stored fields.
        """
        Name = Name.lower()
        Guild = ctx.message.guild.id
        results = self.lt_db.get_char(Guild, Name)

        for output in results:

            embed = discord.Embed(
                title="__" + output["name"].title() + "__",
                description=output["description"],
                color=int(str(output["color"]), 16),
            )

            del (
                output["_id"],
                output["owner"],
                output["name"],
                output["description"],
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
                else:
                    embed.add_field(name=str(keys[i]), value=str(vals[i]))
            if embed:
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"It looks like {Name} doesn't exist!")

    @char.command()
    async def webedit(self, ctx):
        """
        Sends a link to the Little Thunder Web Editor.
        """
        await ctx.send(
            "The LT Web Editor can be found at https://webthunder.herokuapp.com/"
        )


# endregion


def setup(bot):
    bot.add_cog(rpg(bot))
