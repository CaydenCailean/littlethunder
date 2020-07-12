import discord
import re
import requests
from bs4 import BeautifulSoup
from discord.ext import commands

# regex capture for searching items
validItem = re.compile(r"\[\[([\w\s\':]+)\]\]")


class poe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        # do not respond to your own messages, LT

        if message.author == self.bot.user:
            return

        # check message content for above regex capture, then proceed to navigate to the page for the item if it exists

        if validItem.search(message.content):

            site = requests.get(
                f"https://pathofexile.gamepedia.com/{validItem.search(message.content).group(1).replace(' ','_')}"
            )
            embed = discord.Embed(
                title=f"{validItem.search(message.content).group(1).replace(' ','_')}"
            )

            # pare down text from the site

            text = site.text

            soup = BeautifulSoup(text, "lxml")
            stats = str(soup.find("span", {"class": "item-stats"}))
            stats = stats.replace(r"</em>", "")
            stats = stats.replace('<em class="tc -value">', "")
            stats = stats.replace('<em class="tc -mod">', "")
            stats = stats.replace("</a>", "")

            testlist = stats.split("<br/>")
            print(testlist)
            output = ""

            for string in testlist:
                x = BeautifulSoup(string, "lxml")
                for y in x.stripped_strings:
                    output += y + "\n"

            # build an embed with the stats of the item and a link to the item

            embed.add_field(name="Stats", value=output)
            embed.add_field(
                name="Wiki Page",
                value=f"https://pathofexile.gamepedia.com/{validItem.search(message.content).group(1).replace(' ','_')}",
            )
            await message.channel.send(embed=embed)

        else:
            pass


def setup(bot):
    bot.add_cog(poe(bot))
