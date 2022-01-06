import asyncio
import discord
import math
import aiohttp
import pytz
from flask.views import MethodView
from mako.template import Template
from keep_alive import app
import os.path
from main import mongo
from datetime import datetime, timedelta
from discord.ext import commands
import os
import requests
from lxml import html
from cryptography.fernet import Fernet
import re
import utils

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
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def check(self, ctx, aa='all'):
        try:
            await self.food_check(ctx.channel, aa)
        except Exception as e:
            await ctx.send(f"I encountered an error whilst performing self.food_check():\n```{e}```")
        try:
            await self.spies_check(ctx.channel, aa)
        except Exception as e:
            await ctx.send(f"I encountered an error whilst performing self.spies_check():\n```{e}```")
        try:
            await self.inactivity_check(ctx.channel, aa)
        except Exception as e:
            await ctx.send(f"I encountered an error whilst performing self.inactivity_check():\n```{e}```")
        try:
            await self.color_check(ctx.channel)
        except Exception as e:
            await ctx.send(f"I encountered an error whilst performing self.color_check():\n```{e}```")
        await ctx.send("I sent 'em all some DMs!")

    async def aa_check(self):
        channel = self.bot.get_channel(677883771810349067)
        try:
            await self.food_check(channel)
        except Exception as e:
            await channel.send(f"I encountered an error whilst performing self.food_check():\n```{e}```")
        try:
            await self.spies_check(channel)
        except Exception as e:
            await channel.send(f"I encountered an error whilst performing self.spies_check():\n```{e}```")
        try:
            await self.inactivity_check(channel)
        except Exception as e:
            await channel.send(f"I encountered an error whilst performing self.inactivity_check():\n```{e}```")
        try:
            await self.color_check(channel)
        except Exception as e:
            await channel.send(f"I encountered an error whilst performing self.color_check():\n```{e}```")
        await channel.send("I sent 'em all some DMs!")

    @commands.command(brief='Gives you an overview of, and sends a DM to everyone that needs to login/buy spies/get food')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def food_check(self, channel, aa='all'):
        async with aiohttp.ClientSession() as session:
            message = await channel.send("<:thonk:787399051582504980>")
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:500 alliance_id:4729){{data{{nation_name leader_name id alliance_position continent color food vmode dompolicy alliance_id alliance{{name id}} num_cities soldiers tanks aircraft ships missiles nukes offensive_wars{{date attid winner}} defensive_wars{{date attid winner}} ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}) as temp:
                church = (await temp.json())['data']['nations']['data']
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={convent_key}", json={'query': f"{{nations(first:500 alliance_id:7531){{data{{nation_name leader_name id alliance_position continent color food vmode dompolicy alliance_id alliance{{name id}} num_cities soldiers tanks aircraft ships missiles nukes offensive_wars{{date attid winner}} defensive_wars{{date attid winner}} ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}) as temp:
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

            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{colors{{color turn_bonus}}}}"}) as temp:
                res_colors = (await temp.json())['data']['colors']
                colors = {}
                for color in res_colors:
                    colors[color['color']] = color['turn_bonus'] * 12

            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{tradeprices(limit:1){{coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}}}"}) as temp:
                prices = (await temp.json())['data']['tradeprices'][0]
                prices['money'] = 1

            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{treasures{{bonus nation{{id alliance_id}}}}}}"}) as temp:
                treasures = (await temp.json())['data']['treasures']
                
            with requests.Session() as s:
                banker = mongo.users.find_one({"user": 465463547200012298})
                login_url = "https://politicsandwar.com/login/"
                login_data = {
                    "email": str(cipher_suite.decrypt(banker['email'].encode()))[2:-1],
                    "password": str(cipher_suite.decrypt(banker['pwd'].encode()))[2:-1],
                    "loginform": "Login"
                }
                s.post(login_url, data=login_data)

                radiation_page = s.get(f"https://politicsandwar.com/world/radiation/")
                tree = html.fromstring(radiation_page.content)
                info = tree.xpath("//div[@class='col-md-10']/div[@class='row']/div/p")
                for x in info.copy():
                    #print(x.text_content())
                    if "Food" not in x.text_content():
                        info.remove(x)
                    else:
                        info.remove(x)
                        x = re.sub(r"[^0-9.]+", "", x.text_content().strip())
                        info.append(x)
                radiation = {"na": 1 - float(info[0])/100, "sa": 1 - float(info[1])/100, "eu": 1 - float(info[2])/100, "as": 1 - float(info[3])/100, "af": 1 - float(info[4])/100, "au": 1 - float(info[5])/100, "an": 1 - float(info[6])/100}

                info2 = tree.xpath("//div[@class='sidebar'][contains(@style,'padding-left: 20px;')]/text()")
                date = info2[2].strip()
                seasonal_mod = {"na": 1, "sa": 1, "eu": 1, "as": 1, "af": 1, "au": 1, "an": 0.5}
                if "June" in date or "July" in date or "August" in date:
                    seasonal_mod['na'] = 1.2
                    seasonal_mod['as'] = 1.2
                    seasonal_mod['eu'] = 1.2
                    seasonal_mod['sa'] = 0.8
                    seasonal_mod['af'] = 0.8
                    seasonal_mod['au'] = 0.8
                elif "December" in date or "January" in date or "February" in date:
                    seasonal_mod['na'] = 0.8
                    seasonal_mod['as'] = 0.8
                    seasonal_mod['eu'] = 0.8
                    seasonal_mod['sa'] = 1.2
                    seasonal_mod['af'] = 1.2
                    seasonal_mod['au'] = 1.2

            for alliance in aa:
                embed = discord.Embed(title=f"{alliance[0]['alliance']['name']} Food", description="", color=0x00ff00, timestamp=pytz.utc.localize(datetime.utcnow()))
                for nation in alliance:
                    if nation['alliance_position'] == "APPLICANT":
                        continue
                    rev_obj = await utils.revenue_calc(message, nation, radiation, treasures, prices, colors, seasonal_mod, None)
                    if nation['food'] == None:
                        embed.add_field(name=nation['leader_name'], value=f"[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']}) runs out of food in ??? days (??? food).", inline=False)
                        continue
                    days = float(nation['food']) / rev_obj['food']
                    if -1 < days < 1 and int(nation['vmode']) == 0:
                        embed.add_field(name=nation['leader_name'], value=f"[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']}) runs out of food in {math.ceil(days)} days ({nation['food']} food).", inline=False)
                        person = await utils.find_user(self, str(nation['id']))
                        if person == {}:
                            continue
                        user = await self.bot.fetch_user(person['user'])
                        if nation['alliance_id'] == "4729":
                            try:
                                await user.send('Hey, you should get some food. Type "$food" in <#850302301838114826>')
                                print('i just sent a msg to', user)
                            except discord.Forbidden:
                                await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Food', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because it seems that you are running out of food. You don't really want to miss out on 1/3 of your income due to a a lack of food... So please go to the discord and type $food in #pnw-bots, by doing this, Fuquiem will send 100k food your way."})
                        elif nation['alliance_id'] == "7531":
                            try:
                                await user.send("Hey, you should get some food, you don't want to miss out on 1/3 of your income: https://politicsandwar.com/index.php?id=26&display=world")
                                print('i just sent a msg to', user)
                            except discord.Forbidden:
                                await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                                await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Food', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because it seems that you are running out of food. You don't really want to miss out on 1/3 of your income due to a a lack of food... You can go here to buy some food for your nation: <a href=\"https://politicsandwar.com/index.php?id=26&display=world\">https://politicsandwar.com/index.php?id=26&display=world</a>"})

                if len(embed.fields) == 0:
                    await channel.send(f"Nobody is starving in the {alliance[0]['alliance']}!")
                else:
                    await channel.send(embed=embed)
            await message.delete()

    async def spies_check(self, channel, aa='church'):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}') as church:
                church = (await church.json())['nations']
            async with session.get(f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}') as convent:
                convent = (await convent.json())['nations']

            if aa == 'all':
                aa = [church, convent]
            elif aa in 'church':
                aa = [church]
            elif aa in 'convent':
                aa = [convent]
            else:
                await channel.send("That's an illegal argument!")
                return

            for alliance in aa:
                embed = discord.Embed(title=f"{alliance[0]['alliance']} Spies", description="",
                                    color=0x00ff00, timestamp=pytz.utc.localize(datetime.utcnow()))
                for nation in alliance:
                    max_spies = 50
                    if nation['intagncy'] == 1:
                        max_spies += 10
                    if int(nation['spies']) < max_spies and int(nation['vacmode']) == 0:
                        embed.add_field(
                            name=nation['leader'], value=f"[{nation['nation']}](https://politicsandwar.com/nation/id={nation['nationid']}) only has {nation['spies']} spies.", inline=False)
                        person = await utils.find_user(self, str(nation['nationid']))
                        if person == {}:
                            continue
                        if alliance[0]['allianceid'] == 4729:
                            user = await self.bot.fetch_user(person['user'])
                            try:
                                await user.send('Hey, you should get some spies: https://politicsandwar.com/nation/military/spies/')
                                print('i just sent a msg to', user)
                            except discord.Forbidden:
                                await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                                await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Spies', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you don't have max spies. To buy spies, please go here: <a href=\"https://politicsandwar.com/nation/military/spies/\">https://politicsandwar.com/nation/military/spies/</a>"})

                if len(embed.fields) == 0:
                    await channel.send(f"Everyone has max spies in the {alliance[0]['alliance']}!")
                else:
                    await channel.send(embed=embed)

    async def inactivity_check(self, channel, aa='all'):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}') as church:
                church = (await church.json())['nations']
            async with session.get(f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}') as convent:
                convent = (await convent.json())['nations']

            if aa == 'all':
                aa = [church, convent]
            elif aa in 'church':
                aa = [church]
            elif aa in 'convent':
                aa = [convent]
            else:
                await channel.send("That's an illegal argument!")
                return

            for alliance in aa:
                embed = discord.Embed(title=f"{alliance[0]['alliance']} Inactivity", description="",
                                    color=0x00ff00, timestamp=pytz.utc.localize(datetime.utcnow()))
                for nation in alliance:
                    if nation['minutessinceactive'] > 2880 and int(nation['vacmode']) == 0:
                        embed.add_field(
                            name=nation['leader'], value=f"[{nation['nation']}](https://politicsandwar.com/nation/id={nation['nationid']}) has been inactive for {math.ceil(nation['minutessinceactive']/1440)} days.", inline=False)
                        person = await utils.find_user(self, str(nation['nationid']))
                        if person == {}:
                            continue
                        user = await self.bot.fetch_user(person['user'])
                        try:
                            await user.send('Hey, you should log in: https://politicsandwar.com')
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Inactivity', 'message': "Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you have been somewhat inactive lately. He sent this message in the hopes that you might get a notification by email, increasing the probability of you logging in to the game."})
                if len(embed.fields) == 0:
                    await channel.send(f"Everyone has been active in the {alliance[0]['alliance']}!")
                else:
                    await channel.send(embed=embed)
        
    async def color_check(self, channel, aa='all'):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}') as church:
                church = (await church.json())['nations']
            async with session.get(f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}') as convent:
                convent = (await convent.json())['nations']

            if aa == 'all':
                aa = [church, convent]
            elif aa in 'church':
                aa = [church]
            elif aa in 'convent':
                aa = [convent]
            else:
                await channel.send("That's an illegal argument!")
                return

            for alliance in aa:
                embed = discord.Embed(title=f"{alliance[0]['alliance']} Color", description="",
                                    color=0x00ff00, timestamp=pytz.utc.localize(datetime.utcnow()))
                for nation in alliance:
                    if nation['allianceid'] == 4729 and nation['color'] not in ['green', 'beige'] or nation['allianceid'] == 7531 and nation['color'] not in ['blue', 'beige']:
                        if int(nation['vacmode']) > 0:
                            continue
                        embed.add_field(
                            name=nation['leader'], value=f"[{nation['nation']}](https://politicsandwar.com/nation/id={nation['nationid']}) are on {nation['color']}", inline=False)
                        person = await utils.find_user(self, str(nation['nationid']))
                        if person == {}:
                            continue
                        user = await self.bot.fetch_user(person['user'])
                        if nation['allianceid'] == 4729:
                            color = 'green'
                        elif nation['allianceid'] == 7531:
                            color = 'blue'
                        else:
                            continue
                        try:
                            await user.send(f'Hey, you should change your color to {color} in order to get money from the color bonus: https://politicsandwar.com/nation/edit/')
                            print('i just sent a msg to', user)
                        except discord.Forbidden:
                            await channel.send(f"{user} doesn't accept my DMs <:sadcat:787450782747590668>")
                            await session.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': int(person['nationid']), 'subject': 'Color', 'message': f"Hey, this is an automated message from your good friend Fuquiem. He was unable to reach you through discord, so he's contacting you here instead. Fuquiem wanted to get in touch because you are currently not getting any money from the color bonus. If you change your nation's color to {color}, your daily revenue will increase. You can change your color here: <a href=\"https://politicsandwar.com/nation/edit/\">https://politicsandwar.com/nation/edit/</a>"})
                if len(embed.fields) == 0:
                    await channel.send(f"Everyone has the correct colors in the {alliance[0]['alliance']}!")
                else:
                    await channel.send(embed=embed)

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def cityroles(self, ctx):
        await self.city_roles()
        await ctx.send(f'City-dependent roles have been assigned!')
        # merely a debugging command

    async def city_roles(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}') as church_nations:
                church_nations = (await church_nations.json())['nations']
            async with session.get(f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}') as convent_nations:
                convent_nations = (await convent_nations.json())['nations']
            nations = church_nations + convent_nations

            guild = self.bot.get_guild(434071714893398016)
            zerotoninerole = guild.get_role(837789914846330922)
            tentonineteenrole = guild.get_role(837790885512347690)
            twentytotwentyninerole = guild.get_role(837791502272561202)
            thirtyplusrole = guild.get_role(837791514788495397)
            heathen_role = guild.get_role(434248817005690880)
            love_pings = guild.get_role(747179040720289842)
            trader_role = guild.get_role(796057460502298684)
       
            for nation in nations:
                person = await utils.find_user(self, str(nation['nationid']))
                if person == {}:
                    print(f"I couldn't assign a city-role to {nation['nation']}")
                    continue
                user = guild.get_member(person['user'])
                if nation['cities'] < 10:
                    if zerotoninerole not in user.roles:
                        await user.add_roles(zerotoninerole)
                    if tentonineteenrole in user.roles:
                        await user.remove_roles(tentonineteenrole)
                    if twentytotwentyninerole in user.roles:
                        await user.remove_roles(twentytotwentyninerole)
                    if thirtyplusrole in user.roles:
                        await user.remove_roles(thirtyplusrole)
                if 9 < nation['cities'] < 20:
                    if tentonineteenrole not in user.roles:
                        await user.add_roles(tentonineteenrole)
                    if zerotoninerole in user.roles:
                        await user.remove_roles(zerotoninerole)
                    if twentytotwentyninerole in user.roles:
                        await user.remove_roles(twentytotwentyninerole)
                    if thirtyplusrole in user.roles:
                        await user.remove_roles(thirtyplusrole)
                if 19 < nation['cities'] < 30:
                    if twentytotwentyninerole not in user.roles:
                        await user.add_roles(twentytotwentyninerole)
                    if tentonineteenrole in user.roles:
                        await user.remove_roles(tentonineteenrole)
                    if zerotoninerole in user.roles:
                        await user.remove_roles(zerotoninerole)
                    if thirtyplusrole in user.roles:
                        await user.remove_roles(thirtyplusrole)
                if 29 < nation['cities']:
                    if thirtyplusrole not in user.roles:
                        await user.add_roles(thirtyplusrole)
                    if tentonineteenrole in user.roles:
                        await user.remove_roles(tentonineteenrole)
                    if twentytotwentyninerole in user.roles:
                        await user.remove_roles(twentytotwentyninerole)
                    if zerotoninerole in user.roles:
                        await user.remove_roles(zerotoninerole)

            for member in guild.members:
                if zerotoninerole in member.roles or tentonineteenrole in member.roles or twentytotwentyninerole in member.roles or thirtyplusrole in member.roles:
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
    
    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def getsheet(self, ctx):
        print('getting sheet')
        await self.sheet_generator()
        await ctx.send('Finito!')

    async def sheet_generator(self):
        async with aiohttp.ClientSession() as session:
            with open('./data/templates/sheet.txt', 'r', encoding='UTF-8') as file:
                template = file.read()

            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{nations(page:1 first:500 alliance_id:4729){data{id alliance_id alliance_position leader_name nation_name color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available cities{infrastructure barracks factory airforcebase drydock}}}}"}) as temp:
                church = (await temp.json())['data']['nations']['data']
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{nations(page:1 first:500 alliance_id:7531){data{id alliance_id alliance_position leader_name nation_name color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available cities{infrastructure barracks factory airforcebase drydock}}}}"}) as temp:
                convent = (await temp.json())['data']['nations']['data']
            sum = church + convent

            nations = []

            for nation in sum:
                if nation['alliance_position'] != "APPLICANT":
                    nations.append(nation)

            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{alliances(first:2 id:[4729,7531]){data{score nations{num_cities alliance_position}}}}"}) as temp:
                alliances = (await temp.json())['data']['alliances']['data']

            score = alliances[0]['score'] + alliances[1]['score']
            cities = 0
            for i in range(2):
                for nation in alliances[i-1]['nations']:
                    cities += nation['num_cities']

            aa = {"members": len(nations), "cities": cities, "score": score, "mmr": mongo.mmr.find_one({})}

            users = list(self.bot.get_all_members())
            rss = ['aluminum', 'bauxite', 'coal', 'food', 'gasoline', 'iron', 'lead', 'munitions', 'money', 'oil', 'steel', 'uranium']
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{tradeprices(limit:1){coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}"}) as resp:
                prices = (await resp.json())['data']['tradeprices'][0]
                prices['money'] = 1
           
            for nation in nations:
                x = mongo.users.find_one({"nationid": str(nation['id'])})
                nation['user_object'] = {'discordid': '', 'username': '', "audited": ''}
                if x == None:
                    nation['user_object'].update({'discordid': '¯\_(ツ)_/¯', "username": '¯\_(ツ)_/¯'})
                else:
                    for user in users:
                        nation['user_object'].update({'discordid': x['user'], "audited": x['audited']})
                        if user.id == x['user']:
                            nation['user_object']['username'] = str(user)
                            break
                        else:
                            nation['user_object']['username'] = "¯\_(ツ)_/¯"
                y = mongo.total_balance.find_one({"nationid": str(nation['id'])})
                if y == None:
                    nation['user_object'].update({"total": 0, "al": 0, "ba": 0, "co": 0, "fo": 0, "ga": 0, "ir": 0, "le": 0, "mu": 0, "mo": 0, "oi": 0, "st": 0, "ur": 0})
                else:
                    con_total = 0
                    for rs in rss:
                        amount = y[rs[:2].lower()]
                        price = int(prices[rs])
                        con_total += amount * price
                    nation['user_object'].update({"total": round(con_total), "al": y['al'], "ba": y['ba'], "co": y['co'], "fo": y['fo'], "ga": y['ga'], "ir": y['ir'], "le": y['le'], "mu": y['mu'], "mo": y['mo'], "oi": y['oi'], "st": y['st'], "ur": y['ur']})
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

            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            result = Template(template).render(aa=aa,nations=nations,timestamp=timestamp, datetime=datetime)
            mongo.sheet_code.replace_one({},{"code": result})
            print('webpage updated')

    async def alert_scanner(self):
        alerts = list(mongo.users.find({"beige_alerts": {"$exists": True, "$not": {"$size": 0}}}))
        for user in alerts:
            for alert in user['beige_alerts']:
                if datetime.utcnow() >= alert['time']:
                    disc_user = await self.bot.fetch_user(user['user'])
                    await disc_user.send(f"Hey, https://politicsandwar.com/nation/id={alert['id']} is out of beige!")
                    user['beige_alerts'].remove(alert)
                    alert_list = user['beige_alerts']
                    if not alert_list:
                        alert_list = []
                    mongo.users.find_one_and_update({"user": user['user']}, {"$set": {"beige_alerts": alert_list}})
    
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

    async def soxi(self):
        users = list(mongo.users.find({}))
        user_list = []
        for user in users:
            user_list.append({"discordid": user['user'], "nationid": user['nationid']})
        result = str(user_list)
        class soxi(MethodView):
            def get(arg):
                return str(result)
        app.add_url_rule(f"/soxi", view_func=soxi.as_view("soxi"), methods=["GET"])
        return

    async def auto_update(self):
        await self.bot.wait_until_ready()
        Raffle = self.bot.get_cog('Raffle')
        Military = self.bot.get_cog('Military')
        debug_channel = self.bot.get_channel(739155202640183377)
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
                except Exception as e:
                    await debug_channel.send(f"I encountered an error whilst performing Raffle.draw_func():\n```{e}```")

            if now.hour == 0:
                print(datetime.utcnow(), 'hour is 0')
                try:
                    await self.aa_check()
                except Exception as e:
                    await debug_channel.send(f"I encountered an error whilst performing self.aa_check():\n```{e}```")

            if now.hour == 18:
                try:
                    await Military.spies_msg()
                except Exception as e:
                    await debug_channel.send(f"I encountered an error whilst performing Military.spies_msg():\n```{e}```")
                try:
                    await self.raffle_reminder()
                except Exception as e:
                    await debug_channel.send(f"I encountered an error whilst performing self.raffle_reminder():\n```{e}```")
            try:
                await self.alert_scanner()
            except Exception as e:
                await debug_channel.send(f"I encountered an error whilst performing self.alert_scanner():\n```{e}```")
            try:
                await self.sheet_generator()
            except Exception as e:
                await debug_channel.send(f"I encountered an error whilst performing sheet.sheet_generator():\n```{e}```")
            try:
                await self.city_roles()
            except Exception as e:
                await debug_channel.send(f"I encountered an error whilst performing self.city_roles():\n```{e}```")
            try:
                await Military.wars_check()
            except Exception as e:
                await debug_channel.send(f"I encountered an error whilst performing Military.wars_check():\n```{e}```")

            print(datetime.utcnow(), 'finished, going to sleep')
            await asyncio.sleep(60)

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
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

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def spyreminder(self, ctx):
        await ctx.send('I will do my worst...')
        Military = self.bot.get_cog('Military')
        try:
            await Military.spies_msg()
        except Exception as e:
            await ctx.send(f"I encountered an error whilst performing Military.spies_msg():\n```{e}```")
        await ctx.send('Things have been updated from the API.')


def setup(bot):
    bot.add_cog(Update(bot))