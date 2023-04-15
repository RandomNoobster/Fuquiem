import aiohttp
# from datetime import datetime, timedelta
import asyncio
import pymongo
import requests
import os
import motor.motor_asyncio
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("api_key")
client = pymongo.MongoClient(os.getenv("pymongolink"))
# client2 = pymongo.MongoClient(os.getenv("pymongolink2"))
async_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("pymongolink"), serverSelectionTimeoutMS=5000)
# async_client_2 = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("pymongolink2"), serverSelectionTimeoutMS=5000)

async def refresh(mongo):
    await asyncio.sleep(2)
    members = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:500 alliance_id:[4729,7531]){{data{{id leader_name nation_name}}}}}}"}).json()['data']['nations']['data']
    users = list(mongo.users.find({}))
    for user in users:
        for member in members:
            if member['id'] == user['nationid']:
                if member['leader_name'] != user['leader']:
                    mongo.users.find_one_and_update({"nationid": user["nationid"]}, {"$set": {"leader": member['leader_name']}})
                if member['nation_name'] != user['name']:
                    mongo.users.find_one_and_update({"nationid": user["nationid"]}, {"$set": {"name": member['nation_name']}})
                break

async def get_users():
    async with aiohttp.ClientSession() as session:
        has_more_pages = True
        n = 1
        data = []
        while has_more_pages:
            await asyncio.sleep(2)
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:{n} first:500){{paginatorInfo{{hasMorePages}} data{{id discord leader_name nation_name alliance{{name id}}}}}}}}"}) as temp:
                n += 1
                res = await temp.json()
                for nation in res['data']['nations']['data']:
                    data.append(nation)
                has_more_pages = res['data']['nations']['paginatorInfo']['hasMorePages']
        futures = []
        for mongo in [async_client['main'], async_client['testing']]:
            for nation in data:
                futures.append(asyncio.ensure_future(mongo.world_nations.find_one_and_replace({"id": nation['id']}, nation, upsert=True)))
        await asyncio.gather(*futures)
        for mongo in [client['main'], client['testing']]:
            entries = mongo.world_nations.find({})
            for entry in entries:
                found = False
                for nation in data:
                    if entry["id"] == nation["id"]:
                        found = True
                        break
                if not found:
                    mongo.world_nations.find_one_and_delete({"id": entry['id']})

async def get_alliances():
    async with aiohttp.ClientSession() as session:
        has_more_pages = True
        n = 1
        data = []
        while has_more_pages:
            await asyncio.sleep(2)
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{alliances(page:{n} first:100){{paginatorInfo{{hasMorePages}} data{{id name acronym}}}}}}"}) as temp:
                n += 1
                res = await temp.json()
                for nation in res['data']['alliances']['data']:
                    data.append(nation)
                has_more_pages = res['data']['alliances']['paginatorInfo']['hasMorePages']
        for mongo in [client['main'], client['testing']]:
            mongo.alliances.drop()
            mongo.alliances.insert_many(data)

# async def get_nation_details(mongo):
#     async with aiohttp.ClientSession() as session:
#         has_more_pages = True
#         n = 1
#         while has_more_pages:
#             await asyncio.sleep(2)
#             async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:{n} first:75 vmode:false min_score:15 orderBy:{{column:DATE order:ASC}}){{paginatorInfo{{hasMorePages}} data{{id discord leader_name nation_name warpolicy flag last_active continent dompolicy vds irond population alliance_id beige_turns score color soldiers tanks aircraft ships missiles nukes bounties{{amount type}} treasures{{name}} alliance{{name id}} wars{{date winner attacker{{war_policy}} defender{{war_policy}} war_type defid turnsleft attacks{{loot_info victor moneystolen}}}} alliance_position num_cities ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}) as temp:
#                 n += 1
#                 res = await temp.json()
#                 now = int(datetime.utcnow().timestamp())
#                 futures = []
#                 for nation in res['data']['nations']['data']:
#                     nation['last_fetched'] = now                    
#                     mongo.nations.find_one_and_replace({"id": nation['id']}, nation, upsert=True)
#                     futures.append(asyncio.ensure_future(async_client_2['main'].nations.find_one_and_replace({"id": nation['id']}, nation, upsert=True)))
                    
#                 await asyncio.gather(*futures)
#                 has_more_pages = res['data']['nations']['paginatorInfo']['hasMorePages']

async def auto_update():
    while True:
        for mongo in [client['main'], client['testing']]:
            try:
                await refresh(mongo)
                print('refresh done')
            except Exception as e:
                print(f"I encountered an error whilst performing refresh():\n{e}")

        try:
            await get_users()
            print('get_users done')
        except Exception as e:
            print(f"I encountered an error whilst performing get_users():\n{e}")
            
        try:
            await get_alliances()
            print('get_alliances done')
        except Exception as e:
            print(f"I encountered an error whilst performing get_alliances():\n{e}")

        #try:
        #    await get_nation_details(client2['main'])
        #    print('get_nation_details done')
        #except Exception as e:
        #    print(f"I encountered an error whilst performing get_nation_details():\n{e}")

        await asyncio.sleep(60)
            
loop = asyncio.get_event_loop()
loop.run_until_complete(auto_update())