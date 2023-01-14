import os
import discord
import logging, logging.handlers
from dotenv import load_dotenv
import asyncio
from discord.ext import commands
import re
from pprint import pprint

# cogs
from cogs.puggers import Puggers
from cogs.karma import Karma

# logging
handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)

discord.utils.setup_logging(handler=handler, level=logging.ERROR)

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix=('!', '~'), intents=intents)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

async def main():

    await client.add_cog(Puggers(bot=client))
    await client.add_cog(Karma(bot=client))

    async with client:
        await client.start(TOKEN)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

if __name__ == '__main__':
    asyncio.run(main())
