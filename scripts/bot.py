import os
import re
import discord
import logging, logging.handlers
from dotenv import load_dotenv
import asyncpg
import asyncio

class KarmaNameError(Exception):
    pass

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            intents=intents,
        )

    async def setup_hook(self):
        db = await asyncpg.create_pool(**CREDENTIALS)

        create_karma = ''' CREATE TABLE IF NOT EXISTS karma_table (
            name    varchar(40) PRIMARY KEY,
            karma   int) '''

        await db.execute(create_karma)
        await db.close()

    async def on_ready(self):
        print(f'{client.user} has connected to Discord!')

    async def on_message(self, message):
        content = message.content
        channel = message.channel
            
        karma_matches = re.findall(r"(?:\S+)+(?:\s|)(?:\+\+|--|—)|\(.*?\)(?:\s|)--|\(.*?\)(?:\s|)\+\+|\(.*?\)(?:\s|)—", content)    
        if karma_matches:
            for item in karma_matches:
                if len(item) > 40:
                    error_message = "Sorry, the names of your karmic victims cannot exceed 40 characters."
                    await channel.send(error_message)
                    raise KarmaNameError(error_message)
                else:
                    plus_or_minus = 'plus' if ('++' in item) else 'minus'
                    item = re.sub('--|\+\+|—','',item)
                    item = re.sub('(?:(?<=\))\s)|(?:\(|\))','',item).strip()
                    # TODO: Use a try statement here. int() in find_display_name is going to be problematic
                    if '@' in item:
                        item = self.find_display_name(item)
                    await asyncio.create_task(self.karmic_repercussion(item.lower(), plus_or_minus))
                    record = await asyncio.create_task(self.find_karma(item.lower()))
                    message = self.compile_message(record, plus_or_minus)
                    await channel.send(message)

    # Finds the display_name associated with a discord user ID
    def find_display_name(self, user):
        discord_user = re.sub('>','',re.sub('<','',re.sub('@','',user.strip())))
        profile_name = client.get_user(int(discord_user))
        return profile_name.name

    # Add/remove karma from db entries
    async def karmic_repercussion(self, item, effect):
        db = await asyncpg.create_pool(**CREDENTIALS)
        if effect == 'plus':
            karma_query = ''' INSERT INTO karma_table("name", karma) VALUES($1, $2)
                ON CONFLICT("name") DO UPDATE SET karma = karma_table.karma + 1 '''
            await db.execute(karma_query, item.lower(), 1)
        else:
            karma_query = ''' INSERT INTO karma_table("name", karma) VALUES($1, $2)
                ON CONFLICT("name") DO UPDATE SET karma = karma_table.karma - 1 '''
            await db.execute(karma_query, item.lower(), -1)
        await db.close()

    async def find_karma(self, item):
        db = await asyncpg.create_pool(**CREDENTIALS)
        connection = await db.acquire()
        async with connection.transaction():
            find_karma_q = "SELECT * FROM KARMA_TABLE WHERE name = $1"
            record = await db.fetchrow(find_karma_q, item)
        await db.release(connection)
        return(record)

    def compile_message(self, record, plus_or_minus):
        name = record['name']
        karma = record['karma']
        if plus_or_minus == "plus":
            return f"\"{name}\" feels warm and fuzzy! ({karma} karma)"
        else:
            return f"Ouch! \"{name}\" just took a dive! ({karma} karma)"
        # TODO: use this syntax to pull in random karmic phrases:
        #   stuff_in_string = "{} something something. ({} karma)".format(item, karma)
        #        # From https://matthew-brett.github.io/teaching/string_formatting.html
    

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CREDENTIALS = {
            "user": f"{os.getenv('PGUSER')}",
            "password": f"{os.getenv('PGPASSWORD')}",
            "database": f"{os.getenv('PGDATABASE')}",
            "host": f"{os.getenv('PGHOST')}",
            "port": f"{os.getenv('PGPORT')}"
        }

# Logging
handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)

discord.utils.setup_logging(handler=handler, level=logging.DEBUG)

client = MyClient()
client.run(TOKEN, log_handler=handler, log_level=logging.WARN, reconnect=True)