import discord
import os
import configparser
from discord.ext import commands
from dbinit import lt_db
from cogs.main import main
from cogs.info import info
from cogs.utility import utility
from cogs.rpg import rpg
from cogs.mw import mw
from cogs.rand import rand
from cogs.lt_logger import lt_logger
from cogs.channels import channels
#from cogs.economy import economy
from random import randint

# Read config and connect to db
if "DBUSER" in os.environ:
    config = {
        "user": os.environ["DBUSER"],
        "pass": os.environ["DBPASS"],
        "host": os.environ["DBHOST"],
        "port": os.environ["DBPORT"],
        "dbname": os.environ["DBNAME"],
        "discordtoken": os.environ["DISCTOKEN"],
        "log_channel": os.environ["LOG_CHANNEL"],
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
    await ctx.send(f"I am in {len(guilds)} guilds: {', '.join(guilds)}.\n Their IDs are: {guildids}")

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
        (10, "_closes his eyes, enjoying the pat thoroughly._"),
        (10, "_wags his tail energetically as he's pet._"),
        (10, f"_licks {user} appreciatively._"),
        (10, "_rolls over and exposes his belly for more rubs._"),
        (1, "_uwu_"),
    ]
    await ctx.send(weighted(responses))

# connect to and initialize DB

lt_db = lt_db(config)
lt_db.connect()
lt_db.db_init()

# add cogs before startup


bot.add_cog(main(bot, config["log_channel"]))
#bot.add_cog(economy(bot, lt_db, config["log_channel"]))
bot.add_cog(channels(bot, lt_db, config["log_channel"]))
bot.add_cog(info(bot, config["log_channel"]))
bot.add_cog(utility(bot, lt_db, config["log_channel"]))
bot.add_cog(rpg(bot, lt_db, config["log_channel"]))
bot.add_cog(rand(bot, lt_db, config["log_channel"]))
bot.add_cog(mw(bot, config["log_channel"]))
bot.add_cog(lt_logger(bot, config["log_channel"]))
bot.run(discToken)
