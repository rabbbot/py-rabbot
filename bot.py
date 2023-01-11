import os
import discord
import logging, logging.handlers
from dotenv import load_dotenv
import asyncio
from discord.ext import commands
import re
from motor.motor_asyncio import AsyncIOMotorClient
from pprint import pprint
from cogs.puggers import Puggers

# Logging
handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
discord.utils.setup_logging(handler=handler, level=logging.DEBUG)

# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
mongo_url = os.getenv('MONGO_URL')
db_name = os.getenv('DB_NAME')
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client.db_name
collection = db.karma

async def main():

    await client.add_cog(Puggers(bot=client))

    async with client:
        await client.start(TOKEN)


@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.command()
async def printdb(self, ctx):
    print("Karma DB entries:\n")
    cursor = collection.find({})
    for doc in await cursor.to_list(length=100):
        print("Doc")
        pprint.pprint(f"{doc['victim']}: {doc['karma']}")
    await ctx.send("DB printed to console")

@client.command()
async def karma(ctx, op: str, *tuple: str):
    victim = ' '.join(tuple)
    victim_array = await compile_victims(victim)
    cheater = False
    match op:
        case '+':
            for item in victim_array:
                cheater = await cheater_check(ctx, item)
                if not cheater:
                    await karmic_repercussions(item, '+')
                    db_entry = await collection.find_one({'victim': item.lower()})
                    await ctx.send(f'{db_entry["victim"]} feels warm and fuzzy! ({db_entry["karma"]} karma)')
        case '-':
            for item in victim_array:
                message = await karmic_repercussions(item, '-')
                db_entry = await collection.find_one({'victim': item.lower()})
                await ctx.send(f'{db_entry["victim"]} just took a dive! ({db_entry["karma"]} karma)')
        case 'worst':
            await sort_karma(1, "**Karmic assholes**:\n", ctx)
        case 'best':
            await sort_karma(-1, "**Karmic champions**\n", ctx)
        case 'print':
            message = await print_all()
        case 'find':
            for item in victim_array:
                message = await find_karma(item)
                await ctx.send(message)  
        case _:
            await ctx.send('I don\'t understand you, human.')


async def compile_victims(victim_string):
    end_array = []
    user_array = re.findall('(?<!\w)@\w+', victim_string)
    for item in user_array:
        item = await find_display_name(item)
        end_array.append(item)
    victim_string = re.sub('<|>', '', re.sub('(?<!\w)@\w+', '', victim_string))
    groupings = list(filter(None, re.findall(r'(?!\()(.*?)(?=\))', victim_string)))
    victim_string = re.sub(r'\((.*?)\)', '', victim_string)
    misc_victims = list(filter(None, victim_string.split()))
    end_array = end_array + misc_victims + groupings
    end_array = list(set(end_array))
    return(end_array)

# Finds the display_name associated with a discord user ID
async def find_display_name(user):
    discord_user = re.sub('@','',user)
    try:
        profile_name = client.get_user(int(discord_user))
        profile_name = profile_name.name
    except:
        profile_name = discord_user
    return profile_name

async def cheater_check(ctx, item):
    display_name = ctx.author.display_name.lower()
    if item.lower() == display_name:
        await ctx.send('https://media.giphy.com/media/owRSsSHHoVYFa/giphy.gif')
        return True

async def update_document(filter, i):
    await collection.find_one_and_update(
            filter, 
            {'$inc': {'karma': i}}
        )

async def karmic_repercussions(item, string):
    filter = {'victim': item.lower()}
    found = await collection.find_one(filter)
    int = 1 if string == '+' else -1
    if found:
        if string == '+':
            await update_document(filter, int)
        else:
            await update_document(filter, int)  
    else:
        filter['karma'] = int
        await collection.insert_one(filter)

async def print_all():
    print("Karma DB entries:\n")
    cursor = collection.find({})
    for doc in await cursor.to_list(length=1000):
        pprint.pprint(f"{doc['victim']}: {doc['karma']}")

async def find_karma(item):
    filter = {'victim': item.lower()}
    db_entry = await collection.find_one(filter)
    if db_entry:
        return(f'{db_entry["victim"]} has {db_entry["karma"]} karma.')
    else:
        return(f'{item} not found.')

async def sort_karma(value, doc, ctx):
    n = 1
    karma_map = {}
    cursor = collection.find()
    cursor.sort('karma', value).limit(5)
    async for document in cursor:
       karma_map[document['victim']]=document["karma"]
    for entry in karma_map:
       doc += f"**{n}**. {entry} ({karma_map[entry]} karma)\n"
       n += 1   
    await ctx.send(doc)


if __name__ == '__main__':
    asyncio.run(main())

