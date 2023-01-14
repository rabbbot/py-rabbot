from discord.ext import commands
from dotenv import load_dotenv
import os, re
from motor.motor_asyncio import AsyncIOMotorClient
from pprint import pprint

load_dotenv()
mongo_url = os.getenv('MONGO_URL')
db_name = os.getenv('DB_NAME')
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client.db_name
collection = db.karma

class Karma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None    
    
    @commands.command()
    async def printdb(self, ctx):
        print("Karma DB entries:\n")
        cursor = collection.find({})
        for doc in await cursor.to_list(length=100):
            print("Doc")
            pprint.pprint(f"{doc['victim']}: {doc['karma']}")
        await ctx.send("DB printed to console")
    
    @commands.command(aliases=['k'])
    async def karma(self, ctx, op: str, *tuple: str):
        victim = ' '.join(tuple)
        victim_array = await self.compile_victims(victim)
        cheater = False
        match op:
            case '+':
                for item in victim_array:
                    cheater = await self.cheater_check(ctx, item)
                    if not cheater:
                        await self.karmic_repercussions(item, '+')
                        db_entry = await collection.find_one({'victim': item.lower()})
                        await ctx.send(f'{db_entry["victim"]} feels warm and fuzzy! ({db_entry["karma"]} karma)')
            case '-':
                for item in victim_array:
                    message = await self.karmic_repercussions(item, '-')
                    db_entry = await collection.find_one({'victim': item.lower()})
                    await ctx.send(f'{db_entry["victim"]} just took a dive! ({db_entry["karma"]} karma)')
            case 'worst':
                await self.sort_karma(1, "**Karmic assholes**:\n", ctx)
            case 'best':
                await self.sort_karma(-1, "**Karmic champions**\n", ctx)
            case 'print':
                message = await self.print_all()
            case 'find':
                for item in victim_array:
                    message = await self.find_karma(item)
                    await ctx.send(message)  
            case _:
                await ctx.send('I don\'t understand you, human.')
    
    async def compile_victims(self, victim_string):
        end_array = []
        user_array = re.findall('(?<!\w)@\w+', victim_string)
        for item in user_array:
            item = await self.find_display_name(item)
            end_array.append(item)
        victim_string = re.sub('<|>', '', re.sub('(?<!\w)@\w+', '', victim_string))
        groupings = list(filter(None, re.findall(r'(?!\()(.*?)(?=\))', victim_string)))
        victim_string = re.sub(r'\((.*?)\)', '', victim_string)
        misc_victims = list(filter(None, victim_string.split()))
        end_array = end_array + misc_victims + groupings
        end_array = list(set(end_array))
        return(end_array)

    # Finds the display_name associated with a discord user ID
    async def find_display_name(self, user):
        discord_user = re.sub('@','',user)
        try:
            profile_name = self.client.get_user(int(discord_user))
            profile_name = profile_name.name
        except:
            profile_name = discord_user
        return profile_name

    async def cheater_check(self, ctx, item):
        display_name = ctx.author.display_name.lower()
        if item.lower() == display_name:
            await ctx.send('https://media.giphy.com/media/owRSsSHHoVYFa/giphy.gif')
            return True

    async def update_document(self, filter, i):
        await collection.find_one_and_update(
                filter, 
                {'$inc': {'karma': i}}
            )

    async def karmic_repercussions(self, item, string):
        filter = {'victim': item.lower()}
        found = await collection.find_one(filter)
        int = 1 if string == '+' else -1
        if found:
            if string == '+':
                await self.update_document(filter, int)
            else:
                await self.update_document(filter, int)  
        else:
            filter['karma'] = int
            await collection.insert_one(filter)

    async def print_all():
        print("Karma DB entries:\n")
        cursor = collection.find({})
        for doc in await cursor.to_list(length=1000):
            pprint.pprint(f"{doc['victim']}: {doc['karma']}")

    async def find_karma(self, item):
        filter = {'victim': item.lower()}
        db_entry = await collection.find_one(filter)
        if db_entry:
            return(f'{db_entry["victim"]} has {db_entry["karma"]} karma.')
        else:
            return(f'{item} not found.')

    async def sort_karma(self, value, doc, ctx):
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
