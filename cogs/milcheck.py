import discord
from pymongo import database
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
        self.bot.bg_task = self.bot.loop.create_task(self.wars())

    @commands.command(brief='Returns military statistics', help='Accepts an optional argument "convent"')
    @commands.has_any_role('Deacon', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def milcheck(self, ctx):
        async with aiohttp.ClientSession() as session:
            message = await ctx.send('Hang on...')
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:500 alliance_id:4729){{data{{id leader_name nation_name alliance_id color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available offensive_wars{{winner turnsleft}} defensive_wars{{winner turnsleft}} cities{{infrastructure barracks factory airforcebase drydock}}}}}}}}"}) as temp:
                nations = (await temp.json())['data']['nations']['data']
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={convent_key}", json={'query': f"{{nations(page:1 first:500 alliance_id:7531){{data{{id leader_name nation_name alliance_id color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available offensive_wars{{winner turnsleft}} defensive_wars{{winner turnsleft}} cities{{infrastructure barracks factory airforcebase drydock}}}}}}}}"}) as temp:
                nations += (await temp.json())['data']['nations']['data']

        fields2 = []
        fields3 = []
        fields4 = []
        fields5 = []

        for x in nations:
            barracks = 0
            factories = 0
            hangars = 0
            drydocks = 0
            
            for city in x['cities']:
                barracks += city['barracks']
                factories += city['factory']
                hangars += city['airforcebase']
                drydocks += city['drydock']

            max_soldiers = 3000 * barracks
            max_tanks = 250 * factories
            max_aircraft = 15 * hangars
            max_ships = 5 * drydocks
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
                    {'name': f"{x['leader_name']}", 'value': rebuy})
            

            avg_bar = (barracks / x['num_cities'])
            avg_fac = (factories / x['num_cities'])
            avg_han = (hangars / x['num_cities'])
            avg_dry = (drydocks / x['num_cities'])

            fields3.append(
                {'name': f"{x['leader_name']}", 'value': f'Average improvements:\n{round(avg_bar, 1)}/{round(avg_fac, 1)}/{round(avg_han, 1)}/{round(avg_dry, 1)}'})
            
            city_count = x['num_cities']
            fields4.append({'name': f"{x['leader_name']}", 'value': f"Warchest:\nMoney: ${round(float(x['money']) / 1000000)}M/${round(city_count * 500000 / 1000000)}M\nMunis: {round(float(x['munitions']) / 1000)}k/{round(city_count * 361.2 / 1000)}k\nGas: {round(float(x['gasoline']) / 1000)}k/{round(city_count * 320.25 / 1000)}k\nSteel: {round(float(x['steel']) / 1000)}k/{round(city_count * 619.5 / 1000)}k\n Alum: {round(float(x['aluminum']) / 1000)}k/{round(city_count * 315 / 1000)}k"})

            offensive_used_slots = 0
            for war in x['offensive_wars']:
                if war['turnsleft'] > 0:
                    offensive_used_slots += 1

            defensive_used_slots = 0
            for war in x['defensive_wars']:
                if war['turnsleft'] > 0:
                    defensive_used_slots += 1

            fields5.append(
                {'name': f"{x['leader_name']}", 'value': f"Offensive: {offensive_used_slots} wars\nDefensive: {defensive_used_slots} wars"})

        embed2 = discord.Embed(title="Militarization pt. 1",
                               description="", color=0x00ff00)
        embed3 = discord.Embed(title="Militarization pt. 2",
                               description="", color=0x00ff00)
        embed4 = discord.Embed(title="Militarization pt. 3", description="",
                               color=0x00ff00, timestamp=pytz.utc.localize(datetime.utcnow()))
        embed5 = discord.Embed(title="Militarization pt. 4", description="",
                               color=0x00ff00, timestamp=pytz.utc.localize(datetime.utcnow()))

        async def add_fields(fields, count, embed):
            for x in fields:
                if count == 24:
                    await ctx.send(embed=embed)
                    embed.clear_fields()
                    count = 0
                embed.add_field(name=x['name'], value=x['value'])
                count += 1
            if len(embed.fields) > 0:
                await ctx.send(embed=embed)

        await add_fields(fields2, 0, embed2)
        await add_fields(fields3, 0, embed3)
        await add_fields(fields4, 0, embed4)
        await add_fields(fields5, 0, embed5)
        await message.delete()

    @commands.command(brief='Delete all threads in this channel.')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def clear_threads(self, ctx):
        channel = self.bot.get_channel(796752432263725066)
        for thread in channel.threads:
            await thread.delete()
        print("done")
        return

    @commands.command(brief='May be used in military coordination threads.')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def status(self, ctx):
        nation_id = ctx.channel.name[ctx.channel.name.rfind("(")+1:-1]
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation_id}){{data{{nation_name leader_name id alliance{{name}} population score color dompolicy alliance_id num_cities soldiers tanks aircraft ships missiles nukes offensive_wars{{defender{{nation_name id score num_cities color defensive_wars{{turnsleft}} offensive_wars{{turnsleft}} soldiers tanks aircraft ships nukes missiles}} date id attid winner att_resistance def_resistance attpoints defpoints attpeace defpeace war_type groundcontrol airsuperiority navalblockade turnsleft att_fortify def_fortify}} defensive_wars{{attacker{{nation_name id score num_cities color defensive_wars{{turnsleft}} offensive_wars{{turnsleft}} soldiers tanks aircraft ships nukes missiles}} date id attid winner att_resistance def_resistance attpoints defpoints attpeace defpeace war_type groundcontrol airsuperiority navalblockade turnsleft att_fortify def_fortify}}}}}}}}"}) as temp:
                try:
                    nation = (await temp.json())['data']['nations']['data'][0]
                except:
                    print((await temp.json())['errors'])
                    return
        nation['offensive_wars'] = [y for y in nation['offensive_wars'] if y['turnsleft'] > 0]
        nation['defensive_wars'] = [y for y in nation['defensive_wars'] if y['turnsleft'] > 0]
        desc = f"[Nation link](https://politicsandwar.com/nation/id={nation['id']})```autohotkey\nOffensive wars: {len(nation['offensive_wars'])}\nDefensive wars: {len(nation['defensive_wars'])}\nSoldiers: {nation['soldiers']:,}\nTanks: {nation['tanks']:,}\nPlanes: {nation['aircraft']:,}\nShips: {nation['ships']:,}```"
        embed = discord.Embed(title=f"{nation['nation_name']} ({nation['id']}) & their wars", description=desc, color=0x00ff00)
        n = 1
        for war in nation['offensive_wars'] + nation['defensive_wars']:
            if war['turnsleft'] < 0:
                continue

            n += 1
            if n % 2 == 0:
                embed.add_field(name="\u200b", value="\u200b", inline=False)

            if war in nation['offensive_wars']:
                war_emoji = "⚔️"
                x = war['defender']
                main_enemy_res = war['att_resistance']
                main_enemy_points = war['attpoints']
                their_enemy_points = war['defpoints']
                their_enemy_res = war['def_resistance']
            else:
                war_emoji = "🛡️"
                x = war['attacker']
                main_enemy_res = war['def_resistance']
                main_enemy_points = war['defpoints']
                their_enemy_points = war['attpoints']
                their_enemy_res = war['att_resistance']

            x['offensive_wars'] = [y for y in x['offensive_wars'] if y['turnsleft'] > 0]
            x['defensive_wars'] = [y for y in x['defensive_wars'] if y['turnsleft'] > 0]

            if war['groundcontrol'] in [nation['id'], x['id']]:
                war['groundcontrol'] = [nation['nation_name'], x['nation_name']][[nation['id'], x['id']].index(war['groundcontrol'])]
            else:
                war['groundcontrol'] = None

            x_air_mod = 1
            nation_air_mod = 1
            if war['airsuperiority'] == nation['id']:
                war['airsuperiority'] = nation['nation_name']
                x_air_mod = 0.5
            elif war['airsuperiority'] == x['id']:
                war['airsuperiority'] = x['nation_name']
                nation_air_mod = 0.5
            else:
                war['airsuperiority'] = None

            if war['navalblockade'] in [nation['id'], x['id']]:
                war['navalblockade'] = [x['nation_name'], nation['nation_name']][[nation['id'], x['id']].index(war['navalblockade'])]
            else:
                war['navalblockade'] = None

            try:
                y = (x['soldiers'] * 1.75 + x['tanks'] * 40 * x_air_mod) / (nation['soldiers'] * 1.75 + nation['tanks'] * 40 * nation_air_mod + nation['population'] * 0.0025)
                if y > 2:
                    ground_win_rate = 1
                elif y < 0.4:
                    ground_win_rate = 0
                else:
                    ground_win_rate = (12.832883444301027*y**(11)-171.668262561212487*y**(10)+1018.533858483560834*y**(9)-3529.694284997589875*y**(8)+7918.373606722701879*y**(7)-12042.696852729619422*y**(6)+12637.399722721022044*y**(5)-9128.535790660698694*y**(4)+4437.651655224382012*y**(3)-1378.156072477675025*y**(2)+245.439740545813436*y-18.980551645186498)
            except ZeroDivisionError:
                ground_win_rate = 1
            ground_win_rate = round(ground_win_rate * 100)

            try:
                y = (x['aircraft'] * 3) / (nation['aircraft'] * 3)
                if y > 2:
                    air_win_rate = 1
                elif y < 0.4:
                    air_win_rate = 0
                else:
                    air_win_rate = (12.832883444301027*y**(11)-171.668262561212487*y**(10)+1018.533858483560834*y**(9)-3529.694284997589875*y**(8)+7918.373606722701879*y**(7)-12042.696852729619422*y**(6)+12637.399722721022044*y**(5)-9128.535790660698694*y**(4)+4437.651655224382012*y**(3)-1378.156072477675025*y**(2)+245.439740545813436*y-18.980551645186498)
            except ZeroDivisionError:
                air_win_rate = 1
            air_win_rate = round(air_win_rate * 100)

            try:
                y = (x['ships'] * 4) / (nation['ships'] * 4)
                if y > 2:
                    naval_win_rate = 1
                elif y < 0.4:
                    naval_win_rate = 0
                else:
                    naval_win_rate = (12.832883444301027*y**(11)-171.668262561212487*y**(10)+1018.533858483560834*y**(9)-3529.694284997589875*y**(8)+7918.373606722701879*y**(7)-12042.696852729619422*y**(6)+12637.399722721022044*y**(5)-9128.535790660698694*y**(4)+4437.651655224382012*y**(3)-1378.156072477675025*y**(2)+245.439740545813436*y-18.980551645186498)
            except ZeroDivisionError:
                naval_win_rate = 1
            naval_win_rate = round(naval_win_rate * 100)

            embed.add_field(name=f"\{war_emoji} {x['nation_name']} ({x['id']})", value=f"[Nation link](https://politicsandwar.com/nation/id={x['id']}) | [War timeline](https://politicsandwar.com/nation/war/timeline/war={war['id']})```autohotkey\nOffensive wars: {len(x['offensive_wars'])}\nDefensive wars: {len(x['defensive_wars'])}\n\nGround control: \"{war['groundcontrol']}\"\nAir superiority: \"{war['airsuperiority']}\"\nBlockaded: \"{war['navalblockade']}\"\n{nation['nation_name'][:5]}. resistance: {main_enemy_res}\n{x['nation_name'][:5]}. resistance: {their_enemy_res}\n{nation['nation_name'][:5]}. MAPs: {main_enemy_points}\n{x['nation_name'][:5]}. MAPs: {their_enemy_points}\nExpiration (hours): {war['turnsleft']*2}\n\nSoldiers: {x['soldiers']:,}\nTanks: {x['tanks']:,}\nPlanes: {x['aircraft']:,}\nShips: {x['ships']:,}\n\nGround win%: {ground_win_rate}\nAir win%: {air_win_rate}\nNaval win%: {naval_win_rate}```", inline=True)
        await ctx.send(embed=embed)

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def war_scanner(self, ctx):
        await self.wars()

    async def add_to_thread(self, thread, atom):
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(atom)
        if person == {}:
            print("could not find", atom)
            return
        user = await self.bot.fetch_user(person['user'])
        await thread.add_user(user)

    async def wars(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(796752432263725066)
        guild = self.bot.get_guild(434071714893398016)
        prev_wars = None

        async def cthread(name, embed, non_atom, atom, new_war):
            found = False
            for thread in guild.threads:
                if f"({non_atom['id']})" in thread.name:
                    found = True
                    matching_thread = thread
                    break
            print(new_war, found)
            if not found:
                message = await channel.send(embed=embed)
                try:
                    thread = await channel.create_thread(name=name, message=message, auto_archive_duration=4320, type=discord.ChannelType.private_thread, reason="War declaration")
                except:
                    thread = await channel.create_thread(name=name, message=message, auto_archive_duration=1440, type=discord.ChannelType.private_thread, reason="War declaration")
                await self.add_to_thread(thread, atom['id'])
            elif new_war and found:
                await matching_thread.send(embed=embed)
                await self.add_to_thread(matching_thread, atom['id'])

        async def attack_check(attack, new_war):
            if attack['type'] in ["MISSILEFAIL", "MISSILE", "NUKE", "NUKEFAIL"]:
                if {"id": attack['cityid']} in new_war['attacker']['cities']:
                    attacker = new_war['defender']['id']
                else:
                    attacker = new_war['attacker']['id']
            elif attack['type'] == "FORTIFY":
                attacker = None
            elif attack['success'] > 0:
                attacker = attack['victor']
                #print(attack)
                #print(new_war)
                #print(old_war)
            else:
                #print([new_war['attacker']['id'], new_war['defender']['id']], attack['victor'], attack)
                attacker = [new_war['attacker']['id'], new_war['defender']['id']]
                print([new_war['attacker']['id'], new_war['defender']['id']])
                attacker.remove(attack['victor'])
                attacker = attacker[0]
                #print(attacker)
            return attacker

        async def smsg(attacker_id, attack, war, atom, non_atom, peace):
            embed = discord.Embed(title=f"New {war['war_type'].lower().capitalize()} War", description=f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) declared a{'n'[:(len(war['war_type'])-5)^1]} {war['war_type'].lower()} war on [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']})", color=0x00ff00)
            await cthread(f"{non_atom['nation_name']} ({non_atom['id']})", embed, non_atom, atom, False)
            
            for thread in guild.threads:
                if f"({non_atom['id']})" in thread.name:
                    #print("match")
                    if peace != None:
                        embed = discord.Embed(title="Peace offering", description=f"[{peace['offerer']['nation_name']}](https://politicsandwar.com/nation/id={peace['offerer']['id']}) is offering peace to [{peace['reciver']['nation_name']}](https://politicsandwar.com/nation/id={peace['reciever']['id']}). The peace offering will be canceled if either side performs an act of aggression.", color=0xfff)
                        await thread.send(embed=embed)
                        break
                    if attack['type'] != "FORTIFY":
                        if attack['type'] in ["GROUND", "NAVAL", "AIRVINFRA", "AIRVSOLDIERS", "AIRVTANKS", "AIRVMONEY", "AIRVSHIPS", "AIRVAIR"]:
                            for nation in [war['attacker'], war['defender']]:
                                if nation['id'] == attacker_id:
                                    attacker_nation = nation
                                elif nation['id'] != attacker_id:
                                    defender_nation = nation

                            colors = [0xff0000, 0xffff00, 0xffff00, 0x00ff00]
                            #print(war['attacker'], war['defender'], attacker_id)
                            if attacker_nation['id'] == non_atom['id']:
                                colors.reverse()
                            #print(colors)
                            #print(attack['success'])

                            if attack['success'] == 3:
                                success = "Immense Triumph"
                            elif attack['success'] == 2:
                                success = "Moderate Success"
                            elif attack['success'] == 1:
                                success = "Pyrrhic Victory"
                            elif attack['success'] == 0:
                                success = "Utter Failure"

                            description = f"[War timeline](https://politicsandwar.com/nation/war/timeline/war={war['id']})\nSuccess: {success}"

                            if attack['type'] == "GROUND":
                                title = "Ground battle"
                                att_casualties = f"{attack['attcas1']:,} soldiers\n{attack['attcas2']:,} tanks"
                                def_casualties = f"{attack['defcas1']:,} soldiers\n{attack['defcas2']:,} tanks\n{attack['infradestroyed']} infra (${attack['infra_destroyed_value']:,})\n${attack['moneystolen']:,} money"
                            elif attack['type'] == "NAVAL":
                                title = "Naval Battle"
                                att_casualties = f"{attack['attcas1']:,} ships"
                                def_casualties = f"{attack['defcas1']:,} ships\n{attack['infradestroyed']} infra (${attack['infra_destroyed_value']:,})"
                            elif attack['type'] == "AIRVINFRA":
                                title = "Airstrike targeting infrastructure"
                                att_casualties = f"{attack['attcas1']:,} planes"
                                def_casualties = f"{attack['defcas1']:,} planes\n{attack['infradestroyed']} infra (${attack['infra_destroyed_value']:,})"
                            elif attack['type'] == "AIRVSOLDIERS":
                                title = "Airstrike targeting soldiers"
                                att_casualties = f"{attack['attcas1']:,} planes"
                                def_casualties = f"{attack['defcas1']:,} planes\n{attack['defcas2']} soldiers"
                            elif attack['type'] == "AIRVTANKS":
                                title = "Airstrike targeting tanks"
                                att_casualties = f"{attack['attcas1']:,} planes"
                                def_casualties = f"{attack['defcas1']:,} planes\n{attack['defcas2']} tanks"
                            elif attack['type'] == "AIRVMONEY":
                                title = "Airstrike targeting money"
                                att_casualties = f"{attack['attcas1']:,} planes"
                                def_casualties = f"{attack['defcas1']:,} planes\n{attack['defcas2']} money"
                            elif attack['type'] == "AIRVSHIPS":
                                title = "Airstrike targeting ships"
                                att_casualties = f"{attack['attcas1']:,} planes"
                                def_casualties = f"{attack['defcas1']:,} planes\n{attack['defcas2']} ships"
                            elif attack['type'] == "AIRVAIR":
                                title = "Airstrike targeting aircraft"
                                att_casualties = f"{attack['attcas1']:,} planes"
                                def_casualties = f"{attack['defcas1']:,} planes"
                            try:
                                aaa_link = f"[{attacker_nation['alliance']['name']}](https://politicsandwar.com/alliance/id={attacker_nation['alliance_id']})"
                            except:
                                aaa_link = "No alliance"
                            try:
                                daa_link = f"[{defender_nation['alliance']['name']}](https://politicsandwar.com/alliance/id={defender_nation['alliance_id']})"
                            except:
                                daa_link = "No alliance"

                            embed = discord.Embed(title=title, description=description, color=colors[attack['success']])
                            embed.add_field(name=f"Attacker", value=f"[{attacker_nation['nation_name']}](https://politicsandwar.com/nation/id={attacker_nation['id']})\n{aaa_link}\n\n**Casualties**: ```{att_casualties}```")
                            embed.add_field(name=f"Defender", value=f"[{defender_nation['nation_name']}](https://politicsandwar.com/nation/id={defender_nation['id']})\n{daa_link}\n\n**Casualties**: ```{def_casualties}```")
                            await thread.send(embed=embed)
                            break
                        elif attack['type'] in ["PEACE", "VICTORY", "ALLIANCELOOT"]:
                            if attack['type'] == "PEACE":
                                title = "Peace"
                                content = f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) & [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']}) peaced out???"
                            elif attack['type'] == "VICTORY":
                                title = "Victory"
                                content = f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) & [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']}) won???"
                            elif attack['type'] == "ALLIANCELOOT":
                                title = "Alliance loot"
                                content = f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) & [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']}) looted someone???"
                            embed = discord.Embed(title=title, description=content, color=0xfff)
                            await thread.send(embed=embed)
                            break
                        else:
                            for nation in [war['attacker'], war['defender']]:
                                if nation['id'] == attacker_id:
                                    attacker_nation = nation
                                elif nation['id'] != attacker_id:
                                    defender_nation = nation

                            colors = [0xff0000, 0x00ff00]
                            if attacker_nation['id'] == non_atom['id']:
                                colors.reverse()

                            if attack['type'] == "MISSILE":
                                title = "Missile"
                                content = f"[{attacker_nation['nation_name']}](https://politicsandwar.com/nation/id={attacker_nation['id']}) launched a missile upon [{defender_nation['nation_name']}](https://politicsandwar.com/nation/id={defender_nation['id']}), destroying {attack['infradestroyed']} infra (${attack['infra_destroyed_value']:,}) and {attack['improvementslost']} improvement{'s'[:attack['improvementslost']^1]}."
                            elif attack ['type'] == "MISSILEFAIL":
                                title = "Failed missile"
                                content = f"[{attacker_nation['nation_name']}](https://politicsandwar.com/nation/id={attacker_nation['id']}) launched a missile upon [{defender_nation['nation_name']}](https://politicsandwar.com/nation/id={defender_nation['id']}), but the missile was shot down."
                            elif attack['type'] == "NUKE":
                                title = "Nuke"
                                content = f"[{attacker_nation['nation_name']}](https://politicsandwar.com/nation/id={attacker_nation['id']}) launched a nuclear weapon upon [{defender_nation['nation_name']}](https://politicsandwar.com/nation/id={defender_nation['id']}), destroying {attack['infradestroyed']} infra (${attack['infra_destroyed_value']:,}) and {attack['improvementslost']} improvement{'s'[:attack['improvementslost']^1]}."
                            elif attack['type'] == "NUKEFAIL":
                                title = "Failed nuke"
                                content = f"[{attacker_nation['nation_name']}](https://politicsandwar.com/nation/id={attacker_nation['id']}) launched a nuclear weapon upon [{defender_nation['nation_name']}](https://politicsandwar.com/nation/id={defender_nation['id']}), but the nuke was shot down."
                        
                            #print(attack['type'])
                            embed = discord.Embed(title=title, description=content, color=colors[attack['success']])
                            await thread.send(embed=embed)
                            break
                    else:
                        if war['att_fortify'] and war['def_fortify']:
                            content = f"{war['attacker']['nation_name']} and {war['defender']['nation_name']} are now fortified."
                            color = 0xffff00
                        elif war['att_fortify']:
                            content = f"{war['attacker']['nation_name']} is now fortified."
                            if war['attacker'] == atom:
                                color = 0x00ff00
                            else:
                                color = 0xff0000
                        elif war['def_fortify']:
                            content = f"{war['defender']['nation_name']} is now fortified."
                            if war['defender'] == atom:
                                color = 0x00ff00
                            else:
                                color = 0xff0000
                        else:
                            content = f"{war['attacker']['nation_name']} or {war['defender']['nation_name']} fortified (idk who due to api limitations), then subsequently attacked, losing the fortified effect."
                            color = 0xffffff
                        #print(war)
                        embed = discord.Embed(title=f"Fortification", description=content, color=color)
                        await thread.send(embed=embed)
                        break

        while True:
            #print("check", datetime.utcnow())
            async with aiohttp.ClientSession() as session:
                async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] days_ago:5){{id att_fortify war_type def_fortify turnsleft attacker{{nation_name alliance{{name}} id num_cities alliance_id cities{{id}}}} defender{{nation_name alliance{{name}} id num_cities alliance_id cities{{id}}}} attacks{{type victor moneystolen success cityid resistance_eliminated infradestroyed infra_destroyed_value improvementslost attcas1 attcas2 defcas1 defcas2}}}}}}"}) as temp:
                    try:
                        wars = (await temp.json())['data']['wars']
                    except:
                        print((await temp.json())['errors'])
                        await asyncio.sleep(60)
                        continue
                    if prev_wars == None:
                        prev_wars = wars
                        print("previous is none")
                        #await asyncio.sleep(60)
                        continue
                #n = 0
                for new_war in wars:
                    #n += 1
                    #if n < 150:
                    #    continue
                    #print(n)
                    if new_war['attacker']['alliance_id'] in ['4729', '7531']: ## CHANGE T0 ATOM ---------------------------------------------------------
                        atom = new_war['attacker']
                        non_atom = new_war['defender']
                    else:
                        atom = new_war['defender']
                        non_atom = new_war['attacker']
                    if non_atom['num_cities'] < 10:
                        channel = self.bot.get_channel(837985478648660018)
                    elif 20 > non_atom['num_cities'] >= 10:
                        channel = self.bot.get_channel(837985611763810324)
                    elif 30 > non_atom['num_cities'] >= 20:
                        channel = self.bot.get_channel(837985741454966832)
                    elif non_atom['num_cities'] >= 30:
                        channel = self.bot.get_channel(837985858568060938)
                    found_war = False
                    for old_war in prev_wars:
                        if new_war['id'] == old_war['id']:
                            if new_war['attpeace'] and not old_war['attpeace']:
                                peace_obj = {"offerer": new_war['attacker'], "reciever": new_war['defender']}
                                await smsg(None, None, new_war, atom, non_atom, peace_obj)
                            elif new_war['defpeace'] and not old_war['defpeace']:
                                peace_obj = {"offerer": new_war['defender'], "reciever": new_war['attacker']}
                                await smsg(None, None, new_war, atom, non_atom, peace_obj)
                            found_war = True
                            if len(new_war['attacks']) == 0:
                                break
                            attack = None
                            for attack in new_war['attacks']:
                                if attack not in old_war['attacks']:
                                    attacker = await attack_check(attack, new_war)
                                    await smsg(attacker, attack, new_war, atom, non_atom, None)
                            break
                    if not found_war:
                        print("war not found")
                        embed = discord.Embed(title=f"New {new_war['war_type'].lower().capitalize()} War", description=f"[{new_war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={new_war['attacker']['id']}) declared a{'n'[:(len(new_war['war_type'])-5)^1]} {new_war['war_type'].lower()} war on [{new_war['defender']['nation_name']}](https://politicsandwar.com/nation/id={new_war['defender']['id']})", color=0x00ff00)
                        await cthread(f"{non_atom['nation_name']} ({non_atom['id']})", embed, non_atom, atom, True)
                        for attack in new_war['attacks']:
                            attacker = await attack_check(attack, new_war)
                            await smsg(attacker, attack, new_war, atom, non_atom, None)
            prev_wars = wars
            await asyncio.sleep(60)
   
    @commands.command(brief='Add someone to the military coordination thread.')
    @commands.has_any_role('Deacon', 'Advisor', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def add(self, ctx, *, user):
        await self.add_to_thread(ctx.channel, user)

    @commands.command(brief='Reomve someone from the military coordination thread.')
    @commands.has_any_role('Deacon', 'Advisor', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def remove(self, ctx, *, user):
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(user)
        user = await self.bot.fetch_user(person['user'])
        await ctx.channel.remove_user(user)

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
        #await ctx.send('This command has been disabled.')
        #return
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(ctx.author.id)
        embed = discord.Embed(title="Targets",
                              description=f"[Explore targets on slotter](https://slotter.bsnk.dev/search?nation={person['nationid']}&alliances=7452,8841,8624,9000,7450,6088,7306,4648,9187,8335,5476,8594&countersMode=false&threatsMode=false&vm=false&grey=true&beige=false)", color=0x00ff00)
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
                try:
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
                        await ctx.send(f"{user} does not allow my DMs")
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
                except Exception as e:
                    print(e)
                    await ctx.send(e)
                    
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
        #return
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
                    background-color: #383838;
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

                p {
                    font-family: sans-serif;
                    font-size: small;
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
        </head>
        <body>
            <div style="overflow-x:auto;">
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

                            <td>${f"{nation['soldiers']:,}"}</td>
                            <td>${f"{nation['tanks']:,}"}</td>
                            <td>${nation['aircraft']}</td>
                            <td>${nation['ships']}</td>
                            <td>${nation['missiles']}</td>
                            <td>${nation['nukes']}</td>
                            <td>${nation['winchance']}</td>
                            <td>${nation['def_slots']}/3</td>
                            <td style="text-align:right">${f"{nation['monetary_net_num']:,}"}</td>
                            <td style="text-align:right">${f"{nation['net_cash_num']:,}"}</td>
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
                    </tbody>
                </table>
                <p>Last updated: ${datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC<br><a href="http://www.timezoneconverter.com/cgi-bin/tzc.tzc" target="_blank">Timezone converter</a></p>
                <p style="color:gray">Please report bugs to RandomNoobster#0093<br>Courtesy of Church of Atom</p>
                <script>
                    const getCellValue = (tr, idx) => tr.children[idx].innerText.replace(/,/g, '') || tr.children[idx].textContent.replace(/,/g, '');

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
            futures = []
            tot_pages = 0
            app_pages = 1
            any_pages = 1
            progress = 0
            
            async def call_api(url, json):
                nonlocal progress
                await message.edit(content=f"Getting targets... ({progress}/{tot_pages})")
                async with session.post(url, json=json) as temp:
                    resp = await temp.json()
                    print("future recieved")
                    progress += 1
                    await message.edit(content=f"Getting targets... ({progress}/{tot_pages})")
                    return resp
            
            await message.clear_reactions()
            await message.edit(content="Getting targets...", embed=None)
            waiting_gif = await ctx.send(file=gif)

            #start_time = time.time()

            if applicants == True:
                async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:300 min_score:{minscore} max_score:{maxscore} vmode:false alliance_position:1){{paginatorInfo{{lastPage}}}}}}"}) as temp:
                    tot_pages += (await temp.json())['data']['nations']['paginatorInfo']['lastPage']
                    app_pages += (await temp.json())['data']['nations']['paginatorInfo']['lastPage']

            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:300 min_score:{minscore} max_score:{maxscore} vmode:false{who}){{paginatorInfo{{lastPage}}}}}}"}) as temp1:
                tot_pages += (await temp1.json())['data']['nations']['paginatorInfo']['lastPage']
                any_pages += (await temp1.json())['data']['nations']['paginatorInfo']['lastPage']

            if applicants == True:
                for n in range(1, app_pages):
                    #print(n)
                    url = f"https://api.politicsandwar.com/graphql?api_key={api_key}"
                    json = {'query': f"{{nations(page:{n} first:300 min_score:{minscore} max_score:{maxscore} vmode:false alliance_position:1){{data{{id flag nation_name last_active leader_name continent dompolicy population alliance_id beigeturns score color soldiers tanks aircraft ships missiles nukes alliance{{name id}} offensive_wars{{winner}} defensive_wars{{date winner turnsleft attacks{{loot_info victor moneystolen}}}} alliance_position num_cities ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}
                    futures.append(asyncio.ensure_future(call_api(url, json)))
                    await asyncio.sleep(0.2)
            
            for n in range(1, any_pages):
                #print(n)
                url = f"https://api.politicsandwar.com/graphql?api_key={api_key}"
                json = {'query': f"{{nations(page:{n} first:300 min_score:{minscore} max_score:{maxscore} vmode:false{who}){{data{{id flag nation_name last_active leader_name continent dompolicy population alliance_id beigeturns score color soldiers tanks aircraft ships missiles nukes alliance{{name id}} offensive_wars{{winner}} defensive_wars{{date winner turnsleft attacks{{loot_info victor moneystolen}}}} alliance_position num_cities ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}
                futures.append(asyncio.ensure_future(call_api(url, json)))
                await asyncio.sleep(0.2)

            #print("--- %s seconds ---" % (time.time() - start_time))
            done_jobs = await asyncio.gather(*futures)
            #print("--- %s seconds ---" % (time.time() - start_time))

            await message.edit(content="Caching targets...")
            for done_job in done_jobs:
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
                    if x['alliance_id'] in ["4729", "7531"]:
                        continue
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
                        pass
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
                        target['nation_loot'] = f"{round(nation_loot):,}"
                        target['aa_loot'] = f"{round(aa_loot):,}"
                        target['same_aa'] = same_aa
                        embed.add_field(name="Previous nation loot", value=f"${round(nation_loot):,}")

                        if same_aa or target['aa_loot'] == 0:
                            embed.add_field(name="Previous aa loot", value=f"${round(aa_loot):,}")
                        else:
                            embed.add_field(name="Previous aa loot", value=f"${round(aa_loot):,}\nNOTE: Different aa!")

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
                embed.add_field(name="Monetary Net Income", value=rev_obj['mon_net_txt'])
                
                target['net_cash_num'] = rev_obj['net_cash_num']
                embed.add_field(name="Net Cash Income", value=rev_obj['money_txt'])

                target['max_infra'] = rev_obj['max_infra']
                target['avg_infra'] = rev_obj['avg_infra']
                embed.add_field(name="Infra", value=f"Max: {rev_obj['max_infra']}\nAvg: {rev_obj['avg_infra']}")

                try:
                    x = (target['soldiers'] * 1.75 + target['tanks'] * 40) / (atck_ntn['soldiers'] * 1.75 + atck_ntn['tanks'] * 40 + atck_ntn['population'] * 0.0025)
                    if x > 2:
                        ground_win_rate = 0
                    elif x < 0.4:
                        ground_win_rate = 1
                    else:
                        ground_win_rate = 1 - (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
                except ZeroDivisionError:
                    ground_win_rate = 0
                target['groundwin'] = ground_win_rate
                embed.add_field(name="Chance to win ground rolls", value=str(round(100*ground_win_rate)) + "%")

                try:
                    x = (atck_ntn['aircraft'] * 3) / (target['aircraft'] * 3)
                    if x > 2:
                        air_win_rate = 1
                    elif x < 0.4:
                        air_win_rate = 0
                    else:
                        air_win_rate = 1 - (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
                except ZeroDivisionError:
                    air_win_rate = 1
                target['airwin'] = air_win_rate
                embed.add_field(name="Chance to win air rolls", value=str(round(100*air_win_rate)) + "%")

                try:
                    x = (atck_ntn['ships'] * 4) / (target['ships'] * 4)
                    if x > 2:
                        naval_win_rate = 1
                    elif x < 0.4:
                        naval_win_rate = 0
                    else:
                        naval_win_rate = 1 - (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
                except ZeroDivisionError:
                    naval_win_rate = 1
                target['navalwin'] = naval_win_rate
                embed.add_field(name="Chance to win naval rolls", value=str(round(100*naval_win_rate)) + "%")

                target['winchance'] = round((ground_win_rate+air_win_rate+naval_win_rate)*100/3)

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
        #check is any wars are active, and if they have air superiority, ground control, fortified etc
        message = await ctx.send('Alright, give me a sec to calculate the winrates...')
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

        casualties = {}
        attacker_army_value = attacker_nation['soldiers'] * 1.75 + attacker_nation['tanks'] * 40
        defender_army_value = defender_nation['soldiers'] * 1.75 + defender_nation['tanks'] * 40 + defender_nation['population'] * 0.0025

        try:
            x = attacker_army_value / defender_army_value
            print(x)
            if x > 2:
                ground_win_rate = 1
            elif x < 0.4:
                ground_win_rate = 0
            else:
                ground_win_rate = (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
        except ZeroDivisionError:
            ground_win_rate = 1

        winning = "loss"
        losing = "win"
        if attacker_army_value > defender_army_value:
            winning = "win"
            losing = "loss"
        
        for party in ["attacker", "defender"]:
            for variant in [{"type": "avg", "rate": 0.7}, {"type": "diff", "rate": 0.3}]:
                for fighter in [{"fighter": "soldiers", "win_cas_rate": 125, "loss_cas_rate": 125}, {"fighter": "tanks", "win_cas_rate": 1650, "loss_cas_rate": 1550}]:
                    if party == "attacker":
                        casualties[f"ground_{party}_{variant['type']}_{fighter['fighter']}"] = round(defender_army_value * variant['rate'] / fighter[f"{winning}_cas_rate"] * 3)
                    elif party == "defender":
                        casualties[f"ground_{party}_{variant['type']}_{fighter['fighter']}"] = round(attacker_army_value * variant['rate'] / fighter[f"{losing}_cas_rate"] * 3)

        attacker_army_value = attacker_nation['soldiers'] * 1.75 + attacker_nation['tanks'] * 40 + attacker_nation['population'] * 0.0025
        defender_army_value = defender_nation['soldiers'] * 1.75 + defender_nation['tanks'] * 40

        try:
            x = defender_army_value / attacker_army_value
            print(x)
            if x > 2:
                ground_loss_rate = 1
            elif x < 0.4:
                ground_loss_rate = 0
            else:
                ground_loss_rate = (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
        except ZeroDivisionError:
            ground_loss_rate = 1

        winning = "loss"
        losing = "win"
        if attacker_army_value > defender_army_value:
            winning = "win"
            losing = "loss"

        for party in ["attacker", "defender"]:
            for variant in [{"type": "avg", "rate": 0.7}, {"type": "diff", "rate": 0.3}]:
                for fighter in [{"fighter": "soldiers", "win_cas_rate": 125, "loss_cas_rate": 125}, {"fighter": "tanks", "win_cas_rate": 1650, "loss_cas_rate": 1550}]:
                    if party == "attacker":
                        casualties[f"ground_opposite_{party}_{variant['type']}_{fighter['fighter']}"] = round(attacker_army_value * variant['rate'] / fighter[f"{winning}_cas_rate"] * 3)
                    elif party == "defender":
                        casualties[f"ground_opposite_{party}_{variant['type']}_{fighter['fighter']}"] = round(defender_army_value * variant['rate'] / fighter[f"{losing}_cas_rate"] * 3)

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

        airtoair_attacker_avg = round(defender_nation['aircraft'] * 3 * 0.7 * 0.01 * 3)
        airtoair_attacker_diff = round(defender_nation['aircraft'] * 3 * 0.3 * 0.01 * 3)
        airtoair_defender_avg = round(attacker_nation['aircraft'] * 3 * 0.7 * 0.018337 * 3)
        airtoair_defender_diff = round(attacker_nation['aircraft'] * 3 * 0.3 * 0.018337 * 3)

        airtoground_attacker_avg = round(defender_nation['aircraft'] * 3 * 0.7 * 0.015385 * 3)
        airtoground_attacker_diff = round(defender_nation['aircraft'] * 3 * 0.3 * 0.015385 * 3)
        airtoground_defender_avg = round(attacker_nation['aircraft'] * 3 * 0.7 * 0.009091 * 3)
        airtoground_defender_diff = round(attacker_nation['aircraft'] * 3 * 0.3 * 0.009091 * 3)
        
        try:
            x = (attacker_nation['ships'] * 4) / (defender_nation['ships'] * 4)
            if x > 2:
                naval_win_rate = 1
            elif x < 0.4:
                naval_win_rate = 0
            else:
                naval_win_rate = (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
        except ZeroDivisionError:
            naval_win_rate = 1

        naval_attacker_avg = round(defender_nation['ships'] * 4 * 0.7 * 0.01375 * 3)
        naval_attacker_diff = round(defender_nation['ships'] * 4 * 0.3 * 0.01375 * 3)
        naval_defender_avg = round(attacker_nation['ships'] * 4 * 0.7 * 0.01375 * 3)
        naval_defender_diff = round(attacker_nation['ships'] * 4 * 0.3 * 0.01375 * 3)


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

        embed.add_field(name="Casualties", value=f"Att. Sol.: {casualties['ground_attacker_avg_soldiers']:,} ± {casualties['ground_attacker_diff_soldiers']:,}\nAtt. Tnk.: {casualties['ground_attacker_avg_tanks']:,} ± {casualties['ground_attacker_diff_tanks']:,}\nDef. Sol.: {casualties['ground_defender_avg_soldiers']:,} ± {casualties['ground_defender_diff_soldiers']:,}\nDef. Tnk.: {casualties['ground_defender_avg_tanks']:,} ± {casualties['ground_defender_diff_tanks']:,}")        
        embed1.add_field(name="Casualties", value=f"Att. Sol.: {casualties['ground_opposite_attacker_avg_soldiers']:,} ± {casualties['ground_opposite_attacker_diff_soldiers']:,}\nAtt. Tnk.: {casualties['ground_opposite_attacker_avg_tanks']:,} ± {casualties['ground_opposite_attacker_diff_tanks']:,}\nDef. Sol.: {casualties['ground_opposite_defender_avg_soldiers']:,} ± {casualties['ground_opposite_defender_diff_soldiers']:,}\nDef. Tnk.: {casualties['ground_opposite_defender_avg_tanks']:,} ± {casualties['ground_opposite_defender_diff_tanks']:,}")        
        
        embed.add_field(name="Casualties", value=f"*Targeting air:*\nAtt. Plane: {airtoair_attacker_avg:,} ± {airtoair_attacker_diff:,}\nDef. Plane: {airtoair_defender_avg:,} ± {airtoair_defender_diff:,}\n*Targeting other:*\nAtt Plane: {airtoground_attacker_avg:,} ± {airtoground_attacker_diff:,}\nDef. Plane: {airtoground_defender_avg:,} ± {airtoground_defender_diff:,}")        
        embed1.add_field(name="Casualties", value=f"*Targeting air:*\nAtt. Plane: {round(airtoair_defender_avg / 0.018337 * 0.01):,} ± {round(airtoair_defender_diff / 0.018337 * 0.01):,}\nDef. Plane: {round(airtoair_attacker_avg * 0.018337 / 0.01):,} ± {round(airtoair_attacker_diff * 0.018337 / 0.01):,}\n*Targeting other:*\nAtt. Plane: {round(airtoground_defender_avg / 0.009091 * 0.015385):,} ± {round(airtoground_defender_diff / 0.009091 * 0.015385):,}\nDef. Plane: {airtoground_attacker_avg * 0.009091 / 0.015385:,} ± {round(airtoground_attacker_diff * 0.009091 / 0.015385):,}")        

        embed.add_field(name="Casualties", value=f"Att. Ships: {naval_attacker_avg:,} ± {naval_attacker_diff:,}\nDef. Ships: {naval_defender_avg:,} ± {naval_defender_diff:,}")        
        embed1.add_field(name="Casualties", value=f"Att. Ships: {naval_defender_avg:,} ± {naval_defender_diff:,}\nDef. Ships: {naval_attacker_avg:,} ± {naval_attacker_diff:,}")        

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