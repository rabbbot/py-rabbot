# bot.py
import os
import re
import discord
from dotenv import load_dotenv

from pymongo import MongoClient, ReturnDocument
from pprint import pprint

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'{client.user} has connected to Discord!')

    async def on_message(self, message):
        content = message.content
        channel = message.channel
            
        karma_matches = re.findall(r"(?:\S+)+(?:\s|)(?:\+\+|--)|\(.*?\)(?:\s|)--|\(.*?\)(?:\s|)\+\+", content)
        if karma_matches:
            for item in karma_matches:
                plus_or_minus = 'plus' if ('++' in item) else 'minus'
                item = re.sub('--|\+\+','',item)
                item = re.sub('(?:(?<=\))\s)|(?:\(|\))','',item).strip()
                # TODO: Use a try statement here. int() in find_display_name is going to be problematic
                if '@' in item:
                    item = self.find_display_name(item)
                self.karmic_repercussion(item, plus_or_minus)
                message = self.find_karma(item, plus_or_minus)
                await channel.send(message)

    # Finds the display_name associated with a discord user ID
    def find_display_name(self, user):
        discord_user = re.sub('>','',re.sub('<','',re.sub('@','',user.strip())))
        profile_name = client.get_user(int(discord_user))
        return profile_name.name

    # Handle database updates
    def db_update(self, filter, i):
        if collection.find_one(filter):
            collection.find_one_and_update(
                filter, 
                {'$inc': {'karma': i}},
                return_document=ReturnDocument.AFTER
                )
        else:
            filter['karma'] = i
            collection.insert_one(filter)

    # Add/remove karma from db entries
    def karmic_repercussion(self, item, effect):
        if effect == 'plus':
            self.db_update({"protagonist": item.lower() }, 1)
        else:
            self.db_update({"protagonist": item.lower() }, -1)

    def find_karma(self, item, plus_or_minus):
        db_entry = collection.find_one({"protagonist": item.lower() })
        if db_entry['karma']:
            if plus_or_minus == "plus":
                # TODO: use this syntax to pull in random karmic phrases:
                # stuff_in_string = "{} something something. ({} karma)".format(item, karma)
                # From https://matthew-brett.github.io/teaching/string_formatting.html
                return f"\"{item}\" feels warm and fuzzy! ({db_entry['karma']} karma)"
            else:
                return f"Ouch! \"{item}\" just took a dive! ({db_entry['karma']} karma)"

load_dotenv()

mongo_user = os.environ.get("MONGO_USERNAME")
mongo_password = os.environ.get("MONGO_PASSWORD")
dev_environment=os.environ.get("DEV_ENVIRONMENT")
TOKEN = os.getenv('DISCORD_TOKEN')

if dev_environment:
    print(f"DEV ENVIRONMENT: {dev_environment}")
    client = MongoClient()
    
else:
    print(f"DEV ENVIRONMENT: {dev_environment}")
    client = MongoClient(
        username=mongo_user,
        password=mongo_password
    )

db = client.karma_db
collection = db.karma_db

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

client = MyClient(intents=intents, )
client.run(TOKEN)
