from discord.ext import commands
import json
from dotenv import load_dotenv
from urllib import parse, request
import os
import random

class Factoids(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None


def check_prefix(ctx):  
        return ctx.prefix == "~"

@commands.check(check_prefix)
@commands.command()