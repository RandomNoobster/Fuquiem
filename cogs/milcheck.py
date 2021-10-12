import discord
import requests
import dateutil.parser
import pytz
from main import mongo
from datetime import datetime, timedelta
from lxml import html
from mako.template import Template
from discord.ext import commands
import aiohttp
from keep_alive import app
import random
from flask.views import MethodView
from flask import request
import pathlib
import re
#import chat_exporter
#import io
import asyncio
import os
from cryptography.fernet import Fernet

api_key = os.getenv("api_key")
api_key_2 = os.getenv("api_key_2")
convent_key = os.getenv("convent_api_key")
key = os.getenv("encryption_key")
cipher_suite = Fernet(key)

class Military(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        #self.bot.bg_task = self.bot.loop.create_task(self.war_channels())

    @commands.command(brief='Returns military statistics', help='Accepts an optional argument "convent"')
    @commands.has_any_role('Deacon', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def milcheck(self, ctx, alliance=None):
        message = await ctx.send('Hang on...')
        if alliance is None:
            alliance = 'church'
            aa = requests.get(
                f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}').json()
        elif alliance.lower() in 'convent':
            alliance = 'convent'
            aa = requests.get(
                f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}').json()
        else:
            await message.edit(content='That is not a valid argument!')
            return
        fields1 = []
        fields2 = []
        fields3 = []
        fields4 = []
        fields5 = []
        f = list(mongo[f'{alliance}_nations'].find({}))[0]
        nations = f['results']
        n = 0
        for x in nations:
            f = list(mongo[f'{alliance}_cities'].find({}))[0]
            cinfo = f['results'][n]['cities']
            max_soldiers = 0
            max_tanks = 0
            max_aircraft = 0
            max_ships = 0
            for z in cinfo:
                max_soldiers += (int(z['barracks']) * 3000)
                max_tanks += (int(z['factories']) * 250)
                max_aircraft += (int(z['hangars']) * 15)
                max_ships += (int(z['drydocks']) * 5)
            print(f"{x['name']} - soldiers: {x['soldiers']}/{max_soldiers}, tanks: {x['tanks']}/{max_tanks}, aircraft: {x['aircraft']}/{max_aircraft}, ships: {x['ships']}/{max_ships}")
            fields1.append(
                {'name': f"{x['leadername']}", 'value': f"Soldiers: {x['soldiers']}/{max_soldiers}\nTanks: {x['tanks']}/{max_tanks}\nAircraft: {x['aircraft']}/{max_aircraft}\nShips: {x['ships']}/{max_ships}"})
            rebuy = ''
            if int(x['soldiers']) - max_soldiers < 0 or int(x['tanks']) - max_tanks < 0 or int(x['aircraft']) - max_aircraft < 0 or int(x['ships']) - max_ships < 0:
                rebuy += f"They can rebuy:\n"
                if int(x['soldiers']) - max_soldiers < 0:
                    rebuy += f"{max_soldiers - int(x['soldiers'])} soldiers\n"
                if int(x['tanks']) - max_tanks < 0:
                    rebuy += f"{max_tanks - int(x['tanks'])} tanks\n"
                if int(x['aircraft']) - max_aircraft < 0:
                    rebuy += f"{max_aircraft - int(x['aircraft'])} aircraft\n"
                if int(x['ships']) - max_ships < 0:
                    rebuy += f"{max_ships - int(x['ships'])} ships\n"
                fields2.append(
                    {'name': f"{x['leadername']}", 'value': rebuy})
            avg_bar = (max_soldiers / 3000 / x['cities'])
            avg_fac = (max_tanks / 250 / x['cities'])
            avg_han = (max_aircraft / 15 / x['cities'])
            avg_dry = (max_ships / 5 / x['cities'])
            fields3.append(
                {'name': f"{x['leadername']}", 'value': f'Average improvements:\n{round(avg_bar, 1)}/{round(avg_fac, 1)}/{round(avg_han, 1)}/{round(avg_dry, 1)}'})
            n += 1
        for y in aa['nations']:
            city_count = y['cities']
            fields4.append({'name': f"{y['leader']}", 'value': f"Warchest:\nMoney: ${round(float(y['money']) / 1000000)}M/${round(city_count * 500000 / 1000000)}M\nMunis: {round(float(y['munitions']) / 1000)}k/{round(city_count * 361.2 / 1000)}k\nGas: {round(float(y['gasoline']) / 1000)}k/{round(city_count * 320.25 / 1000)}k\nSteel: {round(float(y['steel']) / 1000)}k/{round(city_count * 619.5 / 1000)}k\n Alum: {round(float(y['aluminum']) / 1000)}k/{round(city_count * 315 / 1000)}k"})
            fields5.append(
                {'name': f"{y['leader']}", 'value': f"Offensive: {y['offensivewars']} wars\nDefensive: {y['defensivewars']} wars"})
        temp_time = dateutil.parser.parse(f['time'])
        embed_time = temp_time.replace(tzinfo=pytz.UTC)
        embed = discord.Embed(title="Militarization pt. 1",
                              description="", color=0x00ff00, timestamp=embed_time)
        embed2 = discord.Embed(title="Militarization pt. 2",
                               description="", color=0x00ff00, timestamp=embed_time)
        embed3 = discord.Embed(title="Militarization pt. 3",
                               description="", color=0x00ff00, timestamp=embed_time)
        embed4 = discord.Embed(title="Militarization pt. 4", description="",
                               color=0x00ff00, timestamp=pytz.utc.localize(datetime.utcnow()))
        embed5 = discord.Embed(title="Militarization pt. 5", description="",
                               color=0x00ff00, timestamp=pytz.utc.localize(datetime.utcnow()))

        async def add_fields(fields, count, embed):
            for x in fields:
                if count == 25:
                    await ctx.send(embed=embed)
                    embed.clear_fields()
                    f = 0
                embed.add_field(name=x['name'], value=x['value'])
                count += 1
            if len(embed.fields) > 0:
                await ctx.send(embed=embed)

        await add_fields(fields1, 0, embed)
        await add_fields(fields2, 0, embed2)
        await add_fields(fields3, 0, embed3)
        await add_fields(fields4, 0, embed4)
        await add_fields(fields5, 0, embed5)
        await message.delete()

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def channels(self, ctx):
        await self.war_channels()
        await ctx.send(f'Done')
        # merely a debugging command

    async def war_channels(self):
        await self.bot.wait_until_ready()
        world_nations = list(mongo.world_nations.find({}))
        debug_channel = self.bot.get_channel(677883771810349067)
        guild = self.bot.get_guild(434071714893398016)
        category = discord.utils.get(
            guild.categories, id=830521271443914773)
        # print(0)
        while True:
            wars = requests.get(
                f'https://politicsandwar.com/api/wars/800&key={api_key_2}&alliance_id=7531,4729', stream=True).json()['wars']
            # print(0.5)
            category = discord.utils.get(
                guild.categories, id=830521271443914773)
            channels = category.channels
            for war in wars:
                if war['defenderAA'] == 'None':
                    continue
                if war['status'] == "Active":
                    #print('found war')
                    is_channel = {'exists': False,
                                  'enemy': None, 'friend': None}
                    if "Atom" in war['attackerAA']:
                        is_channel['enemy'] = 'defenderID'
                        is_channel['friend'] = 'attackerID'
                    elif "Atom" in war['defenderAA']:
                        is_channel['enemy'] = 'attackerID'
                        is_channel['friend'] = 'defenderID'
                    for channel in channels:
                        if str(war[is_channel['enemy']]) == channel.name[channel.name.rfind('-')+1:]:
                            is_channel['exists'] = True
                            break
                    if is_channel['enemy'] == None:
                        #print(war, 'I think the enemy is None, therefore I am skipping')
                        continue
                    enemy = next(
                        item for item in world_nations if item["nationid"] == war[is_channel['enemy']])
                    #print('found enemy')
                    user = mongo.users.find_one(
                        {'nationid': str(war[is_channel['friend']])})
                    if not user:
                        #print(war, 'I could not find the friend, therefore I am skipping')
                        continue
                    # might fail if a user is in th db but not in the server
                    user = guild.get_member(user['user'])
                    # print(user)
                    if not is_channel['exists'] and user:
                        #print('not exists')
                        channel = await guild.create_text_channel(f"{enemy['nation']} {enemy['nationid']}", category=category)
                        message = await channel.send(f"https://politicsandwar.com/nation/id={enemy['nationid']}")
                        await message.pin()
                        channels.append(channel)
                        await debug_channel.send(f"I created `{channel.name}`.")
                        overwrite = channel.overwrites_for(user)
                        await channel.set_permissions(user, read_messages=True)
                        await debug_channel.send(f"I let `{user}` see `{channel.name}`.")
                    elif is_channel['exists'] and user:
                        # print('exists')
                        channel = [
                            channel for channel in channels if str(enemy['nationid']) in channel.name][0]
                        overwrite = channel.overwrites_for(user)
                        # print(overwrite.read_messages)
                        if overwrite.read_messages != True:
                            await channel.set_permissions(user, read_messages=True)
                            await debug_channel.send(f"I let `{user}` see `{channel.name}`.")
            category = discord.utils.get(
                guild.categories, id=830521271443914773)
            channels = category.channels
            await Military.war_channels_channels(channels, wars, guild, debug_channel)
            await asyncio.sleep(60)

    async def war_channels_channels(channels, wars, guild, debug_channel):
        for channel in channels:
            # print(channel)
            relevant_wars = [war for war in wars if str(
                war['attackerID']) == channel.name[channel.name.rfind('-')+1:] or str(war['defenderID']) == channel.name[channel.name.rfind('-')+1:]]
            # print(relevant_wars)
            for rel_war in relevant_wars:
                # print(rel_war)
                # print(1)
                if rel_war['status'] in ["Defender Victory", "Attacker Victory", "Peace", "Expired"]:
                    if "Atom" in rel_war['attackerAA']:
                        enemy = 'defenderID'
                        friend = 'attackerID'
                    elif "Atom" in rel_war['defenderAA']:
                        enemy = 'attackerID'
                        friend = 'defenderID'
                    # print(2)
                    if rel_war[friend] in [war1['attackerID'] for war1 in wars if war1['defenderID'] == rel_war[enemy] and war1['status'] in ['Active', 'Attacker Offered Peace', 'Defender Offered Peace']] or rel_war[friend] in [war1['defenderID'] for war1 in wars if war1['attackerID'] == rel_war[enemy] and war1['status'] in ['Active', 'Attacker Offered Peace', 'Defender Offered Peace']]:
                        #print(rel_war[friend], 'is embrolied in a war with', rel_war[enemy], 'I have therefore skipped them')
                        continue
                    user = mongo.users.find_one(
                        {'nationid': str(rel_war[friend])})
                    # print(3)
                    if user:
                        # might fail if a user is in th db but not in the server
                        user = guild.get_member(user['user'])
                        if not user:
                            #print(rel_war, 'I could not find the member, therefore I am skipping')
                            continue
                        overwrite = channel.overwrites_for(user)
                        if overwrite.read_messages == True:
                            # print(4)
                            # should put in a try, except discord.errors.NotFound
                            await channel.set_permissions(user, overwrite=None)
                            await debug_channel.send(f"I made `{user}` unable to see `{channel.name}`.")
            # print(channel.overwrites)
            if channel.permissions_synced:
                """transcript = await chat_exporter.export(channel, None, 'Europe/London')
                if transcript is None:
                    return
                transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                            filename=f"transcript-{channel.name}.html")
                await debug_channel.send(file=transcript_file)"""
                name = channel.name
                await channel.delete()
                await debug_channel.send(f"I deleted `{name}`.")

    """@commands.command()
    async def save(self, ctx):
        print('on it!')
        transcript = await chat_exporter.export(ctx.channel, None, 'Europe/London')
        print('transcript is done')
        if transcript is None:
            print('transcript is none')
            return
        with open('test.html', 'wb') as f:
            f.write(transcript.encode())
        # transcript_file = discord.File(io.BytesIO(transcript.encode()),
        #                               filename=f"transcript-{ctx.channel.name}.html")
        print('transcript encoded')
        # await ctx.send(file=transcript_file)
        """

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Deacon', 'Advisor', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def add(self, ctx, *, user):
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(user)
        user = await self.bot.fetch_user(person['user'])
        guild = self.bot.get_guild(434071714893398016)
        category = discord.utils.get(
            guild.categories, id=830521271443914773)
        if ctx.channel.category == category:
            overwrite = ctx.channel.overwrites_for(user)
            if overwrite.read_messages != True:
                await ctx.channel.set_permissions(user, read_messages=True)
                await ctx.send(f'I added {user} to this channel.')

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Deacon', 'Advisor', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def remove(self, ctx, *, user):
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(user)
        user = await self.bot.fetch_user(person['user'])
        guild = self.bot.get_guild(434071714893398016)
        category = discord.utils.get(
            guild.categories, id=830521271443914773)
        if ctx.channel.category == category:
            overwrite = ctx.channel.overwrites_for(user)
            if overwrite.read_messages == True:
                await ctx.channel.set_permissions(user, overwrite=None)
                await ctx.send(f'I removed {user} from this channel.')

    @commands.command(aliases=['counter'], brief='Accepts one argument, gives you a pre-filled link to slotter.', help='Accepted arguments include nation name, leader name, nation id and nation link. When browsing the databse, Fuquiem will use the first match, so it can be wise to double check that it returns a slotter link for the correct person.')
    async def counters(self, ctx, *, arg):
        result = None
        try:
            result = list(mongo.world_nations.find({"nation": arg}).collation(
                {"locale": "en", "strength": 1}))[0]
        except:
            try:
                result = list(mongo.world_nations.find({"leader": arg}).collation(
                    {"locale": "en", "strength": 1}))[0]
            except:
                try:
                    arg = int(re.sub("[^0-9]", "", arg))
                    result = list(mongo.world_nations.find({"nationid": arg}).collation(
                        {"locale": "en", "strength": 1}))[0]
                except:
                    pass
        embed = discord.Embed(title="Counters",
                              description=f"[Explore counters against {result['nation']} on slotter](https://slotter.bsnk.dev/search?nation={result['nationid']}&alliances=4729,7531&countersMode=true&threatsMode=false&vm=false&grey=true&beige=false)", color=0x00ff00)
        await ctx.send(embed=embed)

    @commands.command(aliases=['target'], brief='Sends you a pre-filled link to slotter')
    async def targets(self, ctx):
        await ctx.send('This command has been disabled.')
        return
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(ctx.author.id)
        embed = discord.Embed(title="Targets",
                              description=f"[Explore targets on slotter](https://slotter.bsnk.dev/search?nation={person['nationid']}&alliances=3339,619,1584,7000,615,8236,8243,8289,4271,877,8043,8905,8902,8901,7635,7346,4468,8879&countersMode=false&threatsMode=false&vm=false&grey=true&beige=false)", color=0x00ff00)
        await ctx.send(embed=embed)

    @commands.command(brief="Sends a warchest top up to the people in need", help="Requires admin perms, sends people the resources they need in addition to telling people what to deposit.")
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def warchest(self, ctx, alliance=None):
        async with aiohttp.ClientSession() as session:
            if alliance is None:
                alliance = 'church'
                aa = requests.get(
                    f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}').json()
            elif alliance.lower() in 'convent':
                alliance = 'convent'
                aa = requests.get(
                    f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}').json()
            f1 = list(mongo.users.find({}))
            Database = self.bot.get_cog('Database')
            randy = await Database.find_user(465463547200012298)
            if len(randy['email']) <= 1 or len(randy['pwd']) <= 1:
                await ctx.send("<@465463547200012298>'s credentials are wrong?")
            for nation in aa['nations']:
                if int(nation['vacmode']) > 0:
                    continue
                city_count = nation['cities']
                user = None
                excess = ""
                person = await Database.find_user(str(nation['nationid']))
                minmoney = round(city_count * 500000 - float(nation['money']))
                maxmoney = round(city_count * 500000 * 3 - float(nation['money']))
                if maxmoney < 0:
                    if person != {}:
                        user = await self.bot.fetch_user(person['user'])
                        excess += "$" + \
                            str(round(abs(city_count * 500000 * 2 -
                                float(nation['money'])))) + " money, "
                if minmoney < 0:
                    minmoney = 0
                mingasoline = round(city_count * 320.25 -
                                    float(nation['gasoline']))
                maxgasoline = round(city_count * 320.25 * 3 -
                                    float(nation['gasoline']))
                if maxgasoline < 0:
                    if person != {}:
                        user = await self.bot.fetch_user(person['user'])
                        excess += str(round(abs(city_count * 320.25 *
                                    2 - float(nation['gasoline'])))) + " gasoline, "
                if mingasoline < 0:
                    mingasoline = 0
                minmunitions = round(city_count * 361.2 -
                                    float(nation['munitions']))
                maxmunitions = round(city_count * 361.2 * 3 -
                                    float(nation['munitions']))
                if maxmunitions < 0:
                    if person != {}:
                        user = await self.bot.fetch_user(person['user'])
                        excess += str(round(abs(city_count * 361.2 * 2 -
                                    float(nation['munitions'])))) + " munitions, "
                if minmunitions < 0:
                    minmunitions = 0
                minsteel = round(city_count * 619.5 - float(nation['steel']))
                maxsteel = round(city_count * 619.5 * 3 - float(nation['steel']))
                if maxsteel < 0:
                    if person != {}:
                        user = await self.bot.fetch_user(person['user'])
                        excess += str(round(abs(city_count * 619.5 *
                                    2 - float(nation['steel'])))) + " steel, "
                if minsteel < 0:
                    minsteel = 0
                minaluminum = round(city_count * 315 - float(nation['aluminum']))
                maxaluminum = round(city_count * 315 * 3 -
                                    float(nation['aluminum']))
                if maxaluminum < 0:
                    if person != {}:
                        user = await self.bot.fetch_user(person['user'])
                        excess += str(round(abs(city_count * 315 * 2 -
                                    float(nation['aluminum'])))) + " aluminum, "
                if minaluminum < 0:
                    minaluminum = 0

                if minmoney == 0 and mingasoline == 0 and minmunitions == 0 and minsteel == 0 and minaluminum == 0:
                    continue

                try:
                    if user == None:
                        pass
                    else:
                        await user.send(f"Hey, you have an excess of {excess}please deposit it here for safekeeping: https://politicsandwar.com/alliance/id={nation['allianceid']}&display=bank")
                        print('i just sent a msg to', user, excess)
                except discord.errors.Forbidden:
                    await ctx.send(user, 'does not allow my DMs')
                except:
                    print('no dm for', nation['nation'])

                with requests.Session() as s:
                    login_url = "https://politicsandwar.com/login/"
                    login_data = {
                        "email": str(cipher_suite.decrypt(randy['email'].encode()))[2:-1],
                        "password": str(cipher_suite.decrypt(randy['pwd'].encode()))[2:-1],
                        "loginform": "Login"
                    }
                    s.post(login_url, data=login_data)

                    withdraw_url = f'https://politicsandwar.com/alliance/id=4729&display=bank'
                    withdraw_data = {
                        "withmoney": str(minmoney),
                        "withfood": '0',
                        "withcoal": '0',
                        "withoil": '0',
                        "withuranium": '0',
                        "withlead": '0',
                        "withiron": '0',
                        "withbauxite": '0',
                        "withgasoline": str(mingasoline),
                        "withmunitions": str(minmunitions),
                        "withsteel": str(minsteel),
                        "withaluminum": str(minaluminum),
                        "withtype": 'Nation',
                        "withrecipient": nation['nation'],
                        "withnote": 'Resupplying warchest',
                        "withsubmit": 'Withdraw'
                    }

                    start_time = (datetime.utcnow() - timedelta(seconds=5))
                    p = s.post(withdraw_url, data=withdraw_data)
                    end_time = (datetime.utcnow() + timedelta(seconds=5))
                    await ctx.send(f"```{withdraw_data}```")
                    print(f'Response: {p}')
                    success = False
                    async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={person['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                        txids = await txids.json()
                    for x in txids['data']:
                        if x['note'] == 'Resupplying warchest' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                            success = True
                    if success:
                        await ctx.send(f"I can confirm that the transaction to {nation['nation']} ({nation['leader']}) has successfully commenced.")
                    else:
                        await ctx.send(f"<@465463547200012298> the transaction to {nation['nation']} ({nation['leader']}) might have failed. Check this page to be sure:\nhttps://politicsandwar.com/nation/id={nation['nationid']}&display=bank")

    @commands.command(brief="Sends a warchest top up to the person you specified", help="Requires admin perms. It's basically the $warchest command, but it's limited to the person you specified.")
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def resupply(self, ctx, *, arg):
        async with aiohttp.ClientSession() as session:
            Database = self.bot.get_cog('Database')
            person = await Database.find_user(arg)
            randy = await Database.find_user(465463547200012298)

            if len(randy['email']) <= 1 or len(randy['pwd']) <= 1:
                await ctx.send("<@465463547200012298>'s credentials are wrong?")

            async with session.get(f"http://politicsandwar.com/api/nation/id={person['nationid']}&key={api_key}") as temp:
                nation = (await temp.json())
            if nation['allianceid'] == '4729':
                async with session.get(f"http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}") as temp1:
                    aa = (await temp1.json())
            elif nation['allianceid'] == '7531':
                async with session.get(f"http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}") as temp2:
                    aa = (await temp2.json())
            else:
                await ctx.send("They are not in CoA.")

            for member in aa['nations']:
                if str(member['nationid']) == nation['nationid']:
                    nation = member
                    break

            city_count = nation['cities']
            excess = ""
            minmoney = round(city_count * 500000 - float(nation['money']))
            maxmoney = round(city_count * 500000 * 3 - float(nation['money']))
            if maxmoney < 0:
                if person != {}:
                    user = await self.bot.fetch_user(person['user'])
                    excess += "$" + \
                        str(round(abs(city_count * 500000 * 2 -
                            float(nation['money'])))) + " money, "
            if minmoney < 0:
                minmoney = 0
            mingasoline = round(city_count * 320.25 -
                                float(nation['gasoline']))
            maxgasoline = round(city_count * 320.25 * 3 -
                                float(nation['gasoline']))
            if maxgasoline < 0:
                if person != {}:
                    user = await self.bot.fetch_user(person['user'])
                    excess += str(round(abs(city_count * 320.25 *
                                  2 - float(nation['gasoline'])))) + " gasoline, "
            if mingasoline < 0:
                mingasoline = 0
            minmunitions = round(city_count * 361.2 -
                                 float(nation['munitions']))
            maxmunitions = round(city_count * 361.2 * 3 -
                                 float(nation['munitions']))
            if maxmunitions < 0:
                if person != {}:
                    user = await self.bot.fetch_user(person['user'])
                    excess += str(round(abs(city_count * 361.2 * 2 -
                                  float(nation['munitions'])))) + " munitions, "
            if minmunitions < 0:
                minmunitions = 0
            minsteel = round(city_count * 619.5 - float(nation['steel']))
            maxsteel = round(city_count * 619.5 * 3 - float(nation['steel']))
            if maxsteel < 0:
                if person != {}:
                    user = await self.bot.fetch_user(person['user'])
                    excess += str(round(abs(city_count * 619.5 *
                                  2 - float(nation['steel'])))) + " steel, "
            if minsteel < 0:
                minsteel = 0
            minaluminum = round(city_count * 315 - float(nation['aluminum']))
            maxaluminum = round(city_count * 315 * 3 -
                                float(nation['aluminum']))
            if maxaluminum < 0:
                if person != {}:
                    user = await self.bot.fetch_user(person['user'])
                    excess += str(round(abs(city_count * 315 * 2 -
                                  float(nation['aluminum'])))) + " aluminum, "
            if minaluminum < 0:
                minaluminum = 0

            if minmoney == 0 and mingasoline == 0 and minmunitions == 0 and minsteel == 0 and minaluminum == 0:
                await ctx.send("This guy already has enough resources to fulfill minimum requirements!")

            try:
                await user.send(f"Hey, you have an excess of {excess}please deposit it here for safekeeping: https://politicsandwar.com/alliance/id={nation['allianceid']}&display=bank")
                print('i just sent a msg to', user, excess)
            except discord.errors.Forbidden:
                await ctx.send(user, 'does not allow my DMs')
            except:
                print('no dm for', nation['nation'])

            with requests.Session() as s:
                login_url = "https://politicsandwar.com/login/"
                login_data = {
                    "email": str(cipher_suite.decrypt(randy['email'].encode()))[2:-1],
                    "password": str(cipher_suite.decrypt(randy['pwd'].encode()))[2:-1],
                    "loginform": "Login"
                }
                s.post(login_url, data=login_data)

                withdraw_url = f'https://politicsandwar.com/alliance/id=4729&display=bank'
                withdraw_data = {
                    "withmoney": str(minmoney),
                    "withfood": '0',
                    "withcoal": '0',
                    "withoil": '0',
                    "withuranium": '0',
                    "withlead": '0',
                    "withiron": '0',
                    "withbauxite": '0',
                    "withgasoline": str(mingasoline),
                    "withmunitions": str(minmunitions),
                    "withsteel": str(minsteel),
                    "withaluminum": str(minaluminum),
                    "withtype": 'Nation',
                    "withrecipient": nation['nation'],
                    "withnote": 'Resupplying warchest',
                    "withsubmit": 'Withdraw'
                }
                start_time = (datetime.utcnow() - timedelta(seconds=5))
                p = s.post(withdraw_url, data=withdraw_data)
                end_time = (datetime.utcnow() + timedelta(seconds=5))
                await ctx.send(f"```{withdraw_data}```")
                print(f'Response: {p}')
                success = False
                async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={person['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                    txids = await txids.json()
                for x in txids['data']:
                    if x['note'] == 'Resupplying warchest' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                        success = True
                if success:
                    await ctx.send(f"I can confirm that the transaction to {nation['nation']} ({nation['leader']}) has successfully commenced.")
                else:
                    await ctx.send(f"<@465463547200012298> the transaction to {nation['nation']} ({nation['leader']}) might have failed. Check this page to be sure:\nhttps://politicsandwar.com/nation/id={nation['nationid']}&display=bank")

    async def spies_msg(self): #enable in times of war
        return
        async with aiohttp.ClientSession() as session:
            Database = self.bot.get_cog('Database')
            async with session.get(f'http://politicsandwar.com/api/alliance/id=4729&key={api_key}') as resp:
                resp = await resp.json()
            for memberid in resp['member_id_list']:
                async with session.get(f"http://politicsandwar.com/api/nation/id={memberid}&key={api_key}") as member:
                    member = await member.json()
                    if member['espionage_available']:
                        person = await Database.find_user(member['nationid'])
                        user = await self.bot.fetch_user(person['user'])
                        nation = mongo.world_nations.find_one({"nationid": int(member['nationid'])})
                        if nation == None:
                            continue
                        spycount = 1
                        for x in range(60):
                            probability = requests.get(f"https://politicsandwar.com/war/espionage_get_odds.php?id1=341326&id2={member['nationid']}&id3=0&id4=1&id5={spycount}").text
                            if "Greater than 50%" in probability:
                                spycount -= 1
                                enemyspy = ((((100*int(spycount))/(50-25))-1)/3)
                                enemyspy = round(enemyspy)
                                break
                            #if "Lower than 50%" in probability and spycount >= 60:
                            spycount += 1
                        embed = discord.Embed(title="Remember to use your spy ops!",
                                  description=f"You can spy on someone you're fighting, or you can say `{round(float(nation['score']))} / {enemyspy} /<@131589896950251520> <@220333267121864706>` in <#668581622693625907>", color=0x00ff00)
                        print(nation['nation'])
                        try:
                            await user.send(embed=embed)
                        except:
                            pass

    @commands.command(brief='Manually update the #threats channel')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def check_wars(self, ctx):
        await self.wars_check()
        await ctx.send(f'Done!')
        # merely a debugging command

    async def wars_check(self):
        async with aiohttp.ClientSession() as session:
            channel = self.bot.get_channel(842116871322337370)
            await channel.purge()
            async with session.get(f"https://politicsandwar.com/api/wars/500&key={api_key}&alliance_id=7531,4729") as wars:
                wars = await wars.json()
                if wars['success'] == False:
                    print('api call failed, not checking wars')
                    return
            enemy_list = []
            for war in wars['wars']:
                if war['status'] in ['Active', 'Attacker Offered Peace', 'Defender Offered Peace']:
                    async with session.get(f"https://politicsandwar.com/api/war/{war['warID']}&key={api_key_2}") as warinfo:
                        warinfo = await warinfo.json()
                        if warinfo['success'] == False:
                            print('api call failed, not checking this war')
                            continue
                        warinfo = warinfo['war'][0]
                        if 'Atom' in warinfo['aggressor_alliance_name']:
                            warinfo.update({'atom': 'aggressor'})
                            warinfo.update({'enemy': 'defender'})
                        elif 'Atom' in warinfo['defender_alliance_name']:
                            warinfo.update({'atom': 'defender'})
                            warinfo.update({'enemy': 'aggressor'})
                        elif 'Atom Applicant' in warinfo["agressor_alliance_name"]:
                            print('applicant offensive war, skipping')
                            continue
                        else:
                            print('Atom is in not an alliance in the war')
                            continue
                        if mongo.world_nations.find_one({"nationid": int(warinfo[f"{warinfo['enemy']}_id"])}):
                            score =list(mongo.world_nations.find({"nationid": int(warinfo[f"{warinfo['enemy']}_id"])}))[0]["score"]
                        else:
                            score = 0
                        obj = next((item for item in enemy_list if item["nationid"] == int(warinfo[f"{warinfo['enemy']}_id"])), {
                                'nationid': int(warinfo[f"{warinfo['enemy']}_id"]), 'score': score, 'wars': []})
                        try:
                            enemy_list.remove(obj)
                        except:
                            pass
                        obj['wars'].append(warinfo)
                        enemy_list.append(obj)

            await channel.send("~~strikethrough~~ = this person is merely fighting our applicants\n\❗ = a follower of atom is currently losing against this opponent\n\⚔️ = this person is fighting offensive wars against atom\n\🛡️ = this person is fighting defensive wars against atom\n🟢 = you are able to attack this person\n🟡 = this person is in beige\n🔴 = this person is fully slotted")
            enemy_list = sorted(enemy_list, key=lambda k: k['score'])
            async with session.get(f"http://politicsandwar.com/api/nations/?key={api_key}") as temp:
                world_nations = (await temp.json())['nations']
            for enemy in enemy_list:
                try:
                    enemy_nation = [element for element in world_nations if element['nationid'] == enemy['nationid']][0]
                except:
                    print("couldn't find enemy", enemy['nationid'])
                    continue
                if enemy_nation['alliance'] == "None":
                    continue

                applicant = ''
                if enemy_nation['allianceposition'] == 1:
                    applicant = ' (Applicant)'
                circle = '🟢'
                exclamation = ''
                sword = ''
                shield = ''
                str_start = '~~'
                str_end = '~~'
                for warinfo in enemy['wars']:
                    if int(warinfo[f"{warinfo['atom']}_resistance"]) <= int(warinfo[f"{warinfo['enemy']}_resistance"]):
                        exclamation = '\❗'
                    if enemy_nation['color'] == 'beige' and circle != '🔴':
                        circle = '🟡'
                    if enemy_nation['defensivewars'] == 3:
                        circle = '🔴'
                    if 'Applicant' not in warinfo[f"{warinfo['atom']}_alliance_name"]:
                        str_start = ''
                        str_end = ''
                    if enemy_nation['nationid'] == int(warinfo["aggressor_id"]):
                        sword = '\⚔️'
                    if enemy_nation['nationid'] == int(warinfo["defender_id"]):
                        shield = '\🛡️'

                minscore = round(enemy_nation['score'] / 1.75)
                maxscore = round(enemy_nation['score'] / 0.75)
                await channel.send(content=f"{str_start}Priority target! {sword}{shield}{exclamation}{circle} Defensive range: {minscore} - {maxscore} <https://politicsandwar.com/nation/id={enemy['nationid']}>, {enemy_nation['alliance']}{applicant}{str_end}", embed=None)

    def raidspage(self, attacker, targets, endpoint, invoker, beige_alerts):
        template = """
        <!DOCTYPE html>
        <head>
            <link rel="icon" href="https://i.ibb.co/2dX2WYW/atomism-ICONSSS.png">
            <title>Raid targets</title>
        </head>
        <body>
            <div style="overflow-x:auto;">
                <style>
                    table {
                        font-family: Verdana, Arial, Monaco;
                        font-size: 80%;
                        border-collapse: collapse;
                        width: 100%;
                    }

                    th {
                        text-align: left;
                        padding: 6px;
                    }

                    tr:nth-child(even) {
                        background-color: #f2f2f2
                    }

                    th {
                        background-color: #4CAF50;
                        color: white;
                        cursor: pointer;
                    }

                    th:hover {
                        background-color: #008000;
                    }

                    td {
                        position: relative;
                        text-align: left;
                        padding: 1px 6px;
                        white-space: nowrap;
                    }

                    tr.strikeout td:before {
                        content: " ";
                        position: absolute;
                        top: 50%;
                        left: 0;
                        border-bottom: 1px solid #111;
                        width: 100%;
                    }

                </style>
                <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
                <script>
                    function postreq(id, turns, name, btn_id) {
                        console.log('button click registered')
                        var to_parse = {turns: turns, invoker: "${invoker}", id: id, endpoint: "${endpoint}"}

                        $.ajax({
                            url: 'https://fuquiem.karemcbob.repl.co/raids/${endpoint}',
                            type: 'POST',
                            data: JSON.stringify(to_parse),
                            contentType: "application/json; charset=utf-8",
                            dataType: "text",
                            success: function(data) {
                                console.log(data);
                                var abc = document.getElementById(btn_id);
                                abc.innerHTML = "Reminder active";
                            },
                            error: function(er) {
                                console.log(er);
                                var abc = document.getElementById(btn_id);
                                abc.innerHTML = "<b>Error! Try reloading the page.</b>";
                            }
                        });
                    };
                </script>
                <table id="grid">
                    <tbody>
                        <tr>
                            <th data-type="number">Nation id</th>
                            <th data-type="string">Nation name</th>
                            <th data-type="string">Leader name</th>
                            <th data-type="string">Alliance</th>
                            <th data-type="string">Alliance pos.</th>
                            <th data-type="number">Cities</th>
                            <th data-type="number">Infra/city</th>
                            <th data-type="number">Score</th>
                            <th data-type="string">Color</th>
                            <th data-type="number">Beigeturns</th>
                            <th data-type="string">Reminder</th>
                            <th data-type="number">Days inactive</th>
                            <th data-type="number">Soldiers</th>
                            <th data-type="number">Tanks</th>
                            <th data-type="number">Aircraft</th>
                            <th data-type="number">Ships</th>
                            <th data-type="number">Missiles</th>
                            <th data-type="number">Nukes</th>
                            <th data-type="string">Chance to win battles</th>
                            <th data-type="string">Ongoing defensive wars</th>
                            <th data-type="number">Monetary Net Income</th>
                            <th data-type="number">Net Cash Income</th>
                            <th data-type="number">Days since war</th>
                            <th data-type="number">Previous beige loot (nation)</th>
                            <th data-type="number">Previous beige loot (aa)</th>
                            <th data-type="string">Same alliance</th>
                        </tr>
                        % for nation in targets:
                            <td>${nation['id']}</td>
                            <td><a href="https://politicsandwar.com/nation/id=${nation['id']}" target="_blank">${nation['nation_name']}</a></td>
                            <td>${nation['leader_name']}</td>

                            % if nation['alliance']['id'] != 0:
                            <td><a href="https://politicsandwar.com/alliance/id=${nation['alliance']['id']}" target="_blank">${nation['alliance']['name']}</a></td>
                            % else:
                            <td>None</td>
                            % endif

                            % if nation['alliance_position'] == "NOALLIANCE":
                            <td>None</td>
                            % else:
                            <td>${nation['alliance_position'].lower().capitalize()}</td>
                            % endif
                            
                            <td>${nation['num_cities']}</td>
                            <td>${round(float(nation['infrastructure'])/nation['num_cities'])}</td>
                            <td>${nation['score']}</td>
                            <td>${nation['color']}</td>
                            <td>${nation['beigeturns']}</td>

                            % if nation['beigeturns'] > 0:
                                % if nation['id'] not in [alert['id'] for alert in beige_alerts]:
                                    <td id="btn${nation['id']}">
                                        <button onclick="postreq(${nation['id']}, ${nation['beigeturns']}, '${nation['nation_name']}', 'btn${nation['id']}')">Remind me</button>
                                    </td>
                                % else:
                                    <td>Reminder active</td>
                                % endif
                            % else:
                            <td>Not beige</td>
                            % endif

                            % if nation['last_active'] == '-0001-11-30 00:00:00':
                            <td>0</td>
                            % else:
                            <td>${(datetime.utcnow() - datetime.strptime(nation['last_active'], "%Y-%m-%d %H:%M:%S")).days}</td>
                            % endif

                            <td>${nation['soldiers']}</td>
                            <td>${nation['tanks']}</td>
                            <td>${nation['aircraft']}</td>
                            <td>${nation['ships']}</td>
                            <td>${nation['missiles']}</td>
                            <td>${nation['nukes']}</td>
                            <td>${nation['winchance']}</td>
                            <td>${nation['def_slots']}/3</td>
                            <td style="text-align:right">${nation['monetary_net_num']}</td>
                            <td style="text-align:right">${nation['net_cash']}</td>
                            <td style="text-align:right">${nation['time_since_war']}</td>
                            <td style="text-align:right">${nation['nation_loot']}</td>
                            <td style="text-align:right">${nation['aa_loot']}</td>
                            % if nation['same_aa'] == True:
                            <td>Yes</td>
                            % elif nation['same_aa'] == False:
                            <td>No</td>
                            % else:
                            <td>${nation['same_aa']}</td>
                            % endif
                        </tr>
                        % endfor

                </table>
                <p>Last updated: ${datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC<br><a href="http://www.timezoneconverter.com/cgi-bin/tzc.tzc" target="_blank">Timezone converter</a></p>
                <script>
                    const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;

                    const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
                        v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
                        )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

                    // do the work...
                    document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {
                        const table = th.closest('table');
                        Array.from(table.querySelectorAll('tr:nth-child(n+2)'))
                            .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
                            .forEach(tr => table.appendChild(tr) );
                    })));
                </script>
            </div>
        </body>
        </html>"""
        print(invoker)
        result = Template(template).render(attacker=attacker, targets=targets, endpoint=endpoint, invoker=str(invoker), beige_alerts=beige_alerts, datetime=datetime)
        return str(result)

    @commands.command(brief='something something')
    @commands.has_any_role('Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def mmr(self, ctx, mmr):
        mmr = re.sub("[^0-9]", "", mmr)
        min_bar = int(mmr[0])
        min_fac = int(mmr[1])
        min_han = int(mmr[2])
        min_dry = int(mmr[3])
        mongo.mmr.drop()
        mongo.mmr.insert_one({"bar": min_bar, "fac": min_fac, "han": min_han, "dry": min_dry})
        mmr = '/'.join(mmr[i:i+1] for i in range(0, len(mmr), 1))
        await ctx.send(f"I set the mmr to {mmr}")

    @commands.command(brief='something something')
    @commands.has_any_role('Pupil', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def raids(self, ctx, *, arg=None):
        invoker = str(ctx.author.id)
        async with aiohttp.ClientSession() as session:
            message = await ctx.send('Finding person...')
            Economic = self.bot.get_cog('Economic')
            Database = self.bot.get_cog('Database')
            if arg == None:
                arg = ctx.author.id
            attacker = await Database.find_user(arg)
            if attacker == {}:
                try:
                    attacker = list(mongo.world_nations.find({"nation": arg}).collation(
                        {"locale": "en", "strength": 1}))[0]
                except:
                    try:
                        attacker = list(mongo.world_nations.find({"leader": arg}).collation(
                            {"locale": "en", "strength": 1}))[0]
                    except:
                        try:
                            arg = int(re.sub("[^0-9]", "", arg))
                            attacker = list(mongo.world_nations.find({"nationid": arg}).collation(
                                {"locale": "en", "strength": 1}))[0]
                        except:
                            attacker = None
                if not attacker:
                    await message.edit(content='I could not find that person!')
                    return
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{attacker['nationid']}){{data{{nation_name score id population soldiers tanks aircraft ships}}}}}}"}) as temp:
                atck_ntn = (await temp.json())['data']['nations']['data'][0]
            if atck_ntn == None:
                await message.edit(content='I did not find that person!')
                return
            minscore = round(atck_ntn['score'] * 0.75)
            maxscore = round(atck_ntn['score'] * 1.75)

            embed = discord.Embed(title=f"Presentation", description="Do you want to get your targets\n\n:one: - here on discord\n:two: - as a webpage", color=0x00ff00)
            await message.edit(content="", embed=embed)

            react01 = asyncio.create_task(message.add_reaction("1\N{variation selector-16}\N{combining enclosing keycap}"))
            react02 = asyncio.create_task(message.add_reaction("2\N{variation selector-16}\N{combining enclosing keycap}"))
            await asyncio.gather(react01, react02)

            while True:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=300)
                if reaction.message != message or user.id != ctx.author.id:
                    continue

                if str(reaction.emoji) == "1\N{variation selector-16}\N{combining enclosing keycap}":
                    webpage = False
                    break

                elif str(reaction.emoji) == "2\N{variation selector-16}\N{combining enclosing keycap}":
                    webpage = True
                    break

            await message.clear_reactions()
            
            embed = discord.Embed(title=f"Filters (1/2)", description="Do you want to include...\n\n:one: - All nations\n:two: - Applicants and nations not in alliances\n:three: - Nations not in alliances", color=0x00ff00)
            await message.edit(content="", embed=embed)

            react11 = asyncio.create_task(message.add_reaction("1\N{variation selector-16}\N{combining enclosing keycap}"))
            react12 = asyncio.create_task(message.add_reaction("2\N{variation selector-16}\N{combining enclosing keycap}"))
            react13 = asyncio.create_task(message.add_reaction("3\N{variation selector-16}\N{combining enclosing keycap}"))
            await asyncio.gather(react11, react12, react13)

            while True:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=300)
                if reaction.message != message or user.id != ctx.author.id:
                    continue

                if str(reaction.emoji) == "1\N{variation selector-16}\N{combining enclosing keycap}":
                    applicants = False
                    who = ""
                    break

                elif str(reaction.emoji) == "2\N{variation selector-16}\N{combining enclosing keycap}":
                    applicants = True
                    who = " alliance_id:0"
                    break

                elif str(reaction.emoji) == "3\N{variation selector-16}\N{combining enclosing keycap}":
                    applicants = False
                    who = " alliance_id:0"
                    break

            embed = discord.Embed(title=f"Filters (2/3)", description="How many active defensive wars should they have?\n\n:zero: - No active wars\n:one: - One or less wars\n:two: - Two or less wars\n:three: - Three or less wars", color=0x00ff00)
            await message.edit(content="", embed=embed)
            await message.clear_reactions()

            react01 = asyncio.create_task(message.add_reaction("0\N{variation selector-16}\N{combining enclosing keycap}"))
            react02 = asyncio.create_task(message.add_reaction("1\N{variation selector-16}\N{combining enclosing keycap}"))
            react03 = asyncio.create_task(message.add_reaction("2\N{variation selector-16}\N{combining enclosing keycap}"))
            react04 = asyncio.create_task(message.add_reaction("3\N{variation selector-16}\N{combining enclosing keycap}"))
            await asyncio.gather(react01, react02, react03, react04)

            while True:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=300)
                if reaction.message != message or user.id != ctx.author.id:
                    continue
                
                if str(reaction.emoji) == "0\N{variation selector-16}\N{combining enclosing keycap}":
                    max_wars = 0
                    break

                elif str(reaction.emoji) == "1\N{variation selector-16}\N{combining enclosing keycap}":
                    max_wars = 1
                    break

                elif str(reaction.emoji) == "2\N{variation selector-16}\N{combining enclosing keycap}":
                    max_wars = 2
                    break

                elif str(reaction.emoji) == "3\N{variation selector-16}\N{combining enclosing keycap}":
                    max_wars = 3
                    break
            
            embed = discord.Embed(title=f"Filters (3/3)", description="Do you want to include beige nations?", color=0x00ff00)
            await message.edit(content="", embed=embed)
            await message.clear_reactions()
            react21 = asyncio.create_task(message.add_reaction("✅"))
            react22 = asyncio.create_task(message.add_reaction("<:redcross:862669500977905694>"))
            await asyncio.gather(react21, react22)

            rndm = random.choice(["", "2", "3"])
            with open (pathlib.Path.cwd() / 'data' / 'attachments' / f'waiting{rndm}.gif', 'rb') as gif:
                gif = discord.File(gif)

            while True:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=300)
                if reaction.message != message or user.id != ctx.author.id:
                    continue

                if str(reaction.emoji) == "✅":
                    beige = True
                    break

                elif str(reaction.emoji) == "<:redcross:862669500977905694>":
                    beige = False
                    break

            target_list = []
            applicant_futures = []
            pages = 1
            
            await message.clear_reactions()
            await message.edit(content="Getting targets...", embed=None)
            waiting_gif = await ctx.send(file=gif)
            
            if applicants == True:
                async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:300 min_score:{minscore} max_score:{maxscore} vmode:false alliance_position:1){{paginatorInfo{{lastPage}}}}}}"}) as temp:
                    pages += (await temp.json())['data']['nations']['paginatorInfo']['lastPage']
                applicant_futures = [session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:{n} first:300 min_score:{minscore} max_score:{maxscore} vmode:false alliance_position:1){{data{{id flag nation_name last_active leader_name continent dompolicy population alliance_id beigeturns score color soldiers tanks aircraft ships missiles nukes alliance{{name id}} offensive_wars{{winner}} defensive_wars{{date winner turnsleft attacks{{loot_info victor moneystolen}}}} alliance_position num_cities cities{{powered infrastructure}} ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}) for n in range(1, pages)]

            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:300 min_score:{minscore} max_score:{maxscore} vmode:false{who}){{paginatorInfo{{lastPage}}}}}}"}) as temp1:
                pages += (await temp1.json())['data']['nations']['paginatorInfo']['lastPage']
            start = datetime.utcnow()

            futures = [session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:{n} first:300 min_score:{minscore} max_score:{maxscore} vmode:false{who}){{data{{id flag nation_name last_active leader_name continent dompolicy population alliance_id beigeturns score color soldiers tanks aircraft ships missiles nukes alliance{{name id}} offensive_wars{{winner}} defensive_wars{{date winner turnsleft attacks{{loot_info victor moneystolen}}}} alliance_position num_cities cities{{powered infrastructure}} ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}) for n in range(1, pages)] + applicant_futures
            done_jobs = await asyncio.gather(*futures)
            end = datetime.utcnow()
            #print((end - start).seconds, 'sec')
            await message.edit(content="Caching targets...")
            for done_job in done_jobs:
                done_job = await done_job.json()
                for x in done_job['data']['nations']['data']:
                    if beige:
                        pass
                    else:
                        if x['color'] == "beige":
                            continue
                        else: 
                            pass
                    used_slots = 0
                    for war in x['defensive_wars']:
                        if war['turnsleft'] > 0:
                            used_slots += 1
                        for attack in war['attacks']:
                            if attack['loot_info']:
                                attack['loot_info'] = attack['loot_info'].replace("\r\n", "")
                    if used_slots > max_wars:
                        continue
                    target_list.append(x)
                    
            if len(target_list) == 0:
                await waiting_gif.delete()
                await message.edit(content="No targets matched your criteria!")
                return
            #await message.edit(content=f'That took {(end - start).seconds} seconds')

            filters = "No active filters"
            if not beige or applicants or who != "" or max_wars != 3:
                filters = "Active filters:"
                if not beige:
                    filters += " hide beige nations"
                if who != "":
                    if not beige:
                        filters += ","
                    if applicants:
                        filters += " hide full alliance members"
                    else:
                        filters += " hide full alliance members and applicants"
                if max_wars != 3:
                    if not beige or who != "":
                        filters += ","
                    filters += f" {max_wars} or less active wars"

            await message.edit(content="Getting color bloc values...")
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{colors{{color turn_bonus}}}}"}) as temp:
                res_colors = (await temp.json())['data']['colors']
            colors = {}
            for color in res_colors:
                colors[color['color']] = color['turn_bonus'] * 12

            await message.edit(content="Getting resource prices...")
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{tradeprices(limit:1){{coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}}}"}) as temp:
                prices = (await temp.json())['data']['tradeprices'][0]
            prices['money'] = 1

            await message.edit(content="Getting treasures...")
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{treasures{{bonus nation{{id alliance_id}}}}}}"}) as temp:
                treasures = (await temp.json())['data']['treasures']

            await message.edit(content="Getting food modifiers...")
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

            await message.edit(content='Calculating best targets...')

            for target in target_list:
                embed = discord.Embed(title=f"{target['nation_name']}", url=f"https://politicsandwar.com/nation/id={target['id']}", description=f"{filters}", color=0x00ff00)
                embed.set_thumbnail(url=target['flag'])
                prev_nat_loot = False
                prev_aa_loot = False
                target['infrastructure'] = 0
                target['def_slots'] = 0
                target['time_since_war'] = "14+"
                
                if target['defensive_wars'] != []:
                    for war in target['defensive_wars']:
                        if war['date'] == '-0001-11-30 00:00:00':
                            target['defensive_wars'].remove(war)
                        if war['turnsleft'] > 0:
                            target['def_slots'] += 1
                            
                    wars = sorted(target['defensive_wars'], key=lambda k: k['date'], reverse=True)
                    war = wars[0]
                    if target['def_slots'] == 0:
                        target['time_since_war'] = (datetime.utcnow() - datetime.strptime(war['date'], "%Y-%m-%d %H:%M:%S")).days
                    else:
                        target['time_since_war'] = "Ongoing"
                    if war['winner'] in [0, target['id']]:
                        rating += 10
                    else:
                        nation_loot = 0
                        aa_loot = 0
                        prev_aa_loot = True
                        prev_nat_loot = True
                        same_aa = False
                        for attack in war['attacks']:
                            if attack['victor'] == target['id']:
                                continue
                            #if attack['moneystolen']:
                            #    nation_loot += attack['moneystolen']
                            ### probably wont rename everyhing to just "beige loot". this is why everything is called nation loot instead.
                            if attack['loot_info']:
                                text = attack['loot_info']
                                if "won the war and looted" in text:
                                    text = text[text.index('looted') + 7 :text.index(' Food. ')]
                                    text = re.sub(r"[^0-9-]+", "", text.replace(", ", "-"))
                                    rss = ['money', 'coal', 'oil', 'uranium', 'iron', 'bauxite', 'lead', 'gasoline', 'munitions', 'steel', 'aluminum', 'food']
                                    n = 0
                                    loot = {}
                                    for sub in text.split("-"):
                                        loot[rss[n]] = int(sub)
                                        n += 1
                                    for rs in rss:
                                        amount = loot[rs]
                                        price = int(prices[rs])
                                        nation_loot += amount * price
                                elif "alliance bank, taking:" in text:
                                    if target['alliance']:
                                        if target['alliance']['name'] in text:
                                            same_aa = True
                                    text = text[text.index('taking:') + 8 :text.index(' Food.')]
                                    text = re.sub(r"[^0-9-]+", "", text.replace(", ", "-"))
                                    rss = ['money', 'coal', 'oil', 'uranium', 'iron', 'bauxite', 'lead', 'gasoline', 'munitions', 'steel', 'aluminum', 'food']
                                    n = 0
                                    loot = {}
                                    for sub in text.split("-"):
                                        loot[rss[n]] = int(sub)
                                        n += 1
                                    for rs in rss:
                                        amount = loot[rs]
                                        price = int(prices[rs])
                                        aa_loot += amount * price
                                else:
                                    continue
                        target['nation_loot'] = round(nation_loot)
                        target['aa_loot'] = round(aa_loot)
                        target['same_aa'] = same_aa
                        embed.add_field(name="Previous nation loot", value=f"${round(target['nation_loot']):,}")

                        if same_aa or target['aa_loot'] == 0:
                            embed.add_field(name="Previous aa loot", value=f"${round(target['aa_loot']):,}")
                        else:
                            embed.add_field(name="Previous aa loot", value=f"${round(target['aa_loot']):,}\nNOTE: Different aa!")

                if prev_nat_loot == False:
                    embed.add_field(name="Previous nation loot", value="NaN")
                    target['nation_loot'] = "NaN"
                if prev_aa_loot in [False, 0]:
                    embed.add_field(name="Previous aa loot", value="NaN")
                    if prev_aa_loot == False:
                        target['aa_loot'] = "NaN"
                    else:
                        target['aa_loot'] = 0
                    target['same_aa'] = "Irrelevant"
                embed.add_field(name="Slots", value=f"{target['def_slots']}/3 used slots") 

                target['beige_loot'] = None
                rating = 0 
                #need to add ratings for all the attributes
                if target['last_active'] == '-0001-11-30 00:00:00':
                    days_inactive = 0
                else:
                    days_inactive = (datetime.utcnow() - datetime.strptime(target['last_active'], "%Y-%m-%d %H:%M:%S")).days

                for city in target['cities']:
                    target['infrastructure'] += city['infrastructure']

                embed.add_field(name="Beige", value=f"{target['beigeturns']} turns")

                embed.add_field(name="Inactivity", value=f"{days_inactive} days")

                if target['alliance']:
                    embed.add_field(name="Alliance", value=f"[{target['alliance']['name']}](https://politicsandwar.com/alliance/id={target['alliance']['id']})\n{target['alliance_position'].lower().capitalize()}")
                else:
                    target['alliance'] = {"name": "None", "id": 0}
                    embed.add_field(name="Alliance", value=f"No alliance")

                embed.add_field(name="Soldiers", value=f"{target['soldiers']:,} soldiers")

                embed.add_field(name="Tanks", value=f"{target['tanks']:,} tanks")

                embed.add_field(name="Aircraft", value=f"{target['aircraft']} aircraft")

                embed.add_field(name="Ships", value=f"{target['ships']:,} ships")

                embed.add_field(name="Nukes", value=f"{target['nukes']:,} nukes")

                embed.add_field(name="Missiles", value=f"{target['missiles']:,} missiles")

                rev_obj = await Economic.revenue_calc(message, target, radiation, treasures, prices, colors, seasonal_mod, None)

                target['monetary_net_num'] = rev_obj['monetary_net_num']
                target['net_cash'] = rev_obj['net_cash_num']
                
                embed.add_field(name="Monetary Net Income", value=rev_obj['mon_net_txt'])
                embed.add_field(name="Net Cash Income", value=rev_obj['money_txt'])

                win_rate = 0

                try:
                    x = (target['soldiers'] * 1.75 + target['tanks'] * 40) / (atck_ntn['soldiers'] * 1.75 + atck_ntn['tanks'] * 40 + atck_ntn['population'] * 0.0025)
                    if x > 2:
                        win_rate += 0
                    elif x < 0.4:
                        win_rate += 1
                    else:
                        win_rate += 1 - (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
                except ZeroDivisionError:
                    win_rate += 0

                try:
                    x = (atck_ntn['aircraft'] * 3) / (target['aircraft'] * 3)
                    if x > 2:
                        win_rate += 1
                    elif x < 0.4:
                        win_rate += 0
                    else:
                        win_rate += 1 - (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
                except ZeroDivisionError:
                    win_rate += 1

                try:
                    x = (atck_ntn['ships'] * 4) / (target['ships'] * 4)
                    if x > 2:
                        win_rate += 1
                    elif x < 0.4:
                        win_rate += 0
                    else:
                        win_rate += 1 - (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
                except ZeroDivisionError:
                    win_rate += 1

                target['winchance'] = round((win_rate*100)/3)
                embed.add_field(name="Chance to win battles", value=f"{round(win_rate/3)}%")
                if not webpage:
                    target['embed'] = embed
                
        best_targets = sorted(target_list, key=lambda k: k['monetary_net_num'], reverse=True)

        if webpage:
            endpoint = datetime.utcnow().strftime('%d%H%M%S')
            class webraid(MethodView):
                def get(raidclass):
                    #print(invoker)
                    beige_alerts = mongo.users.find_one({"user": int(invoker)})['beige_alerts']
                    return self.raidspage(atck_ntn, best_targets, endpoint, invoker, beige_alerts)

                def post(raidclass):
                    data = request.json
                    reminder = {}
                    #print(data)
                    turns = int(data['turns'])
                    time = datetime.utcnow()
                    if time.hour % 2 == 0:
                        time += timedelta(hours=turns*2)
                    else:
                        time += timedelta(hours=turns*2-1)
                    reminder['time'] = datetime(time.year, time.month, time.day, time.hour)
                    reminder['id'] = str(data['id'])
                    mongo.users.find_one_and_update({"user": int(data['invoker'])}, {"$push": {"beige_alerts": reminder}})
                    #beige_alerts = mongo.users.find_one({"user": int(data['invoker'])})['beige_alerts']
                    return "you good" #self.raidspage(data['attacker'], ast.literal_eval(f"""{data['targets']}"""), endpoint, data['invoker'], beige_alerts)
                    #in "var to_parse" -> attacker: ${attacker}, targets: `${targets}`,

            #@app.route(f"/raids/{atck_ntn['id']}")
            app.add_url_rule(f"/raids/{endpoint}", view_func=webraid.as_view(str(datetime.utcnow())), methods=["GET", "POST"]) # this solution of adding a new page instead of updating an existing for the same nation is kinda dependent on the bot resetting every once in a while, bringing down all the endpoints
            await waiting_gif.delete()
            await message.edit(content=f"Go to https://fuquiem.karemcbob.repl.co/raids/{endpoint}")
            return
        
        pages = len(target_list)
        msg_embd = best_targets[0]['embed']
        msg_embd.set_footer(text=f"Page {1}/{pages}")
        await waiting_gif.delete()
        await message.edit(content="", embed=msg_embd)
        await message.add_reaction("◀️")
        await message.add_reaction("▶️")
        await message.add_reaction("🕰️")
        
        cur_page = 1

        async def message_checker():
            print('message')
            while True:
                try:
                    nonlocal cur_page
                    command = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=600)
                    if "page" in command.content.lower():
                        try:
                            cur_page = int(re.sub("\D", "", command.content))
                            msg_embd = best_targets[cur_page-1]['embed']
                            msg_embd.set_footer(text=f"Page {cur_page}/{pages}")
                            await message.edit(content="", embed=msg_embd)
                            await command.delete()
                        except:
                            msg_embd = best_targets[0]['embed']
                            msg_embd.set_footer(text=f"Page {1}/{pages}")
                            await message.edit(content="**Something went wrong with your input!**", embed=msg_embd)
                except asyncio.TimeoutError:
                    await message.edit(content="**Command timed out!**")
                    print('message break')
                    break
                
        async def reaction_checker():
            print('reaction')
            while True:
                try:
                    nonlocal cur_page
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=600)
                    if user.id != ctx.author.id or reaction.message != message:
                        continue
                    if str(reaction.emoji) == "▶️" and cur_page != pages:
                        cur_page += 1
                        msg_embd = best_targets[cur_page-1]['embed']
                        msg_embd.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(content="", embed=msg_embd)
                        await message.remove_reaction(reaction, ctx.author)

                    elif str(reaction.emoji) == "◀️" and cur_page > 1:
                        cur_page -= 1
                        msg_embd = best_targets[cur_page-1]['embed']
                        msg_embd.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(content="", embed=msg_embd)
                        await message.remove_reaction(reaction, ctx.author)
                    
                    elif str(reaction.emoji) == "▶️" and cur_page == pages:
                        cur_page = 1
                        msg_embd = best_targets[cur_page-1]['embed']
                        msg_embd.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(content="", embed=msg_embd)
                        await message.remove_reaction(reaction, ctx.author)

                    elif str(reaction.emoji) == "◀️" and cur_page == 1:
                        cur_page = pages
                        msg_embd = best_targets[cur_page-1]['embed']
                        msg_embd.set_footer(text=f"Page {cur_page}/{pages}")
                        await message.edit(content="", embed=msg_embd)
                        await message.remove_reaction(reaction, ctx.author)
                    
                    elif str(reaction.emoji) == "🕰️":
                        reminder = {}
                        cur_embed = best_targets[cur_page-1]
                        turns = cur_embed['beigeturns']
                        if turns == 0:
                            await message.edit(content="**They are already out of beige!**")
                            continue
                        time = datetime.utcnow()
                        if time.hour % 2 == 0:
                            time += timedelta(hours=turns*2)
                        else:
                            time += timedelta(hours=turns*2-1)
                        reminder['time'] = datetime(time.year, time.month, time.day, time.hour)
                        reminder['id'] = cur_embed['id']
                        mongo.users.find_one_and_update({"user": ctx.author.id}, {"$push": {"beige_alerts": reminder}})
                        await message.edit(content="**Alert was added!**")

                    else:
                        await message.remove_reaction(reaction, ctx.author)

                except asyncio.TimeoutError:
                    await message.edit(content="**Command timed out!**")
                    print('reaction break')
                    break

        msgtask = asyncio.create_task(message_checker())
        reacttask = asyncio.create_task(reaction_checker())

        await asyncio.gather(msgtask, reacttask)

    @commands.command(aliases=['bsim', 'bs'], brief='Simulate battles between two nations', help="Accepts up to two arguments. The first argument is the attacking nation, whilst the latter is the defending nation. If only one argument is provided, Fuquiem will assume that you are the defender")
    @commands.has_any_role('Pupil', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def battlesim(self, ctx, defender, attacker=None):
        message = await ctx.send('Alright, give me a sec to calculate 5000 battles...')
        Database = self.bot.get_cog('Database')
        if defender == None:
            defender = ctx.author.id
        defender_nation = await Database.find_user(defender)
        if defender_nation == {}:
            try:
                defender_nums = int(re.sub("[^0-9]", "", defender))
                defender_nation = list(mongo.world_nations.find({"nationid": defender_nums}).collation(
                    {"locale": "en", "strength": 1}))[0]
            except:
                try:
                    defender_nation = list(mongo.world_nations.find({"leader": defender}).collation(
                        {"locale": "en", "strength": 1}))[0]
                except:
                    try:
                        defender_nation = list(mongo.world_nations.find({"nation": defender}).collation(
                        {"locale": "en", "strength": 1}))[0]
                    except:
                        defender_nation = None
            if not defender_nation:
                if attacker == None:
                    await message.edit(content='I could not find that nation!')
                    return
                else:
                    await message.edit(content='I could not find nation 1!')
                    return 
        
        if attacker == None:
            attacker = ctx.author.id
        attacker_nation = await Database.find_user(attacker)
        if attacker_nation == {}:
            try:
                attacker_nation = list(mongo.world_nations.find({"nation": attacker}).collation(
                    {"locale": "en", "strength": 1}))[0]
            except:
                try:
                    attacker_nation = list(mongo.world_nations.find({"leader": attacker}).collation(
                        {"locale": "en", "strength": 1}))[0]
                except:
                    try:
                        attacker = int(re.sub("[^0-9]", "", attacker))
                        attacker_nation = list(mongo.world_nations.find({"nationid": attacker}).collation(
                            {"locale": "en", "strength": 1}))[0]
                    except:
                        attacker_nation = None
            if not attacker_nation:
                if attacker == None:
                    await message.edit(content='I was able to find the nation you linked, but I could not find *your* nation!')
                    return
                else:
                    await message.edit(content='I could not find nation 2!')
                    return 

        defender_nation = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{defender_nation['nationid']}){{data{{nation_name population id soldiers tanks aircraft ships}}}}}}"}).json()['data']['nations']['data'][0]
        attacker_nation = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{attacker_nation['nationid']}){{data{{nation_name population id soldiers tanks aircraft ships}}}}}}"}).json()['data']['nations']['data'][0]

        embed = discord.Embed(title="Battle Simulator",
                              description=f"These are the results for when [{attacker_nation['nation_name']}](https://politicsandwar.com/nation/id={attacker_nation['id']}) attacks [{defender_nation['nation_name']}](https://politicsandwar.com/nation/id={defender_nation['id']})\nIf you want to use custom troop counts, you can use the [in-game battle simulators](https://politicsandwar.com/tools/)", color=0x00ff00)
        embed1 = discord.Embed(title="Battle Simulator",
                              description=f"These are the results for when [{defender_nation['nation_name']}](https://politicsandwar.com/nation/id={defender_nation['id']}) attacks [{attacker_nation['nation_name']}](https://politicsandwar.com/nation/id={attacker_nation['id']})\nIf you want to use custom troop counts, you can use the [in-game battle simulators](https://politicsandwar.com/tools/)", color=0x00ff00)

        try:
            x = (attacker_nation['soldiers'] * 1.75 + attacker_nation['tanks'] * 40) / (defender_nation['soldiers'] * 1.75 + defender_nation['tanks'] * 40 + defender_nation['population'] * 0.0025)
            print(x)
            if x > 2:
                ground_win_rate = 1
            elif x < 0.4:
                ground_win_rate = 0
            else:
                ground_win_rate = (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
        except ZeroDivisionError:
            ground_win_rate = 1

        try:
            x = (defender_nation['soldiers'] * 1.75 + defender_nation['tanks'] * 40) / (attacker_nation['soldiers'] * 1.75 + attacker_nation['tanks'] * 40 + attacker_nation['population'] * 0.0025)
            print(x)
            if x > 2:
                ground_loss_rate = 1
            elif x < 0.4:
                ground_loss_rate = 0
            else:
                ground_loss_rate = (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
        except ZeroDivisionError:
            ground_loss_rate = 1

        try:
            x = (attacker_nation['aircraft'] * 3) / (defender_nation['aircraft'] * 3)
            print(x)
            if x > 2:
                air_win_rate = 1
            elif x < 0.4:
                air_win_rate = 0
            else:
                air_win_rate = (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
        except ZeroDivisionError:
            air_win_rate = 1

        try:
            x = (attacker_nation['ships'] * 4) / (defender_nation['ships'] * 4)
            print(x)
            if x > 2:
                naval_win_rate = 1
            elif x < 0.4:
                naval_win_rate = 0
            else:
                naval_win_rate = (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
        except ZeroDivisionError:
            naval_win_rate = 1

        print(ground_win_rate, ground_loss_rate, air_win_rate, naval_win_rate)

        ground_it = ground_win_rate**3
        ground_mod = ground_win_rate**2 * (1 - ground_win_rate) * 3
        ground_pyr = ground_win_rate * (1 - ground_win_rate)**2 * 3
        ground_fail = (1 - ground_win_rate)**3

        ground_opposite_it = ground_loss_rate**3
        ground_opposite_mod = ground_loss_rate**2 * (1 - ground_loss_rate) * 3
        ground_opposite_pyr = ground_loss_rate * (1 - ground_loss_rate)**2 * 3
        ground_opposite_fail = (1 - ground_loss_rate)**3

        air_it = air_win_rate**3
        air_mod = air_win_rate**2 * (1 - air_win_rate) * 3
        air_pyr = air_win_rate * (1 - air_win_rate)**2 * 3
        air_fail = (1 - air_win_rate)**3

        naval_it = naval_win_rate**3
        naval_mod = naval_win_rate**2 * (1 - naval_win_rate) * 3
        naval_pyr = naval_win_rate * (1 - naval_win_rate)**2 * 3
        naval_fail = (1 - naval_win_rate)**3

        if attacker_nation['soldiers'] + attacker_nation['tanks'] + defender_nation['soldiers'] + defender_nation['tanks'] == 0:
            embed.add_field(name="Ground Attack", value="Nobody has any forces!")
            embed1.add_field(name="Ground Attack", value="Nobody has any forces!")
        else:
            embed.add_field(name="Ground Attack", value=f"Immense Triumph: {round(ground_opposite_fail*100)}%\nModerate Success: {round(ground_opposite_pyr*100)}%\nPyrrhic Victory: {round(ground_opposite_mod*100)}%\nUtter Failure: {round(ground_opposite_it*100)}%")
            embed1.add_field(name="Ground Attack", value=f"Immense Triumph: {round(ground_fail*100)}%\nModerate Success: {round(ground_pyr*100)}%\nPyrrhic Victory: {round(ground_mod*100)}%\nUtter Failure: {round(ground_it*100)}%")
        
        if attacker_nation['aircraft'] + defender_nation['aircraft'] != 0:
            embed.add_field(name="Airstrike", value=f"Immense Triumph: {round(air_it*100)}%\nModerate Success: {round(air_mod*100)}%\nPyrrhic Victory: {round(air_pyr*100)}%\nUtter Failure: {round(air_fail*100)}%")
            embed1.add_field(name="Airstrike", value=f"Immense Triumph: {round(air_fail*100)}%\nModerate Success: {round(air_pyr*100)}%\nPyrrhic Victory: {round(air_mod*100)}%\nUtter Failure: {round(air_it*100)}%")
        else:
            embed.add_field(name="Airstrike", value="Nobody has any forces!")
            embed1.add_field(name="Airstrike", value="Nobody has any forces!")

        if attacker_nation['ships'] + defender_nation['ships'] != 0:
            embed.add_field(name="Naval Battle", value=f"Immense Triumph: {round(naval_it*100)}%\nModerate Success: {round(naval_mod*100)}%\nPyrrhic Victory: {round(naval_pyr*100)}%\nUtter Failure: {round(naval_fail*100)}%")
            embed1.add_field(name="Naval Battle", value=f"Immense Triumph: {round(naval_fail*100)}%\nModerate Success: {round(naval_pyr*100)}%\nPyrrhic Victory: {round(naval_mod*100)}%\nUtter Failure: {round(naval_it*100)}%")

        else:
            embed.add_field(name="Naval Battle", value="Nobody has any forces!")
            embed1.add_field(name="Naval Battle", value="Nobody has any forces!")
        
        await message.edit(embed=embed, content="")
        await message.add_reaction("↔️")
        cur_page = 1
                
        async def reaction_checker():
            print('reaction')
            while True:
                try:
                    nonlocal cur_page
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=600)
                    if user.id != ctx.author.id or reaction.message != message:
                        continue
                    
                    elif str(reaction.emoji) == "↔️" and cur_page == 2:
                        cur_page = 1
                        msg_embd = [embed, embed1][cur_page-1]
                        await message.edit(content="", embed=msg_embd)
                        await message.remove_reaction(reaction, ctx.author)

                    elif str(reaction.emoji) == "↔️" and cur_page == 1:
                        cur_page = 2
                        msg_embd = [embed, embed1][cur_page-1]
                        await message.edit(content="", embed=msg_embd)
                        await message.remove_reaction(reaction, ctx.author)

                    else:
                        await message.remove_reaction(reaction, ctx.author)

                except asyncio.TimeoutError:
                    await message.edit(content="**Command timed out!**")
                    print('reaction break')
                    break

        reacttask = asyncio.create_task(reaction_checker())

        await asyncio.gather(reacttask)


def setup(bot):
    bot.add_cog(Military(bot))