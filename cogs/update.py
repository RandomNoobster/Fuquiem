import asyncio
import discord
import math
import aiohttp
from flask.views import MethodView
from mako.template import Template
from keep_alive import app
import os.path
from main import mongo, kit
from datetime import datetime, timedelta
from discord.ext import commands
import os
from cryptography.fernet import Fernet
import utils
import traceback
import random

api_key = os.getenv("api_key")
api_key_2 = os.getenv("api_key_2")
convent_key = os.getenv("convent_api_key")
key = os.getenv("encryption_key")
cipher_suite = Fernet(key)


class Update(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.bg_task = self.bot.loop.create_task(self.auto_update())

    @commands.command(brief='Gives you an overview of, and sends a DM to everyone that needs to login/buy spies/get food')
    @commands.has_any_role(*utils.mid_gov_plus_perms)
    async def check(self, ctx, aa='all'):
        try:
            await self.nation_check(ctx.channel, aa)
        except Exception as e:
            await ctx.send(f"I encountered an error whilst performing self.food_check():\n```{traceback.format_exc()}```")

    async def nation_check(self, channel, aa='all'):
        async with aiohttp.ClientSession() as session:
            message = await channel.send("<:thonk:787399051582504980>")

            query = f"{{data{{nation_name leader_name id alliance_position continent color food aluminum bauxite coal gasoline iron lead munitions oil steel uranium last_active spies dompolicy alliance_id alliance{{name id}} num_cities soldiers tanks aircraft ships missiles nukes wars{{date attid turnsleft winner}} ironw bauxitew armss egr massirr cia propaganda_bureau population itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date name powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}"
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:500 alliance_id:4729 vmode:false){query}}}"}) as temp:
                church = (await temp.json())['data']['nations']['data']
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={convent_key}", json={'query': f"{{nations(first:500 alliance_id:8819 vmode:false){query}}}"}) as temp:
                convent = (await temp.json())['data']['nations']['data']

            if aa == 'all':
                aa = [church, convent]
            elif aa in 'church':
                aa = [church]
            elif aa in 'convent':
                aa = [convent]
            else:
                await message.edit(content="That's an illegal argument!")
                return

            temp, colors, prices, treasures, radiation, seasonal_mod = await utils.pre_revenue_calc(api_key, message)

            embeds = []
            for alliance in aa:
                food_fields = []
                inactivity_fields = []
                color_fields = []
                rss_fields = []
                mil_fields = []
                power_fields = []
                improv_fields = []

                for nation in alliance:
                    if nation['alliance_position'] == "APPLICANT":
                        continue

                    person = utils.find_user(self, nation['id'])
                    if person == {}:
                        continue
                    user = await self.bot.fetch_user(person['user'])

                    # rss_check
                    rev_obj = await utils.revenue_calc(message, nation, radiation, treasures, prices, colors, seasonal_mod, None)
                    rss = ['food', 'aluminum', 'bauxite', 'coal', 'gasoline',
                           'iron', 'lead', 'munitions', 'oil', 'steel', 'uranium']
                    msg = "Hey, you should get some: \n"
                    for rs in rss:
                        if nation[rs] == None:
                            continue
                        if rev_obj[rs] < 0 and nation[rs] < abs(rev_obj[rs]):
                            msg += f"> {rs}\n"
                    if "> " in msg:
                        msg += "You can request some by using </request:1153376925914497024> in <#775428035674898501>"
                        if "food" in msg or "uranium" in msg:
                            msg += ". For food and uranium it's possible to use the `$food` and `$uran` commands in <#850302301838114826> to instantly get some."
                        rss_fields.append(
                            {"name": nation['leader_name'], "value": f"[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']}) is running out of resources."})
                        try:
                            await user.send(msg, silent=True, embed=None, embeds=[])
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Resources', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because it seems that you are running out of resources. You can request some by using </request:1153376925914497024> in #rss-requests."})

                    # wasting improv slots
                    improv_waste = set()
                    for city in nation['cities']:
                        slots = math.floor(city['infrastructure']/50)
                        slots -= city['oilpower'] + city['windpower'] + city['coalpower'] + city['nuclearpower'] + city['coalmine'] + city['oilwell'] + city['uramine'] + city['barracks'] + city['farm'] + city['policestation'] + city['hospital'] + city['recyclingcenter'] + city['subway'] + \
                            city['supermarket'] + city['bank'] + city['mall'] + city['stadium'] + city['leadmine'] + city['ironmine'] + city['bauxitemine'] + city['gasrefinery'] + \
                            city['aluminumrefinery'] + city['steelmill'] + city['munitionsfactory'] + \
                            city['factory'] + \
                            city['airforcebase'] + city['drydock']
                        if slots > 0:
                            improv_waste.add((city['id'], city['name'], slots))
                    if len(improv_waste) > 0:
                        try:
                            improv_fields.append(
                                {"name": nation['leader_name'], "value": f"[{nation['leader_name']}](https://politicsandwar.com/nation/id={nation['id']}) has unused improvement slots."})
                            city_msg = "\n".join(
                                [f"> [{name}](https://politicsandwar.com/city/id={id})" for id, name, slots in improv_waste])
                            await user.send(utils.cut_string(f'Hey, the following cities have unused improvement slots:\n {city_msg}'), silent=True, embed=None, embeds=[])
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Improvements', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you have unused improvement slots. You can use these slots to build more improvements, which will increase your income. "})

                    # city check
                    power_waste = set()
                    city_power = set()
                    for city in nation['cities']:
                        for city in nation['cities']:
                            slots = math.floor(city['infrastructure']/50)
                            slots -= city['oilpower'] + city['windpower'] + city['coalpower'] + city['nuclearpower'] + city['coalmine'] + city['oilwell'] + city['uramine'] + city['barracks'] + city['farm'] + city['policestation'] + city['hospital'] + city['recyclingcenter'] + city['subway'] + \
                                city['supermarket'] + city['bank'] + city['mall'] + city['stadium'] + city['leadmine'] + city['ironmine'] + city['bauxitemine'] + city['gasrefinery'] + \
                                city['aluminumrefinery'] + city['steelmill'] + city['munitionsfactory'] + \
                                city['factory'] + \
                                city['airforcebase'] + city['drydock']
                            if slots < 0:
                                continue
                            unpowered_infra = city['infrastructure']
                            # can add something about wasted slots
                            for _ in range(city['windpower']):
                                if unpowered_infra < 0:
                                    power_waste.add((city['id'], city['name']))
                                if unpowered_infra > 0:
                                    unpowered_infra -= 250
                            for _ in range(city['nuclearpower']):
                                if unpowered_infra < 0:
                                    power_waste.add((city['id'], city['name']))
                                for level in range(2):
                                    if unpowered_infra > 0:
                                        unpowered_infra -= 1000
                            for _ in range(city['oilpower']):
                                if unpowered_infra < 0:
                                    power_waste.add((city['id'], city['name']))
                                for level in range(5):
                                    if unpowered_infra > 0:
                                        unpowered_infra -= 100
                            for _ in range(city['coalpower']):
                                if unpowered_infra < 0:
                                    power_waste.add((city['id'], city['name']))
                                for level in range(5):
                                    if unpowered_infra > 0:
                                        unpowered_infra -= 100
                            city_power.add(
                                (city['id'], city['name'], unpowered_infra))

                    # to much power
                    if power_waste:
                        milt = utils.advanced_militarization_checker(nation)
                        if round(milt['barracks_mmr']) == 5 and round(milt['factory_mmr']) == 5 and round(milt['hangar_mmr']) == 5:
                            pass
                        else:
                            try:
                                power_fields.append(
                                    {"name": nation['leader_name'], "value": f"[{nation['leader_name']}](https://politicsandwar.com/nation/id={nation['id']}) has too many power plants."})
                                city_msg = "\n".join(
                                    [f"> [{name}](https://politicsandwar.com/city/id={id})" for id, name in power_waste])
                                await user.send(utils.cut_string(f'Hey, the following cities have too many power plants:\n {city_msg}'), silent=True, embed=None, embeds=[])
                                print('i just sent a msg to', user)
                            except discord.Forbidden:
                                await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                                await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Power', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you have more power plants than you need."})

                    # not enough power
                    msg = "\n".join([f"> [{name}](https://politicsandwar.com/city/id={id})" for id,
                                    name, unpowered_infra in city_power if unpowered_infra > 0])
                    if "politicsandwar" in msg:
                        try:
                            power_fields.append(
                                {"name": nation['leader_name'], "value": f"[{nation['leader_name']}](https://politicsandwar.com/nation/id={nation['id']}) has too few power plants."})
                            await user.send(utils.cut_string(f'Hey, you need more power plants in the following cities:\n {msg}'), silent=True, embed=None, embeds=[])
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Power', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you have unpowered infrastructure."})

                    # mmr check
                    milt = utils.advanced_militarization_checker(nation)
                    active_war = False
                    for war in nation['wars']:
                        if war['turnsleft'] == 0:
                            active_war = True
                            break
                    if active_war and (milt['barracks_mmr'] < 4.5 or milt['factory_mmr'] < 4.5 or milt['hangar_mmr'] < 4.5 or milt['drydock_mmr'] < 2.5):
                        try:
                            mil_fields.append(
                                {"name": nation['leader_name'], "value": f"[{nation['leader_name']}](https://politicsandwar.com/nation/id={nation['id']}) has too little military improvements."})
                            await user.send(f'Hey, when you are at war, you should always have an MMR of 5/5/5/3. You are at war and your MMR is currently too low, please fix: https://politicsandwar.com/city/manager/', silent=True, embed=None, embeds=[])
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Military Improvements', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you have too little military improvements. When you are at war, you should always have an MMR of 5/5/5/3. You can change your military improvements here: <a href=\"https://politicsandwar.com/city/manager/\">https://politicsandwar.com/city/manager/</a>"})

                    # buy mil check
                    msg = "Hey, you can buy military units: \n"
                    for unit in ['soldiers', 'tanks', 'aircraft', 'ships', 'spies']:
                        if nation[unit] < milt[f"max_{unit}"]:
                            msg += f"> [{unit}](https://politicsandwar.com/nation/military/{unit.replace('ships', 'navy')}/)\n"
                    if "> " in msg:
                        if random.random() < 0.1:
                            msg += "Pro tip: If you play PnW on a computer, you can use this userscript to make unit rebuys easier: https://greasyfork.org/en/scripts/456781-easy-rebuy-for-politics-and-war. This video explains how you can install userscripts via Tampermonkey: https://www.youtube.com/watch?v=N71RrRfztv4"
                        try:
                            mil_fields.append(
                                {"name": nation['leader_name'], "value": f"[{nation['leader_name']}](https://politicsandwar.com/nation/id={nation['id']}) can buy military units."})
                            await user.send(utils.cut_string(msg), silent=True, embed=None, embeds=[])
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Buy Military Units', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. You can buy military units here: <a href=\"https://politicsandwar.com/nation/military/\">https://politicsandwar.com/nation/military/</a>"})

                    # inactivity_check
                    minutes_inactive = round((datetime.utcnow() - datetime.strptime(
                        nation['last_active'], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)).total_seconds()/60)
                    if minutes_inactive > 2880:
                        inactivity_fields.append(
                            {"name": nation['leader_name'], "value": f"[{nation['leader_name']}](https://politicsandwar.com/nation/id={nation['id']}) has been inactive for {round(minutes_inactive/1440)} days."})
                        msg = "Hey, you should log in: https://politicsandwar.com"
                        if random.random() < 0.1:
                            msg += "\nPro tip: If you play PnW on a computer, you can use this userscript to get login reminders in your browser: https://greasyfork.org/en/scripts/476197-pnw-login-reminder. This video explains how you can install userscripts via Tampermonkey: https://www.youtube.com/watch?v=N71RrRfztv4"
                        try:
                            await user.send(msg, silent=True, embed=None, embeds=[])
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Inactivity', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you have been somewhat inactive lately. He sent this message in the hopes that you might get a notification by email, increasing the probability of you logging in to the game."})

                    # color_check
                    if nation['alliance_id'] == "4729" and nation['color'] not in ['green', 'beige'] or nation['alliance_id'] == "8819" and nation['color'] not in ['purple', 'beige']:
                        color_fields.append(
                            {"name": nation['leader_name'], "value": f"[{nation['leader_name']}](https://politicsandwar.com/nation/id={nation['id']}) are on {nation['color']}"})

                        if nation['alliance_id'] == "4729":
                            color = 'green'
                        elif nation['alliance_id'] == "8819":
                            color = 'purple'
                        else:
                            continue
                        try:
                            await user.send(f'Hey, you should change your color to {color} in order to get money from the color bonus: https://politicsandwar.com/nation/edit/', silent=True, embed=None, embeds=[])
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Color', 'message': f"Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you are currently not getting any money from the color bonus. If you change your nation's color to {color}, your daily revenue will increase. You can change your color here: <a href=\"https://politicsandwar.com/nation/edit/\">https://politicsandwar.com/nation/edit/</a>"})

                embeds += utils.embed_pager(
                    f"{alliance[0]['alliance']['name']} food", food_fields)
                embeds += utils.embed_pager(
                    f"{alliance[0]['alliance']['name']} inactivity", inactivity_fields)
                embeds += utils.embed_pager(
                    f"{alliance[0]['alliance']['name']} color", color_fields)
                embeds += utils.embed_pager(
                    f"{alliance[0]['alliance']['name']} rss", rss_fields)
                embeds += utils.embed_pager(
                    f"{alliance[0]['alliance']['name']} military", mil_fields)
                embeds += utils.embed_pager(
                    f"{alliance[0]['alliance']['name']} power", power_fields)
                embeds += utils.embed_pager(
                    f"{alliance[0]['alliance']['name']} improvements", improv_fields)

            await message.delete()
            for embed in embeds:
                await channel.send(embed=embed)

    @commands.command(brief='Assign city-tiering roles')
    @commands.has_any_role(*utils.high_gov_plus_perms)
    async def cityroles(self, ctx):
        await self.city_roles()
        await ctx.send(f'City-dependent roles have been assigned!')
        # merely a debugging command

    async def city_roles(self):
        async with aiohttp.ClientSession() as session:
            nations = []
            async with session.post(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{nations(page:1 first:500 alliance_position:[2,3,4,5] alliance_id:4729){data{id nation_name num_cities}}}"}) as temp:
                nations += (await temp.json())['data']['nations']['data']
            async with session.post(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{nations(page:1 first:500 alliance_position:[2,3,4,5] alliance_id:8819){data{id nation_name num_cities}}}"}) as temp:
                nations += (await temp.json())['data']['nations']['data']

        guild = self.bot.get_guild(434071714893398016)
        zerotoninerole = guild.get_role(837789914846330922)
        tentonineteenrole = guild.get_role(837790885512347690)
        twentytotwentyninerole = guild.get_role(837791502272561202)
        thirtyplusrole = guild.get_role(837791514788495397)
        heathen_role = guild.get_role(434248817005690880)
        love_pings = guild.get_role(747179040720289842)
        trader_role = guild.get_role(796057460502298684)

        for nation in nations:
            person = utils.find_user(self, nation['id'])
            if person == {}:
                print(
                    f"I couldn't assign a city-role to {nation['nation_name']}")
                continue
            user = guild.get_member(person['user'])
            if not user:
                print(
                    f"I could not find {nation['nation_name']} as a member on discord.")
                continue
            if nation['num_cities'] < 10:
                if zerotoninerole not in user.roles:
                    await user.add_roles(zerotoninerole)
                if tentonineteenrole in user.roles:
                    await user.remove_roles(tentonineteenrole)
                if twentytotwentyninerole in user.roles:
                    await user.remove_roles(twentytotwentyninerole)
                if thirtyplusrole in user.roles:
                    await user.remove_roles(thirtyplusrole)
            if 9 < nation['num_cities'] < 20:
                if tentonineteenrole not in user.roles:
                    await user.add_roles(tentonineteenrole)
                if zerotoninerole in user.roles:
                    await user.remove_roles(zerotoninerole)
                if twentytotwentyninerole in user.roles:
                    await user.remove_roles(twentytotwentyninerole)
                if thirtyplusrole in user.roles:
                    await user.remove_roles(thirtyplusrole)
            if 19 < nation['num_cities'] < 30:
                if twentytotwentyninerole not in user.roles:
                    await user.add_roles(twentytotwentyninerole)
                if tentonineteenrole in user.roles:
                    await user.remove_roles(tentonineteenrole)
                if zerotoninerole in user.roles:
                    await user.remove_roles(zerotoninerole)
                if thirtyplusrole in user.roles:
                    await user.remove_roles(thirtyplusrole)
            if 29 < nation['num_cities']:
                if thirtyplusrole not in user.roles:
                    await user.add_roles(thirtyplusrole)
                if tentonineteenrole in user.roles:
                    await user.remove_roles(tentonineteenrole)
                if twentytotwentyninerole in user.roles:
                    await user.remove_roles(twentytotwentyninerole)
                if zerotoninerole in user.roles:
                    await user.remove_roles(zerotoninerole)

        for member in guild.members:
            if heathen_role in member.roles:
                if twentytotwentyninerole in member.roles:
                    await member.remove_roles(twentytotwentyninerole)
                if tentonineteenrole in member.roles:
                    await member.remove_roles(tentonineteenrole)
                if zerotoninerole in member.roles:
                    await member.remove_roles(zerotoninerole)
                if thirtyplusrole in member.roles:
                    await member.remove_roles(thirtyplusrole)
                if love_pings in member.roles:
                    await member.remove_roles(love_pings)
                if trader_role in member.roles:
                    await member.remove_roles(trader_role)

    @commands.command(brief='Refresh sheet information')
    @commands.has_any_role(*utils.high_gov_plus_perms)
    async def getsheet(self, ctx):
        print('getting sheet')
        await self.sheet_generator()
        await ctx.send('Finito!')

    async def sheet_generator(self):
        async with aiohttp.ClientSession() as session:
            with open('./data/templates/sheet.txt', 'r', encoding='UTF-8') as file:
                template = file.read()
            try:
                async with session.post(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{nations(page:1 first:500 alliance_id:4729){data{id alliance_id alliance_position leader_name nation_name color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available wars{turnsleft att_alliance_id} cities{infrastructure barracks factory airforcebase drydock}}}}"}) as temp:
                    church = (await temp.json())['data']['nations']['data']
                async with session.post(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{nations(page:1 first:500 alliance_id:8819){data{id alliance_id alliance_position leader_name nation_name color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available wars{turnsleft att_alliance_id} cities{infrastructure barracks factory airforcebase drydock}}}}"}) as temp:
                    convent = (await temp.json())['data']['nations']['data']
                sum = church + convent
            except Exception as e:
                print(f"I encoutered an error whilst creating a sheet: {e}")
                return

            nations = []

            for nation in sum:
                if nation['alliance_position'] != "APPLICANT":
                    nations.append(nation)

            async with session.post(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{alliances(first:2 id:[4729,8819]){data{score nations{num_cities alliance_position}}}}"}) as temp:
                alliances = (await temp.json())['data']['alliances']['data']

            score = alliances[0]['score'] + alliances[1]['score']
            cities = 0
            for i in range(2):
                for nation in alliances[i-1]['nations']:
                    cities += nation['num_cities']

            aa = {"members": len(nations), "cities": cities,
                  "score": score, "mmr": mongo.mmr.find_one({})}

            users = list(self.bot.get_all_members())
            rss = ['aluminum', 'bauxite', 'coal', 'food', 'gasoline', 'iron',
                   'lead', 'munitions', 'money', 'oil', 'steel', 'uranium']
            async with session.post(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{tradeprices(page:1 first:1){data{coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}}"}) as resp:
                prices = (await resp.json())['data']['tradeprices']['data'][0]
                prices['money'] = 1

            for nation in nations:
                x = mongo.users.find_one({"nationid": str(nation['id'])})
                nation['user_object'] = {
                    'discordid': '', 'username': '', "audited": ''}
                if x == None:
                    nation['user_object'].update(
                        {'discordid': '¯\_(ツ)_/¯', "username": '¯\_(ツ)_/¯'})
                else:
                    for user in users:
                        nation['user_object'].update(
                            {'discordid': x['user'], "audited": x['audited']})
                        if user.id == x['user']:
                            nation['user_object']['username'] = str(user)
                            break
                        else:
                            nation['user_object']['username'] = "¯\_(ツ)_/¯"
                y = mongo.total_balance.find_one(
                    {"nationid": str(nation['id'])})
                if y == None:
                    nation['user_object'].update({"total": 0, "al": 0, "ba": 0, "co": 0, "fo": 0,
                                                 "ga": 0, "ir": 0, "le": 0, "mu": 0, "mo": 0, "oi": 0, "st": 0, "ur": 0})
                else:
                    con_total = 0
                    for rs in rss:
                        amount = y[rs[:2].lower()]
                        price = int(prices[rs])
                        con_total += amount * price
                    nation['user_object'].update({"total": round(con_total), "al": y['al'], "ba": y['ba'], "co": y['co'], "fo": y['fo'],
                                                 "ga": y['ga'], "ir": y['ir'], "le": y['le'], "mu": y['mu'], "mo": y['mo'], "oi": y['oi'], "st": y['st'], "ur": y['ur']})
                nation['infrastructure'] = 0
                barracks = 0
                factories = 0
                hangars = 0
                drydocks = 0
                for city in nation['cities']:
                    nation['infrastructure'] += city['infrastructure']
                    barracks += city['barracks']
                    factories += city['factory']
                    hangars += city['airforcebase']
                    drydocks += city['drydock']
                nation['mmr'] = f"{round(barracks/nation['num_cities'],1)}/{round(factories/nation['num_cities'],1)}/{round(hangars/nation['num_cities'],1)}/{round(drydocks/nation['num_cities'],1)}"
                nation['mmr_color'] = "black"
                if barracks/nation['num_cities'] < aa['mmr']['bar'] or factories/nation['num_cities'] < aa['mmr']['fac'] or hangars/nation['num_cities'] < aa['mmr']['han'] or drydocks/nation['num_cities'] < aa['mmr']['dry']:
                    nation['mmr_color'] = "red"
                nation['off_wars'] = 0
                nation['def_wars'] = 0
                for war in nation['wars']:
                    if war['turnsleft'] > 0:
                        if war['att_alliance_id'] in ["4729", "8819"]:
                            nation['off_wars'] += 1
                        else:
                            nation['def_wars'] += 1

            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            result = Template(template).render(
                aa=aa, nations=nations, timestamp=timestamp, datetime=datetime)
            mongo.sheet_code.replace_one({}, {"code": result})
            print('webpage updated')

    async def alert_scanner(self):
        alerts = list(mongo.users.find(
            {"beige_alerts": {"$exists": True, "$not": {"$size": 0}}}))
        for user in alerts:
            for alert in user['beige_alerts']:
                if datetime.utcnow() >= alert['time']:
                    disc_user = await self.bot.fetch_user(user['user'])
                    await disc_user.send(f"Hey, https://politicsandwar.com/nation/id={alert['id']} is out of beige!")
                    user['beige_alerts'].remove(alert)
                    alert_list = user['beige_alerts']
                    if not alert_list:
                        alert_list = []
                    mongo.users.find_one_and_update({"user": user['user']}, {
                                                    "$set": {"beige_alerts": alert_list}})

    async def raffle_reminder(self):
        users = list(self.bot.get_all_members())
        guild = self.bot.get_guild(434071714893398016)
        iluvping = guild.get_role(747179040720289842)
        pupil = guild.get_role(711385354929700905)
        for user in users:
            if iluvping in user.roles and pupil in user.roles:
                person = mongo.users.find_one({"user": user.id})
                if person == None:
                    print(str(user), 'not in mongo db')
                    continue
                if not person['signedup']:
                    disc = await self.bot.fetch_user(person['user'])
                    await disc.send("Hey, there's 4 hours left until the winners of today's raffle is drawn! Remember to sign up for the raffle in <#850302301838114826>!")

    async def nuke_reminder(self):
        debug_channel = self.bot.get_channel(677883771810349067)
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{nations(page:1 first:500 alliance_id:4729 vmode:false){data{id leader_name nation_name score warpolicy spies cia spy_satellite espionage_available nukes missiles mlp nrf}}}"}) as temp:
                church = (await temp.json())['data']['nations']['data']
            async with session.post(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{nations(page:1 first:500 alliance_id:8819 vmode:false){data{id leader_name nation_name score warpolicy spies cia spy_satellite espionage_available nukes missiles mlp nrf}}}"}) as temp:
                convent = (await temp.json())['data']['nations']['data']
            sum = church + convent
            for member in sum:
                content = "Remember to buy:\n"
                if member['nrf'] and member['nukes'] < 100:
                    content += "> Nukes: <https://politicsandwar.com/nation/military/nukes/>\n"
                if member['mlp'] and member['missiles'] < 100:
                    content += "> Missiles: <https://politicsandwar.com/nation/military/missiles/>\n"
                if content != "Remember to buy:\n":
                    try:
                        person = utils.find_user(self, member['id'])
                        user = await self.bot.fetch_user(person['user'])
                        await asyncio.sleep(1)
                        await user.send(content=content, silent=True)
                    except discord.Forbidden:
                        await debug_channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                    except:
                        await debug_channel.send(f"error led to no nuke/missile dm to {member['nation_name']}")

    async def soxi(self):
        users = list(mongo.users.find({}))
        user_list = []
        for user in users:
            user_list.append(
                {"discordid": user['user'], "nationid": user['nationid']})
        result = str(user_list)

        class soxi(MethodView):
            def get(arg):
                return str(result)
        app.add_url_rule(
            f"/soxi", view_func=soxi.as_view("soxi"), methods=["GET"])
        return

    async def check_maps(self):
        debug_channel = self.bot.get_channel(677883771810349067)
        content = "You have wars with 12 MAPs! Use them before they go to waste! https://politicsandwar.com/nation/war/"
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{nations(page:1 first:500 alliance_id:4729 vmode:false){data{id nation_name wars{att_id def_id att_points def_points}}}}"}) as temp:
                church = (await temp.json())['data']['nations']['data']
            async with session.post(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{nations(page:1 first:500 alliance_id:8819 vmode:false){data{id nation_name wars{att_id def_id att_points def_points}}}}"}) as temp:
                convent = (await temp.json())['data']['nations']['data']
            sum = church + convent
            for member in sum:
                send = False
                for war in member["wars"]:
                    if war['turnsleft'] <= 0:
                        continue
                    if war["att_id"] == member["id"]:
                        if war["att_points"] == 12:
                            send = True
                            break
                    elif war['def_id'] == member['id']:
                        if war["def_points"] == 12:
                            send = True
                            break
                if send:
                    try:
                        person = utils.find_user(self, member['id'])
                        user: discord.User = await self.bot.fetch_user(person['user'])
                        messages = await user.history(limit=5, after=datetime.utcnow() - timedelta(hours=12)).flatten()
                        for msg in messages:
                            if msg.content == content:
                                send = False
                        if send:
                            await user.send(content=content, silent=True)
                    except discord.Forbidden:
                        await debug_channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                    except:
                        await debug_channel.send(f"error led to no 12 MAP dm to {member['nation_name']}")

    async def auto_update(self):
        await self.bot.wait_until_ready()
        Raffle = self.bot.get_cog('Raffle')
        Military = self.bot.get_cog('Military')
        debug_channel = self.bot.get_channel(739155202640183377)
        embed_channel = self.bot.get_channel(677883771810349067)
        await self.soxi()
        while True:
            minute = 0
            now = datetime.utcnow()
            print('now', now)
            future = datetime(now.year, now.month, now.day, now.hour, minute)
            print('future', future)
            if now.minute >= minute:
                future += timedelta(hours=1, seconds=1)
            print((future-now).seconds,
                  'until check for big update is done.', datetime.utcnow())
            await asyncio.sleep((future-now).seconds)
            print(datetime.utcnow(), 'awake')
            if now.hour == 22:
                print(datetime.utcnow(), 'hour is 22')
                try:
                    await Raffle.draw_func()
                except:
                    await debug_channel.send(f"I encountered an error whilst performing Raffle.draw_func():\n```{traceback.format_exc()}```")

            if now.hour == 0:
                print(datetime.utcnow(), 'hour is 0')
                try:
                    await self.nation_check(embed_channel)
                except:
                    await debug_channel.send(f"I encountered an error whilst performing self.nation_check():\n```{traceback.format_exc()}```")
                # try:
                #     await self.nuke_reminder()
                # except:
                #     await debug_channel.send(f"I encountered an error whilst performing self.nuke_reminder():\n```{traceback.format_exc()}```")

            if now.hour == 18:
                try:
                    await Military.spies_msg()
                except:
                    await debug_channel.send(f"I encountered an error whilst performing Military.spies_msg():\n```{traceback.format_exc()}```")
                try:
                    await self.raffle_reminder()
                except:
                    await debug_channel.send(f"I encountered an error whilst performing self.raffle_reminder():\n```{traceback.format_exc()}```")
            try:
                await self.alert_scanner()
            except:
                await debug_channel.send(f"I encountered an error whilst performing self.alert_scanner():\n```{traceback.format_exc()}```")
            try:
                await self.sheet_generator()
            except:
                await debug_channel.send(f"I encountered an error whilst performing sheet.sheet_generator():\n```{traceback.format_exc()}```")
            try:
                await self.city_roles()
            except:
                await debug_channel.send(f"I encountered an error whilst performing self.city_roles():\n```{traceback.format_exc()}```")
            try:
                await Military.wars_check()
            except:
                await debug_channel.send(f"I encountered an error whilst performing Military.wars_check():\n```{traceback.format_exc()}```")
            # try:
            #     await self.check_maps()
            # except:
            #     await debug_channel.send(f"I encountered an error whilst performing self.check_maps():\n```{traceback.format_exc()}```")

            print(datetime.utcnow(), 'finished, going to sleep')
            await asyncio.sleep(60)

    @commands.command(brief='Manually run scheduled tasks')
    @commands.has_any_role(*utils.high_gov_plus_perms)
    async def update(self, ctx):
        await ctx.send('I will do my worst...')
        try:
            await self.alert_scanner()
        except:
            pass
        await self.sheet_generator()
        try:
            await self.city_roles()
        except:
            pass
        await ctx.send('Things have been updated from the API.')

    @commands.command(brief='Manually remind people to buy spies')
    @commands.has_any_role(*utils.mid_gov_plus_perms)
    async def spyreminder(self, ctx):
        await ctx.send('I will do my worst...')
        Military = self.bot.get_cog('Military')
        try:
            await Military.spies_msg()
        except:
            await ctx.send(f"I encountered an error whilst performing Military.spies_msg():\n```{traceback.format_exc()}```")
        await ctx.send('Things have been updated from the API.')


def setup(bot):
    bot.add_cog(Update(bot))
