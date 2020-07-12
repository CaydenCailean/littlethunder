import discord
import os
import time
import asyncio
import configparser
import re
from discord.ext import commands
from dbinit import lt_db
from cogs.info import info
from cogs.poe import poe
from cogs.utility import utility
from cogs.rpg import rpg
from cogs.mw import mw

# bot command prefix

bot = commands.Bot(command_prefix=".")

# startup confirmation


@bot.event
async def on_ready():
    print("I'm ready!")


# Read config and connect to db

cfg = configparser.ConfigParser()
cfg.read("config.cfg")
config = dict(cfg.items("prod"))

# separate configured credentials to their respect services.

twi_cred = {"accountsid": config["accountsid"], "authtoken": config["authtoken"]}
dis_cred = {"discToken": config["discordtoken"]}
discToken = dis_cred["discToken"]

# connect to and initialize DB

lt_db = lt_db(config)
lt_db.connect()
lt_db.db_init()

# add cogs before startup

bot.add_cog(info(bot))
bot.add_cog(poe(bot))
bot.add_cog(utility(bot))
bot.add_cog(rpg(bot, lt_db))
bot.add_cog(mw(bot))
bot.run(discToken)
