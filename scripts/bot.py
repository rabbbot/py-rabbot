import os
import re
import discord
import logging
from dotenv import load_dotenv
import psycopg2
import asyncio

class KarmaNameError(Exception):
    pass

class MyClient(discord.Client):
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
        cur = conn.cursor()
        if effect == 'plus':
            karma_query = ''' INSERT INTO karma_table("name", karma) VALUES(%s, %s)
                ON CONFLICT("name") DO UPDATE SET karma = karma_table.karma + 1 '''
            values = [item.lower(), 1]
            cur.execute(karma_query, values)
            conn.commit()
        else:
            karma_query = ''' INSERT INTO karma_table("name", karma) VALUES(%s, %s)
                ON CONFLICT("name") DO UPDATE SET karma = karma_table.karma - 1 '''
            values = [item.lower(), -1]
            cur.execute(karma_query, values)
            conn.commit()
        cur.close()

    async def find_karma(self, item):
        cur = conn.cursor()
        find_karma_q = ''' SELECT * FROM KARMA_TABLE
        WHERE name = %s '''
        cur.execute(find_karma_q, [item])
        record = cur.fetchall()
        cur.close()
        return(record)

    def compile_message(self, record, plus_or_minus):
        name = ''
        karma = ''
        for tup in record:
            name, karma = tup
        if plus_or_minus == "plus":
            return f"\"{name}\" feels warm and fuzzy! ({karma} karma)"
        else:
            return f"Ouch! \"{name}\" just took a dive! ({karma} karma)"
        # TODO: use this syntax to pull in random karmic phrases:
        #   stuff_in_string = "{} something something. ({} karma)".format(item, karma)
        #        # From https://matthew-brett.github.io/teaching/string_formatting.html
              

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents=intents)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

conn = None
cur = None

if __name__ == '__main__':
    conn = None
    try:
        print('Connecting to database...')
        conn = psycopg2.connect('')
        cur = conn.cursor()
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
        db_version = cur.fetchone()
        print(db_version)

        create_karma = ''' CREATE TABLE IF NOT EXISTS karma_table (
            name    varchar(40) PRIMARY KEY,
            karma   int) '''

        cur.execute(create_karma)
        conn.commit()
        cur.close()

        client.run(TOKEN, log_handler=handler, log_level=logging.WARN, reconnect=True)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:    
            conn.close()