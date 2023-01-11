from discord.ext import commands
import json
from dotenv import load_dotenv
from urllib import parse, request
import os
import random

class Puggers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None      

    @commands.command()
    async def pugbomb(self, ctx):
        load_dotenv(dotenv_path='../.env')
        params = parse.urlencode({
            "q": "pug",
            "api_key": f"{os.getenv('GIPHY_TOKEN')}",
            "limit": "25"
        })
        url = "http://api.giphy.com/v1/gifs/search"
        with request.urlopen("".join((url, "?", params))) as response:
            data = json.loads(response.read())
        
        urls = []
        for key, value in data.items():
            if key == "data":
                for dict in value:
                    urls.append(dict["url"])
        
        select_5 = random.sample(urls, 5)
        for entry in select_5:
            await ctx.send(entry)