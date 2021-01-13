import discord
import os
import time
import asyncio
import configparser
import re
import random
from discord.ext import commands
from dbinit import lt_db
from cogs.info import info
from cogs.utility import utility
from cogs.rpg import rpg
from cogs.mw import mw

# bot command prefix

bot = commands.Bot(command_prefix=".", case_insensitive=True)

# startup confirmation


@bot.event
async def on_ready():
    print("I'm ready!")

def weighted_random(pairs):
    total = sum(pair[0] for pair in pairs)
    r = random.randint(1, total)
    for (weight, value) in pairs:
        r -= weight
        if r <= 0: return value

@bot.command(pass_context="true", no_pm="true", aliases=["pet"])
async def pat(ctx):
    user = ctx.author.display_name
    responses = [
        (10, "_closes his eyes, enjoying the pat thoroughly._"),
        (10, "_wags his tail energetically as he's pet._"),
        (10, f"_licks {user} appreciatively._"),
        (10, "_rolls over and exposes his belly for more rubs._"),
        (1, "_uwu_")
    ]
    await ctx.send(weighted_random(responses))


# Read config and connect to db
if "DBUSER" in os.environ:
    config = {
        "user": os.environ["DBUSER"],
        "pass": os.environ["DBPASS"],
        "host": os.environ["DBHOST"],
        "port": os.environ["DBPORT"],
        "dbname": os.environ["DBNAME"],
        "discordtoken": os.environ["DISCTOKEN"],
    }
else:
    cfg = configparser.ConfigParser()
    cfg.read("config.cfg")
    config = dict(cfg.items("prod"))

# separate configured credentials to their respect services.

discToken = {"discToken": config["discordtoken"]}["discToken"]


# connect to and initialize DB

lt_db = lt_db(config)
lt_db.connect()
lt_db.db_init()

# add cogs before startup

bot.add_cog(info(bot))
bot.add_cog(utility(bot))
bot.add_cog(rpg(bot, lt_db))
bot.add_cog(mw(bot))
bot.run(discToken)
