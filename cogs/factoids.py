from discord.ext import commands
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os

load_dotenv()
mongo_url = os.getenv('MONGO_URL')
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[f"{os.getenv('FACTOID_DB')}"]
collection = db.factoids

class Factoids(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(aliases=['f'])
    async def factoid(self, ctx, *payload: str):
        payload_string = ' '.join(payload)
        if 'is' in payload_string:
            split_string = payload_string.split('is', 1)
            f_name = split_string[0].strip()
            f_result = split_string[1].strip()
            print(f'{f_name}, {f_result}')
            await collection.insert_one({'f_name': f_name, 'f_result': f_result})
            await ctx.send(f'Okay, "{f_name}" saved.')
        else:
            db_entry = await collection.find_one({'f_name': payload_string})
            if db_entry:
                await ctx.send(db_entry['f_result'])
            else:
                await ctx.send(f'No factoid found for "{payload_string}"')
