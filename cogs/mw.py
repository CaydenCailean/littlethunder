import requests
import discord
import json
import re
import ast
import collections
from discord.ext import commands


class mw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # mythweavers command group and subcommands
    @commands.group(pass_context=True)
    async def mw(self, ctx):
        """
        WIP. Not yet functional.

        
        """
        print("This doesn't do anything yet.")

    @mw.command(pass_context=True)
    async def sheettest(self, ctx, sheetid):

        # This will be renamed, but will be the command for pulling specific portions of the character

        charsheet = requests.get(
            f"https://www.myth-weavers.com/api/v1/sheets/sheets/{sheetid}"
        ).json()

        jsondata = charsheet["sheetdata"]["sheet_data"]["jsondata"]
        # jsondata = re.sub(r'\"', '', jsondata)

        # jsondata = json.dumps(jsondata, sort_keys = True, indent = 4)
        jsondata = json.loads(jsondata, object_pairs_hook=collections.OrderedDict)
        # jsondata = ast.literal_eval(jsondata)

        with open("test.txt", "w") as outfile:
            json.dump(jsondata, outfile)

        skillOut = []

        for k, v in jsondata.items():
            print(k, v)
            if k.find(r"skill"):
                skillOut.append(v)

        charname = charsheet["sheetdata"]["name"]

        embed = discord.Embed(title=f"{charname} Skills", description=skillOut)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(mw(bot))
