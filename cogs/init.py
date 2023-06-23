import discord
import traceback

from discord.ext import commands
from discord import app_commands

from .lt_logger import lt_logger
from .dice import dice


class init(commands.GroupCog):
    def __init__(self, bot, lt_db, channel):
        self.bot = bot
        self.db = lt_db
        self.logger = lt_logger
        self.channel = channel
        

    def init_display(self, category, guild):
        initraw = self.db.init_get(guild, category)
        turnNum = int(self.db.turn_get(guild, category))
        Guild = self.bot.get_guild(guild)
        Category = discord.utils.get(Guild.categories, id=category)
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
        embed = discord.Embed(title=f"Initiative for {Category.name}", colour=0x00FF00)
        embed.add_field(name="Initiative", value=output)
        return embed, mentionMe, char

    @app_commands.command()
    async def display(self, interaction: discord.Interaction):
        """
        The init command keeps track of initiative within a channel category.

        Without a subcommand, this command will show the current initiative block.
        """
        
        try:
           
            embed, _, _ = self.init_display(interaction.channel.category.id, interaction.guild.id)
            
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(
                    "Before requesting an initiative table, make sure initiative has been added to this category.", ephemeral=True
                )
                raise e
        
            

        except Exception as e:
            await interaction.response.send_message(
                    "Before requesting an initiative table, make sure initiative has been added to this category.", ephemeral=True
                )
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Initiative",
                interaction.user.global_name,
            )

    @app_commands.command()
    async def ping(self, interaction: discord.Interaction):
        """
        Show current initiative block, and ping the owner of whichever combatant is currently up.
        """
        try:
            embed, mentionMe, char = self.init_display(interaction.channel.category.id, interaction.guild.id)
            await interaction.response.send_message(embed=embed)
            await self.bot.get_channel(interaction.channel.id).send(f"Hey, <@{mentionMe}>, {char} is up.")
        except Exception as e:
            print(e)
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Initiative",
                interaction.user,
            )

    @app_commands.command(description="Adds a combatant to the initiative table. @ a user to add them as a player for a combatant.")
    async def new(self, interaction: discord.Interaction, name: str, notation: str, user: str =None):
        """
        Add a Combatant to the initiative table.

        Syntax:
        .init add [name] [dice]
        """
        
        Category, Guild, _ = dice.ctx_info(self, interaction)
        try:
            try:
                float(notation)
                outcome = float(notation)
            except:
                
                try:
                    Total, embed = dice.diceroll(self, interaction, notation, None)
                    
                    outcome = float(Total)
                except:
                    message = str(traceback.format_exc())
                    await lt_logger.error(
                        self,
                        message,
                        self.__class__.__name__,
                        "Macro",
                        interaction.user,
                    )
            if user == None:
                user = interaction.user.id
            else:
                user = user.replace("<", "").replace(">", "").replace("@", "").replace("!", "")
            try:
                await interaction.response.send_message(embed=embed)
            except:
                pass
            try:
                self.db.init_add(Guild, Category, name, user, outcome)
                await self.bot.get_channel(interaction.channel.id).send(f"{name} has been added to the initiative counter.")
            except Exception as e:
                raise e
        except:
            print(e)
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Add Initiative Entry",
                interaction.user,
            )

    @app_commands.command(description="Removes a combatant from the initiative table. DM Only.")
    async def kill(self, interaction: discord.Interaction, name: str):
        Category, Guild, ID = dice.ctx_info(self, interaction)
        try:
            dmCheck = self.db.owner_check(Guild, Category, ID)
            initraw = self.db.init_get(Guild, Category)
            turnNum = int(self.db.turn_get(Guild, Category))

            if dmCheck == True:
                deleted = self.db.init_remove(Guild, Category, name)
                
                if turnNum == len(initraw):
                    self.db.turn_next(Guild, Category)
                if deleted > 0:
                    await interaction.response.send_message(f"{name} has been removed from the initiative count.")
                    embed, _, _ = self.init_display(Category, Guild)
                    await self.bot.get_channel(interaction.channel.id).send(embed=embed)
                else:
                    await interaction.response.send_message(f"{name} was not found in the initiative count.", ephemeral=True)
                
        except:
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Remove Initiative Entry",
                interaction.user,
            )

    @app_commands.command(description="Ends the current combat. DM Only. Cannot be undone.")
    async def end(self, interaction: discord.Interaction):
        """
        DM Only.

        Clears the initiative table altogether. This cannot be undone.
        """
        
        Category, Guild, ID = dice.ctx_info(self, interaction)
        

        try:
            check = self.db.owner_check(Guild, Category, ID)
            if check == True:
                self.db.init_clear(Guild, Category)
                await interaction.response.send_message(
                    "Combat has ended, and the initiative table has been wiped clean!"
                )
            else:
                await interaction.response.send_message(
                    "It doesn't look like you're the DM here, so you probably don't need to worry about this one."
                )

        except Exception as e:
            print(e)
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "End Init",
                interaction.user,
            )

    @app_commands.command(description="Moves the initiative count to the next combatant.")
    async def next(self, interaction: discord.Interaction):

        
        Category, Guild, ID = dice.ctx_info(self, interaction)
        initraw = self.db.init_get(Guild, Category)
        turnNum = self.db.turn_get(Guild, Category)
        current = initraw[turnNum - 1]["ID"]
        
        dmCheck = ""
        try:
            dmCheck = self.db.owner_check(Guild, Category, ID)
        except Exception as e:
            print(e)
            
        try:    
            if int(ID) == int(current) or dmCheck == True:
                next = self.db.turn_next(Guild, Category)
                embed, _, _ = self.init_display(Category, Guild)
                await interaction.response.send_message(embed=embed)
                await self.bot.get_channel(interaction.channel.id).send(f"It is now {self.bot.get_user(next).mention}'s turn.")

        except Exception as e:
            print(e)
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Next Initiative",
                interaction.user,
            )
        else:
            await interaction.response.send_message("I don't think it's your turn yet!")

    @app_commands.command()
    async def delay(self, interaction: discord.Interaction, new_init: float):
        """
        Moves an existing combatant to a new initiative total.
        """
        Category, Guild, ID = dice.ctx_info(self, interaction)
        initraw = self.db.init_get(Guild, Category)
        turnNum = self.db.turn_get(Guild, Category)
        current = initraw[turnNum - 1]["ID"]
        Name = initraw[turnNum - 1]["Name"]
        dmCheck = self.db.owner_check(Guild, Category, ID)
        
        if int(ID) == int(current) or dmCheck == True:
            self.db.init_delay(Guild, Category, Name, new_init)

        else:
            await interaction.response.send_message("I don't think it's your turn yet!", ephemeral=True)
        # init display
        try:
            embed, _, _ = self.init_display(Category, Guild)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            user = self.db.init_get(Guild,Category)[turnNum-1]["ID"]
            await self.bot.get_channel(interaction.channel.id).send(f"It is now {self.bot.get_user(user).mention}'s turn.")
        except Exception as e:
            print(e)
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Delay Initiative",
                interaction.user,
            )
    @app_commands.command(description="Sets the initiative count to a specific combatant, by name.")
    async def setturn(self, interaction: discord.Interaction, name: str):
        try:
            Category, Guild, ID = dice.ctx_info(self, interaction)
            initraw = self.db.init_get(Guild, Category)
            dmCheck = self.db.owner_check(Guild, Category, ID)
            if dmCheck == True:
                if type(name) == str:
                    new_turn = None
                    for x in initraw:
                        if x["Name"] == name:
                            new_turn = int(initraw.index(x)) + 1
                            break
                        
                    if not new_turn:
                        await interaction.response.send_message(f"{name} was not found in the initiative count.", ephemeral=True)
                        return
                    self.db.turn_set(Guild, Category, new_turn)

                if type(new_turn) == float and len(initraw) >= new_turn:
                    self.db.turn_set(Guild, Category, new_turn)

                embed,_,_ = self.init_display(Category, Guild)
                await interaction.response.send_message(embed=embed)
                await self.bot.get_channel(interaction.channel.id).send(f"It is now {self.bot.get_user(initraw[new_turn-1]['ID']).mention}'s turn.")
            else:
                await interaction.response.send_message("It looks like you have no power here.", ephemeral=True)
        except Exception as e:
            print(e)
            message = str(traceback.format_exc())
            await self.logger.error(
                self,
                message,
                self.__class__.__name__,
                "Set Initiative",
                interaction.user,
            )

def setup(bot):
    bot.add_cog(init(bot))