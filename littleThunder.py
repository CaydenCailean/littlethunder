import discord
import os
import configparser
import traceback
import time

from cogs.main import main
from cogs.info import info
from cogs.utility import utility
from cogs.rpg import rpg
from cogs.rand import rand
from cogs.lt_logger import lt_logger
from cogs.channels import channels
from discord.ext import commands
from dbinit import lt_db

# from cogs.economy import economy
from random import randint

# Read config and connect to db
if "DBNAME" in os.environ:
    config = {
        "dbname": os.environ["DBNAME"],
        "discordtoken": os.environ["DISCTOKEN"],
        "log_channel": os.environ["LOG_CHANNEL"],
        "DB_URI": os.environ["DB_URI"]
    }
else:
    cfg = configparser.ConfigParser()
    cfg.read("config.cfg")
    config = dict(cfg.items("prod"))

# separate configured credentials to their respect services.

discToken = {"discToken": config["discordtoken"]}["discToken"]

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True


# bot command prefix

bot = commands.Bot(command_prefix=".", case_insensitive=True, intents=intents)

# startup confirmation


@bot.command(pass_context="true", hidden="true")
async def list_guilds(ctx):
    """Lists all the guilds the bot is in."""
    guilds = [g.name for g in bot.guilds]
    guildids = [g.id for g in bot.guilds]

    glist = [x for x in zip(guilds, guildids)]
    m = "\n"
    for x in glist:
        m += str(x).replace("',", ":").replace("('", "").replace(")", "")
        m += "\n"

    await ctx.send(f"I am in {len(guilds)} guilds:{m}")


def weighted(pairs):
    total = sum(pair[0] for pair in pairs)
    r = randint(1, total)
    for (weight, value) in pairs:
        r -= weight
        if r <= 0:
            return value


@bot.command(pass_context="true", aliases=["pet"])
async def pat(ctx):
    user = ctx.author.display_name
    responses = [
        (50, "_closes his eyes, enjoying the pat thoroughly._"),
        (50, "_wags his tail energetically as he's pet._"),
        (50, f"_licks {user} appreciatively._"),
        (50, "_rolls over and exposes his belly for more rubs._"),
        (50, "_wags his tail happily as he's pet._"),
        (50, "_perks his ears as he's pet._"),
        (50, "_starts kicking his leg aggressively, scratching at the air in bliss._"),
        (50, "_pants softly, thoroughly enjoying the attention._"),
        (10, "_uwu_"),
        (10, "_owo_"),
        (1, """```
        ██████████████        
    ████▒▒▒▒    ░░  ▒▒████    
  ██▒▒▒▒██        ░░░░▒▒▒▒▓▓  
▓▓▒▒░░██        ░░▒▒░░▓▓▒▒▒▒▓▓
██░░░░██  ▓▓    ▒▒▓▓░░██░░▒▒██
░░██░░██        ▒▒▒▒░░██▒▒██░░
  ██░░██          ▒▒░░██░░██  
  ░░▓▓░░██  ████▓▓  ▓▓░░██░░  
    ░░  ██    ██    ██        
        ░░██      ██▓▓        
          ▒▒██████░░          
          ```""")
    ]
    await ctx.send(weighted(responses))


# connect to and initialize DB

lt_db = lt_db(config)
check = False
while check == False:
    try:
        check = lt_db.connect()
        check2 = False
        while check2 == False:
            try:
                lt_db.db_init()
                check2 = True
            except:
                print("DB init failed, retrying in 30 seconds...")
                lt_logger.error(bot, str(traceback.format_exc()), "Main", "DB init failed")
                time.sleep(30)


    except:
        print("DB connection failed, retrying in 30 seconds")
        lt_logger.error(bot, str(traceback.format_exc()), "Main", "DB Connection")
        time.sleep(30)

# add cogs before startup



bot.add_cog(main(bot, config["log_channel"]))
# bot.add_cog(economy(bot, lt_db, config["log_channel"]))
bot.add_cog(channels(bot, lt_db, config["log_channel"]))
bot.add_cog(info(bot, config["log_channel"]))
bot.add_cog(utility(bot, lt_db, config["log_channel"]))
bot.add_cog(rpg(bot, lt_db, config["log_channel"]))
bot.add_cog(rand(bot, lt_db, config["log_channel"]))
bot.add_cog(lt_logger(bot, config["log_channel"]))
bot.run(discToken)
