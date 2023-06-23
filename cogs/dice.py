import d20
import discord
import re
import traceback
import json

from .lt_logger import lt_logger

from discord import app_commands
from discord.ext import commands


class LTStringifier(d20.SimpleStringifier):
    def _stringify(self, node) -> str:
        if not node.kept:
            return "X"
        return super()._stringify(node)

    def _str_expression(self, node):
        return (
            f'{{"result": {int(node.total)}, "rolled": "{self._stringify(node.roll)}"}}'
        )


class dice(commands.GroupCog, group_name="dice"):
    def __init__(self, bot, lt_db, channel):
        self.bot = bot
        self.db = lt_db
        self.logger = lt_logger
        self.channel = channel

    def ctx_info(self, interaction):
        return (
            interaction.channel.category.id,
            interaction.guild.id,
            interaction.user.id,
        )

    async def macro_list(self, ctx, input):
        try:
            Total, embed = self.diceroll(ctx, input)
            await ctx.send(embed=embed)

            return Total
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Macro", ctx.message.author
            )
            await ctx.send("Didn't work!")

    def diceroll(self, interaction, input, comment):

        try:
            notation = input
            if input.find("#") != -1:
                diceNum, input = input.split("#", 1)
            else:
                diceNum = 1

            results = []

            for _ in range(int(diceNum)):
                results.append(
                    json.loads(str(d20.roll(input, stringifier=LTStringifier())))
                )

            try:
                embed = discord.Embed(
                    title=f"Results for {interaction.user.display_name}",
                    description=f"Rolling {notation}",
                    color=interaction.user.color,
                )
            except Exception as e:
                print(e)

            try:
                embed.set_footer(text=comment)
            except:
                pass

            if len(results) > 1:
                for i in range(len(results)):
                    embed.add_field(
                        name=f"Total {i+1}", value=results[i]["result"], inline=False
                    )
                    embed.add_field(name=f"Rolls {i+1}", value=results[i]["rolled"])
            else:
                embed.add_field(name=f"Total", value=results[0]["result"])
                embed.add_field(name=f"Rolls", value=results[0]["rolled"])

            if len(results) == 1:
                intReturn = results[0]["result"]
            else:
                intReturn = "Multiple Outputs"

            return intReturn, embed
        except:
            raise Exception

    async def macro_eval(self, interaction, notation, macros, Guild, ID, comment=None):

        regex = re.compile(r"\!\w+")

        if comment is None:
            comment = notation

        try:
            for macro in macros:

                # for each macro, replace it with the macro's value
                label = macro.replace("!", "", 1)
                val = self.db.dice_get(ID, Guild, label)
                comment = notation.replace(macro, f"{label}:{val[0]}")

                if len(val) > 1:
                    for value in val:
                        # each val is a single diceroll
                        macros = regex.findall(value)
                        if macros:
                            await self.macro_eval(interaction, value, macros, Guild, ID)

                else:

                    notation = notation.replace(macro, val[0], 1)
                    macros = regex.findall(notation)
                    if macros:
                        return await self.macro_eval(
                            interaction, notation, macros, Guild, ID
                        )
                # macros = regex.findall(notation)
                # if macros:
                #    return await self.macro_eval(interaction, notation, macros, Guild, ID)

            if notation.find("!") == -1:
                Total, embed = self.diceroll(interaction, notation, comment)
                channel = interaction.channel.id
                try:
                    await interaction.response.send_message(embed=embed)
                except:
                    await self.bot.get_channel(channel).send(embed=embed)
                return Total
        except Exception as e:
            print(e)
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Macro",
                interaction.user.global_name,
            )
            await interaction.response.send_message(
                "Sorry, that didn't work! Make sure your macro is formatted correctly."
            )

    # discord.py slash command
    @app_commands.command(description="Rolls dice and/or performs mathematical operations.")
    async def roll(
        self, interaction: discord.Interaction, notation: str, comment: str = None
    ):
        """
        Rolls dice and/or performs mathematical operations.

        Dice can be compounded, such as 1d10+2d6, have modifiers added, like 1d20+3, or use a variety of flags, listed below. These flags can be used together.

        k - Keep - Keep all matched values - 8d6k6 only keeps results of 6.
        p - Drop - Drops all matched values - 8d6p<3 drops all dice less than 3.
        rr - Reroll - Rerolls matched values until none match - 8d6rr1 rerolls all ones until there are not any ones.
        ro - Reroll once - Rerolls all matched values once - 8d6ro1 rerolls any of the first eight dice if they roll a one.
        ra - Reroll and add - Reroll once, keeping the original roll.
        e - Explode - Rolls a die for each match - 8d6e6 rerolls all sixes and adds them to the total.
        mi - Minimum - Sets a minimum value for each die rolled - 8d6mi3 gives a minimum of 3 on any single die.
        ma - Maximum - Sets a maximum value for each die rolled - 8d6ma5 gives a maximum of 5 on any single die.
        """

        # await interaction.response.defer()

        _, Guild, ID = self.ctx_info(interaction)
        # Check if the user has a macro for this command

        regex = re.compile(r"\!\w+")
        macros = regex.findall(notation)

        if macros:

            return await self.macro_eval(interaction, notation, macros, Guild, ID)

        else:
            try:

                Total, embed = self.diceroll(interaction, notation, comment)

                await interaction.response.send_message(embed=embed)
                return Total
            except Exception as e:
                print(e)
                message = str(traceback.format_exc())
                await lt_logger.error(
                    self,
                    message,
                    self.__class__.__name__,
                    "Dice",
                    interaction.user,
                )

    @app_commands.command(description="Save dice macros for later use. For multiple expressions, separate with a pipe (|)")
    async def save(self, interaction: discord.Interaction, alias: str, value: str):
        """
        Saves a dice expression as a variable. Overwrites existing variables. Consecutive expressions can be added after a pipe (|) in order to roll multiple dice at once.

        Example:
        .d save Attack_Longsword 1d20+8

        This will save the dice expression as Attack_Longsword.

        Example of using macros:
        .d !Attack_Longsword
        """
        _, Guild, User = self.ctx_info(interaction)
        value = value.replace(" ", "")
        try:

            Value = []
            for line in value.split('|'):
                
                line = line.replace(f".d save {alias} ", "")
                Value.append(line)

            updoot = {"$set": {"user": User, "alias": alias.lower(), "Value": Value}}
            self.db.dice_add(User, Guild, alias, updoot)

            await interaction.response.send_message(ephemeral=True, content=f"The {alias} macro has been updated.")

        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Macro", interaction.user
            )

    @app_commands.command(description="Delete a dice macro.")
    async def delete(self, interaction: discord.Interaction, alias: str):
        """
        Removes a dice variable.

        Example:
        .d delete Attack_Longsword
        """
        _, Guild, User = self.ctx_info(interaction)
        outMessage = self.db.dice_delete(User, Guild, alias)
        await interaction.response.send_message(outMessage, ephemeral=True)

    @app_commands.command(description="Lists all dice variables.")
    async def list(self, interaction: discord.Interaction):
        """
        Lists all dice variables.
        """
        try:
            _, Guild, User = self.ctx_info(interaction)
            macroDict = self.db.dice_list(User, Guild)

            description = "```\n"
            max_len = max([len(x) for x in macroDict.keys()])

            for k, v in macroDict.items():
                for i in v:
                    if i == v[0]:
                        description += f"{k:<{max_len+1}}: {i}\n"

                    else:
                        description += f"{'':<{max_len+3}}{i}\n"

            description += "```"
            embed = discord.Embed(
                title=f"Dice Variables for {interaction.user.display_name}",
                description=description,
                color=interaction.user.color,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self, message, self.__class__.__name__, "Macro", interaction.user
            )

def setup(bot):
    bot.add_cog(dice(bot))
