import discord
import requests
import pytz
import math
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
import asyncio
from utils import revenue_calc, pre_revenue_calc
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
        for thread in ctx.channel.threads:
            await thread.delete()
        print("done")
        return

    @commands.command(brief='May be used in military coordination threads.', aliases=['s'])
    @commands.has_any_role('Pupil', 'Zealot', 'Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def status(self, ctx, arg=None):
        with open ('./data/attachments/marching.gif', 'rb') as gif:
            gif = discord.File(gif)
        message = await ctx.send(content="*Thinking...*", file=gif)
        Database = self.bot.get_cog('Database')
        if not arg:
            if isinstance(ctx.channel, discord.Thread) and "(" in ctx.channel.name and ")" in ctx.channel.name:
                nation_id = ctx.channel.name[ctx.channel.name.rfind("(")+1:-1]
                int(nation_id) # throw an error if not a number
            else:
                try:
                    person = await Database.find_user(ctx.author.id)
                    nation_id = person['nationid']
                except:
                    await ctx.send("I do not know who to find the status of.")
                    return
        else:
            person = await Database.find_nation_plus(arg)
            nation_id = str(person['nationid'])

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation_id}){{data{{nation_name leader_name id alliance{{name}} cities{{barracks factory airforcebase drydock}} population score last_active beigeturns vmode pirate_economy color dompolicy alliance_id num_cities soldiers tanks aircraft ships missiles nukes offensive_wars{{defender{{nation_name leader_name alliance_id alliance{{name}} cities{{barracks factory airforcebase drydock}} id pirate_economy score last_active beigeturns vmode num_cities color defensive_wars{{turnsleft}} offensive_wars{{turnsleft}} soldiers tanks aircraft ships nukes missiles}} date id attid winner att_resistance def_resistance attpoints defpoints attpeace defpeace war_type groundcontrol airsuperiority navalblockade turnsleft att_fortify def_fortify}} defensive_wars{{attacker{{nation_name leader_name alliance_id alliance{{name}} id cities{{barracks factory airforcebase drydock}} pirate_economy score last_active beigeturns vmode num_cities color defensive_wars{{turnsleft}} offensive_wars{{turnsleft}} soldiers tanks aircraft ships nukes missiles}} date id attid winner att_resistance def_resistance attpoints defpoints attpeace defpeace war_type groundcontrol airsuperiority navalblockade turnsleft att_fortify def_fortify}}}}}}}}"}) as temp:
                try:
                    nation = (await temp.json())['data']['nations']['data'][0]
                    #pretty_response = json.dumps(nation, indent=4)
                    #print(pretty_response)
                except:
                    print((await temp.json())['errors'])
                    return

        if nation['pirate_economy']:
            max_offense = 6
        else:
            max_offense = 5
        
        if nation['beigeturns'] > 0:
            beige = f"\nBeige (turns): {nation['beigeturns']}"
        else:
            beige = ""

        max_sol = 0
        max_tnk = 0
        max_pln = 0
        max_shp = 0
        for c in nation['cities']:
            max_sol += c['barracks'] * 3000
            max_tnk += c['factory'] * 250
            max_pln += c['airforcebase'] * 15
            max_shp += c['drydock']
        
        for war in nation['offensive_wars']:
            if war['defender']['alliance_id'] in ['4729', '7531'] or war['defender']['alliance_id'] in ['4729', '7531']:
                if war['turnsleft'] <= 0:
                    await self.remove_from_thread(ctx.channel, war['defender']['id'])
                else:
                    await self.add_to_thread(ctx.channel, war['defender']['id'])
        
        for war in nation['defensive_wars']:
            if war['attacker']['alliance_id'] in ['4729', '7531'] or war['attacker']['alliance_id'] in ['4729', '7531']:
                if war['turnsleft'] <= 0:
                    await self.remove_from_thread(ctx.channel, war['attacker']['id'])
                else:
                    await self.add_to_thread(ctx.channel, war['attacker']['id'])

        nation['offensive_wars'] = [y for y in nation['offensive_wars'] if y['turnsleft'] > 0]
        nation['defensive_wars'] = [y for y in nation['defensive_wars'] if y['turnsleft'] > 0]

        if nation['alliance']:
            alliance = f"[{nation['alliance']['name']}](https://politicsandwar.com/alliance/id={nation['alliance_id']})"
        else:
            alliance = "No alliance"

        desc = f"[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']}) | {alliance}\n\nLast login: <t:{round(datetime.strptime(nation['last_active'], '%Y-%m-%d %H:%M:%S').timestamp())}:R>\nOffensive wars: {len(nation['offensive_wars'])}/{max_offense}\nDefensive wars: {len(nation['defensive_wars'])}/3\nDefensive range: {round(nation['score'] / 1.75)} - {round(nation['score'] / 0.75)}{beige}\n\nSoldiers: **{nation['soldiers']:,}** / {max_sol:,}\nTanks: **{nation['tanks']:,}** / {max_tnk:,}\nPlanes: **{nation['aircraft']:,}** / {max_pln:,}\nShips: **{nation['ships']:,}** / {max_shp:,}"
        embed = discord.Embed(title=f"{nation['nation_name']} ({nation['id']}) & their wars", description=desc, color=0x00ff00)
        embed1 = discord.Embed(title=f"{nation['nation_name']} ({nation['id']}) & their wars", description=desc, color=0x00ff00)
        embed.set_footer(text="_________________________________\nThe winrate is the chance for the nation in question to win a ground/air/naval roll. Battles consists of 3 rolls. A percentage abvove 50 is good. Use $battlesim for more detailed battle predictions.")
        embed1.set_footer(text="_________________________________\nThe winrate is the chance for the nation in question to win a ground/air/naval roll. Battles consists of 3 rolls. A percentage abvove 50 is good. Use $battlesim for more detailed battle predictions.")
        n = 1

        for war in nation['offensive_wars'] + nation['defensive_wars']:
            n += 1
            if n % 2 == 0:
                embed.add_field(name="\u200b", value="\u200b", inline=False)
                embed1.add_field(name="\u200b", value="\u200b", inline=False)
            else:
                embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed1.add_field(name="\u200b", value="\u200b", inline=True)

            if war in nation['offensive_wars']:
                result = await self.battle_calc(nation['id'], war['defender']['id'])
                war_emoji = "⚔️"
                x = war['defender']
                main_enemy_res = war['att_resistance']
                main_enemy_points = war['attpoints']
                their_enemy_points = war['defpoints']
                their_enemy_res = war['def_resistance']
            else:
                result = await self.battle_calc(nation['id'], war['attacker']['id'])
                war_emoji = "🛡️"
                x = war['attacker']
                main_enemy_res = war['def_resistance']
                main_enemy_points = war['defpoints']
                their_enemy_points = war['attpoints']
                their_enemy_res = war['att_resistance']
            
            main_enemy_bar = ""
            their_enemy_bar = ""
            for z in range(math.ceil(main_enemy_res / 10)):
                if main_enemy_res > 66:
                    main_enemy_bar += "🟩"
                elif main_enemy_res > 33:
                    main_enemy_bar += "🟨"
                else:
                    main_enemy_bar += "🟥"
            while len(main_enemy_bar) < 10:
                main_enemy_bar += "⬛"
            
            for z in range(math.ceil(their_enemy_res / 10)):
                if their_enemy_res > 66:
                    their_enemy_bar += "🟩"
                elif their_enemy_res > 33:
                    their_enemy_bar += "🟨"
                else:
                    their_enemy_bar += "🟥"
            while len(their_enemy_bar) < 10:
                their_enemy_bar += "⬛"

            if nation['pirate_economy']:
                max_offense = 6
            else:
                max_offense = 5
            
            if nation['beigeturns'] > 0:
                beige = f"\nBeige (turns): {nation['beigeturns']}"
            else:
                beige = ""

            max_sol = 0
            max_tnk = 0
            max_pln = 0
            max_shp = 0            
            for c in x['cities']:
                max_sol += c['barracks'] * 3000
                max_tnk += c['factory'] * 250
                max_pln += c['airforcebase'] * 15
                max_shp += c['drydock'] * 5

            if x['vmode'] > 0:
                vmstart = "~~"
                vmend = "~~"
            else:
                vmstart = ""
                vmend = ""

            x['offensive_wars'] = [y for y in x['offensive_wars'] if y['turnsleft'] > 0]
            x['defensive_wars'] = [y for y in x['defensive_wars'] if y['turnsleft'] > 0]

            if x['alliance']:
                alliance = f"[{x['alliance']['name']}](https://politicsandwar.com/alliance/id={x['alliance_id']})"
            else:
                alliance = "No alliance"

            embed.add_field(name=f"\{war_emoji} {x['nation_name']} ({x['id']})", value=f"{vmstart}[War timeline](https://politicsandwar.com/nation/war/timeline/war={war['id']}) | [Message](https://politicsandwar.com/inbox/message/receiver={x['leader_name'].replace(' ', '+')})\n{alliance}\n\n**[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']})**{result['nation1_append']}\n{main_enemy_bar}\n**{main_enemy_res}/100** | MAPs: **{main_enemy_points}/12**\n\n**[{x['nation_name']}](https://politicsandwar.com/nation/id={x['id']})**{result['nation2_append']}\n{their_enemy_bar}\n**{their_enemy_res}/100** | MAPs: **{their_enemy_points}/12**\n\nExpiration (turns): {war['turnsleft']}\nLast login: <t:{round(datetime.strptime(x['last_active'], '%Y-%m-%d %H:%M:%S').timestamp())}:R>\nOngoing wars: {len(x['offensive_wars'] + x['defensive_wars'])}\n\nGround winrate: **{round(100 * result['nation2_ground_win_rate'])}%**\nAir winrate: **{round(100 * (1 - result['nation1_air_win_rate']))}%**\nNaval winrate: **{round(100 * (1 - result['nation1_naval_win_rate']))}%**{vmend}", inline=True)
            embed1.add_field(name=f"\{war_emoji} {x['nation_name']} ({x['id']})", value=f"{vmstart}[War timeline](https://politicsandwar.com/nation/war/timeline/war={war['id']}) | [Message](https://politicsandwar.com/inbox/message/receiver={x['leader_name'].replace(' ', '+')})\n{alliance}\n\n**[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']})**{result['nation1_append']}\n**[{x['nation_name']}](https://politicsandwar.com/nation/id={x['id']})**{result['nation2_append']}\n\nOffensive wars: {len(x['offensive_wars'])}/{max_offense}\nDefensive wars: {len(x['defensive_wars'])}/3{beige}\n\n Soldiers: **{x['soldiers']:,}** / {max_sol:,}\nTanks: **{x['tanks']:,}** / {max_tnk:,}\nPlanes: **{x['aircraft']:,}** / {max_pln:,}\nShips: **{x['ships']:,}** / {max_shp:,}\n\nGround winrate: **{round(100 * result['nation2_ground_win_rate'])}%**\nAir winrate: **{round(100 * (1 - result['nation1_air_win_rate']))}%**\nNaval winrate: **{round(100 * (1 - result['nation1_naval_win_rate']))}%**{vmend}", inline=True)
        
        await message.edit(content="", attachments=[], embed=embed)
        react01 = asyncio.create_task(message.add_reaction("1\N{variation selector-16}\N{combining enclosing keycap}"))
        react02 = asyncio.create_task(message.add_reaction("2\N{variation selector-16}\N{combining enclosing keycap}"))
        await asyncio.gather(react01, react02)
        cur_page = 1
                
        async def reaction_checker():
            #print('reaction')
            while True:
                try:
                    nonlocal cur_page
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=600)
                    if user.id != ctx.author.id or reaction.message != message:
                        continue
                    
                    elif str(reaction.emoji) == "1\N{variation selector-16}\N{combining enclosing keycap}" and cur_page == 2:
                        cur_page = 1
                        msg_embd = [embed, embed1][cur_page-1]
                        await message.edit(content="", embed=msg_embd)
                        await message.remove_reaction(reaction, ctx.author)

                    elif str(reaction.emoji) == "2\N{variation selector-16}\N{combining enclosing keycap}" and cur_page == 1:
                        cur_page = 2
                        msg_embd = [embed, embed1][cur_page-1]
                        await message.edit(content="", embed=msg_embd)
                        await message.remove_reaction(reaction, ctx.author)

                    else:
                        await message.remove_reaction(reaction, ctx.author)

                except asyncio.TimeoutError:
                    await message.edit(content="**Command timed out!**")
                    #print('reaction break')
                    break

        reacttask = asyncio.create_task(reaction_checker())

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def war_scanner(self, ctx):
        await self.wars()

    async def add_to_thread(self, thread, atom):
        #print("adding", atom)
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(atom)
        if person == {}:
            print("tried to add, but could not find", atom)
            return
        user = await self.bot.fetch_user(person['user'])
        try:
            await thread.add_user(user)
        except Exception as e:
            await thread.send(f"I was unable to add {user} to the thread.\n```{e}```")
    
    async def remove_from_thread(self, thread, atom):
        #print("removing ", atom)
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(atom)
        if person == {}:
            print("tried to remove, but could not find", atom)
            return
        user = await self.bot.fetch_user(person['user'])
        try:
            await thread.remove_user(user)
        except:
            await thread.send(f"I was unable to add {user} to the thread.")

    async def wars(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(923249186500116560)
        prev_wars = None

        async def cthread(name, embed, non_atom, atom, new_war):
            found = False
            for thread in channel.threads:
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
            embed = discord.Embed(title=f"New {war['war_type'].lower().capitalize()} War", description=f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) declared a{'n'[:(len(war['war_type'])-5)^1]} {war['war_type'].lower()} war on [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']})", color=0x2F3136)
            await cthread(f"{non_atom['nation_name']} ({non_atom['id']})", embed, non_atom, atom, False)
            
            for thread in channel.threads:
                if f"({non_atom['id']})" in thread.name:
                    #print("match")
                    if peace != None:
                        embed = discord.Embed(title="Peace offering", description=f"[{peace['offerer']['nation_name']}](https://politicsandwar.com/nation/id={peace['offerer']['id']}) is offering peace to [{peace['reciever']['nation_name']}](https://politicsandwar.com/nation/id={peace['reciever']['id']}). The peace offering will be canceled if either side performs an act of aggression.", color=0xffffff)
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
            try:
                #print("check", datetime.utcnow())
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] days_ago:5){{id att_fortify war_type def_fortify attpeace defpeace turnsleft attacker{{nation_name alliance{{name}} id num_cities alliance_id cities{{id}}}} defender{{nation_name alliance{{name}} id num_cities alliance_id cities{{id}}}} attacks{{type victor moneystolen success cityid resistance_eliminated infradestroyed infra_destroyed_value improvementslost attcas1 attcas2 defcas1 defcas2}}}}}}"}) as temp:
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
                    async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] days_ago:5 active:false){{id att_fortify war_type def_fortify attpeace defpeace turnsleft attacker{{nation_name alliance{{name}} id num_cities alliance_id cities{{id}}}} defender{{nation_name alliance{{name}} id num_cities alliance_id cities{{id}}}} attacks{{type victor moneystolen success cityid resistance_eliminated infradestroyed infra_destroyed_value improvementslost attcas1 attcas2 defcas1 defcas2}}}}}}"}) as temp:
                        try:
                            done_wars = (await temp.json())['data']['wars']
                        except:
                            print((await temp.json())['errors'])
                            await asyncio.sleep(60)
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
                            embed = discord.Embed(title=f"New {new_war['war_type'].lower().capitalize()} War", description=f"[{new_war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={new_war['attacker']['id']}) declared a{'n'[:(len(new_war['war_type'])-5)^1]} {new_war['war_type'].lower()} war on [{new_war['defender']['nation_name']}](https://politicsandwar.com/nation/id={new_war['defender']['id']})", color=0x2F3136)
                            await cthread(f"{non_atom['nation_name']} ({non_atom['id']})", embed, non_atom, atom, True)
                            for attack in new_war['attacks']:
                                attacker = await attack_check(attack, new_war)
                                await smsg(attacker, attack, new_war, atom, non_atom, None)
                    for old_war in prev_wars:
                        for done_war in done_wars:
                            if done_war['id'] == old_war['id']:
                                print("wars match")
                                if old_war['attacker']['alliance_id'] in ['4729', '7531']: ## CHANGE T0 ATOM ---------------------------------------------------------
                                    atom = old_war['attacker']
                                    non_atom = old_war['defender']
                                else:
                                    atom = old_war['defender']
                                    non_atom = old_war['attacker']
                                attack = None
                                for attack in done_war['attacks']:
                                    if attack not in old_war['attacks']:
                                        attacker = await attack_check(attack, done_war)
                                        await smsg(attacker, attack, done_war, atom, non_atom, None)
                                for thread in channel.threads:
                                    if f"({non_atom['id']})" in thread.name:
                                        print("found thread")
                                        embed = discord.Embed(title=f"War finished", description=f"[{old_war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={old_war['attacker']['id']}) is no longer at war with [{old_war['defender']['nation_name']}](https://politicsandwar.com/nation/id={old_war['defender']['id']})", color=0xffFFff)
                                        await thread.send(embed=embed)
                                        await self.remove_from_thread(thread, atom)
                                        if thread.member_count == 1:
                                            await thread.edit(archive=True)
                                        break
                            break
                prev_wars = wars
                await asyncio.sleep(60)
            except Exception as e:
                await channel.send(f"I encountered an error```{e}```")

    @commands.command(brief='Add someone to the military coordination thread.')
    @commands.has_any_role('Pupil', 'Zealot', 'Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def add(self, ctx, *, user):
        await self.add_to_thread(ctx.channel, user)

    @commands.command(brief='Reomve someone from the military coordination thread.')
    @commands.has_any_role('Deacon', 'Advisor', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def remove(self, ctx, *, user):
        await self.remove_from_thread(ctx.channel, user)

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

    @commands.command(aliases=['spherecounters'], brief='Accepts one argument, gives you a pre-filled link to slotter.', help='Accepted arguments include nation name, leader name, nation id and nation link. When browsing the databse, Fuquiem will use the first match, so it can be wise to double check that it returns a slotter link for the correct person.')
    async def allcounters(self, ctx, *, arg):
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
        embed = discord.Embed(title="Sphere Counters",
                              description=f"[Explore counters against {result['nation']} on slotter](https://slotter.bsnk.dev/search?nation={result['nationid']}&alliances=4729,7531,790,5012,2358,6877,8804&countersMode=true&threatsMode=false&vm=false&grey=true&beige=false)", color=0x00ff00)
        await ctx.send(embed=embed)

    @commands.command(aliases=['target'], brief='Sends you a pre-filled link to slotter')
    async def targets(self, ctx):
        await ctx.send('This command has been disabled.')
        return
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
                    except discord.Forbidden:
                        await ctx.send(f"{user} does not allow my DMs")
                    except:
                        print('cannot message', nation['nation'], ' yet they did not block me')

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
                await ctx.send("This person already has enough resources to fulfill minimum requirements!")

            try:
                await user.send(f"Hey, you have an excess of {excess}please deposit it here for safekeeping: https://politicsandwar.com/alliance/id={nation['allianceid']}&display=bank")
                print('i just sent a msg to', user, excess)
            except discord.Forbidden:
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
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{nations(page:1 first:500 alliance_id:4729 vmode:false){data{id leader_name nation_name score warpolicy spies cia spy_satellite espionage_available}}}"}) as temp:
                church = (await temp.json())['data']['nations']['data']
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{nations(page:1 first:500 alliance_id:7531 vmode:false){data{id leader_name nation_name score warpolicy spies cia spy_satellite espionage_available}}}"}) as temp:
                convent = (await temp.json())['data']['nations']['data']
            sum = church + convent
            for member in sum:
                if member['espionage_available']:
                    person = await Database.find_user(member['id'])
                    user = await self.bot.fetch_user(person['user']) # person['user']
                    if member['spy_satellite']:
                        spy_sat = "SS"
                    else:
                        spy_sat = "No SS"
                    embed = discord.Embed(title="Remember to use your spy ops!",
                                description=f"You can spy on someone you're fighting, or you can say ```{round(float(member['score']))} / {member['spies']} / {spy_sat} / <@131589896950251520> <@220333267121864706>``` in <#668581622693625907>", color=0x00ff00)
                    try:
                        await user.send(embed=embed)
                    except:
                        pass
    
    async def spy_calc(nation):
        async with aiohttp.ClientSession() as session:
            if nation['warpolicy'] == "Arcane":
                percent = 57.5
            elif nation['warpolicy'] == "Tactician":
                percent = 42.5
            else:
                percent = 50
            upper_lim = 60
            lower_lim = 0
            while True:
                spycount = math.floor((upper_lim + lower_lim)/2)
                async with session.get(f"https://politicsandwar.com/war/espionage_get_odds.php?id1=341326&id2={nation['id']}&id3=0&id4=1&id5={spycount}") as probability:
                    probability = await probability.text()
                #print(probability, spycount, upper_lim, lower_lim)
                if "Greater than 50%" in probability:
                    upper_lim = spycount
                else:
                    lower_lim = spycount
                if upper_lim - 1 == lower_lim:
                    break
            enemyspy = round((((100*int(spycount))/(percent-25))-2)/3)
            if enemyspy > 60:
                enemyspy = 60
            elif enemyspy > 50 and not nation['cia']:
                enemyspy = 50
            elif enemyspy < 2:
                enemyspy = 0
        return enemyspy

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

    @commands.command(brief='Find raid targets', aliases=['raid'], help="When going through the setup wizard, you can choose to get the results on discord or on a webpage. If you decide to get the targets on discord, you will be able to react with the arrows in order to view different targets. You can also type 'page 62' to go nation number 62. This will of course work for any number. By reacting with the clock, you will add a beige reminder for the nation if they are in beige. Fuquiem will then DM you when the nation exits beige. You can use $reminders to view active reminders. If you choose to get the targets on a webpage, you will get a link to a page with a table. The table will include every valid nation, and relevant information about this nation. If you want beige reminders, there is a 'remind me'-button for every nation currently in beige. You can press the table headers to sort by different attributes. By default it's sorted by monetary net income.")
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
            await message.edit(content="Getting targets...", embed=None, file=gif)

            #start_time = time.time()

            if applicants == True:
                async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:250 min_score:{minscore} max_score:{maxscore} vmode:false alliance_position:1){{paginatorInfo{{lastPage}}}}}}"}) as temp:
                    tot_pages += (await temp.json())['data']['nations']['paginatorInfo']['lastPage']
                    app_pages += (await temp.json())['data']['nations']['paginatorInfo']['lastPage']

            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:250 min_score:{minscore} max_score:{maxscore} vmode:false{who}){{paginatorInfo{{lastPage}}}}}}"}) as temp1:
                tot_pages += (await temp1.json())['data']['nations']['paginatorInfo']['lastPage']
                any_pages += (await temp1.json())['data']['nations']['paginatorInfo']['lastPage']

            if applicants == True:
                for n in range(1, app_pages):
                    #print(n)
                    url = f"https://api.politicsandwar.com/graphql?api_key={api_key}"
                    json = {'query': f"{{nations(page:{n} first:250 min_score:{minscore} max_score:{maxscore} vmode:false alliance_position:1){{data{{id flag nation_name last_active leader_name continent dompolicy population alliance_id beigeturns score color soldiers tanks aircraft ships missiles nukes alliance{{name id}} offensive_wars{{winner turnsleft}} defensive_wars{{date winner turnsleft attacks{{loot_info victor moneystolen}}}} alliance_position num_cities ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}
                    futures.append(asyncio.ensure_future(call_api(url, json)))
                    await asyncio.sleep(0.2)
            
            for n in range(1, any_pages):
                #print(n)
                url = f"https://api.politicsandwar.com/graphql?api_key={api_key}"
                json = {'query': f"{{nations(page:{n} first:250 min_score:{minscore} max_score:{maxscore} vmode:false{who}){{data{{id flag nation_name last_active leader_name continent dompolicy population alliance_id beigeturns score color soldiers tanks aircraft ships missiles nukes alliance{{name id}} offensive_wars{{winner turnsleft}} defensive_wars{{date winner turnsleft attacks{{loot_info victor moneystolen}}}} alliance_position num_cities ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap cities{{id date powered infrastructure land oilpower windpower coalpower nuclearpower coalmine oilwell uramine barracks farm policestation hospital recyclingcenter subway supermarket bank mall stadium leadmine ironmine bauxitemine gasrefinery aluminumrefinery steelmill munitionsfactory factory airforcebase drydock}}}}}}}}"}
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
                await message.edit(content="No targets matched your criteria!", attachments=[])
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

            temp, colors, prices, treasures, radiation, seasonal_mod = await pre_revenue_calc(mongo, cipher_suite, api_key, message, query_for_nation=False, parsed_nation=atck_ntn)

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

                rev_obj = await revenue_calc(message, target, radiation, treasures, prices, colors, seasonal_mod)

                target['monetary_net_num'] = rev_obj['monetary_net_num']
                embed.add_field(name="Monetary Net Income", value=rev_obj['mon_net_txt'])
                
                target['net_cash_num'] = rev_obj['net_cash_num']
                embed.add_field(name="Net Cash Income", value=rev_obj['money_txt'])

                target['max_infra'] = rev_obj['max_infra']
                target['avg_infra'] = rev_obj['avg_infra']
                embed.add_field(name="Infra", value=f"Max: {rev_obj['max_infra']}\nAvg: {rev_obj['avg_infra']}")

                ground_win_rate = self.winrate_calc((atck_ntn['soldiers'] * 1.75 + atck_ntn['tanks'] * 40), (target['soldiers'] * 1.75 + target['tanks'] * 40 + target['population'] * 0.0025))

                target['groundwin'] = ground_win_rate
                embed.add_field(name="Chance to win ground rolls", value=str(round(100*ground_win_rate)) + "%")

                air_win_rate = self.winrate_calc((atck_ntn['aircraft'] * 3), (target['aircraft'] * 3))
                
                target['airwin'] = air_win_rate
                embed.add_field(name="Chance to win air rolls", value=str(round(100*air_win_rate)) + "%")

                naval_win_rate = self.winrate_calc((atck_ntn['ships'] * 4), (target['ships'] * 4))
                
                target['navalwin'] = naval_win_rate
                embed.add_field(name="Chance to win naval rolls", value=str(round(100*naval_win_rate)) + "%")

                target['winchance'] = round((ground_win_rate+air_win_rate+naval_win_rate)*100/3)

                if not webpage:
                    target['embed'] = embed
                
        best_targets = sorted(target_list, key=lambda k: k['monetary_net_num'], reverse=True)

        if webpage:
            endpoint = datetime.utcnow().strftime('%d%H%M%S')
            class webraid(MethodView):
                def get(raidclass):
                    #print(invoker)
                    beige_alerts = mongo.users.find_one({"user": int(invoker)})['beige_alerts']
                    with open('./data/templates/raidspage.txt', 'r') as file:
                        template = file.read()
                    result = Template(template).render(attacker=atck_ntn, targets=best_targets, endpoint=endpoint, invoker=str(invoker), beige_alerts=beige_alerts, datetime=datetime)
                    return str(result)

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
            await message.edit(content=f"Go to https://fuquiem.karemcbob.repl.co/raids/{endpoint}", attachments=[])
            return
        
        pages = len(target_list)
        msg_embd = best_targets[0]['embed']
        msg_embd.set_footer(text=f"Page {1}/{pages}")
        await message.edit(content="", embed=msg_embd, attachments=[])
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
            #print('reaction')
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
                    #print('reaction break')
                    break

        msgtask = asyncio.create_task(message_checker())
        reacttask = asyncio.create_task(reaction_checker())

        await asyncio.gather(msgtask, reacttask)
    
    def winrate_calc(self, attacker_value, defender_value):
        try:
            x = attacker_value / defender_value
            if x > 2:
                winrate = 1
            elif x < 0.4:
                winrate = 0
            else:
                winrate = (12.832883444301027*x**(11)-171.668262561212487*x**(10)+1018.533858483560834*x**(9)-3529.694284997589875*x**(8)+7918.373606722701879*x**(7)-12042.696852729619422*x**(6)+12637.399722721022044*x**(5)-9128.535790660698694*x**(4)+4437.651655224382012*x**(3)-1378.156072477675025*x**(2)+245.439740545813436*x-18.980551645186498)
        except ZeroDivisionError:
            winrate = 1
        return winrate

    @commands.command(aliases=['bsim', 'bs'], brief='Simulate battles between two nations', help="Accepts up to two arguments. The first argument is the attacking nation, whilst the latter is the defending nation. If only one argument is provided, Fuquiem will assume that you are the defender")
    @commands.has_any_role('Pupil', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def battlesim(self, ctx, nation1=None, nation2=None):
        #check is any wars are active, and if they have air superiority, ground control, fortified etc
        message = await ctx.send('Alright, give me a sec to calculate the winrates...')
        Database = self.bot.get_cog('Database')
        if nation1 == None:
            nation1 = ctx.author.id
        nation1_nation = await Database.find_user(nation1)
        if nation1_nation == {}:
            try:
                nation1_nums = int(re.sub("[^0-9]", "", nation1))
                nation1_nation = list(mongo.world_nations.find({"nationid": nation1_nums}).collation(
                    {"locale": "en", "strength": 1}))[0]
            except:
                try:
                    nation1_nation = list(mongo.world_nations.find({"leader": nation1}).collation(
                        {"locale": "en", "strength": 1}))[0]
                except:
                    try:
                        nation1_nation = list(mongo.world_nations.find({"nation": nation1}).collation(
                        {"locale": "en", "strength": 1}))[0]
                    except:
                        nation1_nation = None
            if not nation1_nation:
                if nation2 == None:
                    await message.edit(content='I could not find that nation!')
                    return
                else:
                    await message.edit(content='I could not find nation 1!')
                    return 
        nation1_id = str(nation1_nation['nationid'])

        done = False
        if isinstance(ctx.channel, discord.Thread) and nation2 == None:
            try:
                chan = ctx.channel.name
                nation2_id = str(chan[chan.index("(")+1:-1])
                done = True
            except:
                pass

        if not done:
            if nation2 == None:
                nation2 = ctx.author.id
            nation2_nation = await Database.find_user(nation2)
            if nation2_nation == {}:
                try:
                    nation2_nation = list(mongo.world_nations.find({"nation": nation2}).collation(
                        {"locale": "en", "strength": 1}))[0]
                except:
                    try:
                        nation2_nation = list(mongo.world_nations.find({"leader": nation2}).collation(
                            {"locale": "en", "strength": 1}))[0]
                    except:
                        try:
                            nation2 = int(re.sub("[^0-9]", "", nation2))
                            nation2_nation = list(mongo.world_nations.find({"nationid": nation2}).collation(
                                {"locale": "en", "strength": 1}))[0]
                        except:
                            nation2_nation = None
                if not nation2_nation:
                    if nation2 == None:
                        await message.edit(content='I was able to find the nation you linked, but I could not find *your* nation!')
                        return
                    else:
                        await message.edit(content='I could not find nation 2!')
                        return 
            nation2_id = str(nation2_nation['nationid'])
        
        results = await self.battle_calc(nation1_id, nation2_id)

        embed = discord.Embed(title="Battle Simulator", description=f"These are the results for when [{results['nation1_nation']['nation_name']}](https://politicsandwar.com/nation/id={results['nation1_nation']['id']}){results['nation1_append']} attacks [{results['nation2_nation']['nation_name']}](https://politicsandwar.com/nation/id={results['nation2_nation']['id']}){results['nation2_append']}\nIf you want to use custom troop counts, you can use the [in-game battle simulators](https://politicsandwar.com/tools/)", color=0x00ff00)
        embed1 = discord.Embed(title="Battle Simulator", description=f"These are the results for when [{results['nation2_nation']['nation_name']}](https://politicsandwar.com/nation/id={results['nation2_nation']['id']}){results['nation2_append']} attacks [{results['nation1_nation']['nation_name']}](https://politicsandwar.com/nation/id={results['nation1_nation']['id']}){results['nation1_append']}\nIf you want to use custom troop counts, you can use the [in-game battle simulators](https://politicsandwar.com/tools/)", color=0x00ff00)

        if results['nation2_nation']['soldiers'] + results['nation2_nation']['tanks'] + results['nation1_nation']['soldiers'] + results['nation1_nation']['tanks'] == 0:
            embed.add_field(name="Ground Attack", value="Nobody has any forces!")
            embed1.add_field(name="Ground Attack", value="Nobody has any forces!")
        else:
            embed.add_field(name="Ground Attack", value=f"Immense Triumph: {round(results['nation1_ground_it']*100)}%\nModerate Success: {round(results['nation1_ground_mod']*100)}%\nPyrrhic Victory: {round(results['nation1_ground_pyr']*100)}%\nUtter Failure: {round(results['nation1_ground_fail']*100)}%")
            embed1.add_field(name="Ground Attack", value=f"Immense Triumph: {round(results['nation2_ground_it']*100)}%\nModerate Success: {round(results['nation2_ground_mod']*100)}%\nPyrrhic Victory: {round(results['nation2_ground_pyr']*100)}%\nUtter Failure: {round(results['nation2_ground_fail']*100)}%")
        
        if results['nation2_nation']['aircraft'] + results['nation1_nation']['aircraft'] != 0:
            embed.add_field(name="Airstrike", value=f"Immense Triumph: {round(results['nation1_air_it']*100)}%\nModerate Success: {round(results['nation1_air_mod']*100)}%\nPyrrhic Victory: {round(results['nation1_air_pyr']*100)}%\nUtter Failure: {round(results['nation1_air_fail']*100)}%")
            embed1.add_field(name="Airstrike", value=f"Immense Triumph: {round(results['nation1_air_fail']*100)}%\nModerate Success: {round(results['nation1_air_pyr']*100)}%\nPyrrhic Victory: {round(results['nation1_air_mod']*100)}%\nUtter Failure: {round(results['nation1_air_it']*100)}%")
        else:
            embed.add_field(name="Airstrike", value="Nobody has any forces!")
            embed1.add_field(name="Airstrike", value="Nobody has any forces!")

        if results['nation2_nation']['ships'] + results['nation1_nation']['ships'] != 0:
            embed.add_field(name="Naval Battle", value=f"Immense Triumph: {round(results['nation1_naval_it']*100)}%\nModerate Success: {round(results['nation1_naval_mod']*100)}%\nPyrrhic Victory: {round(results['nation1_naval_pyr']*100)}%\nUtter Failure: {round(results['nation1_naval_fail']*100)}%")
            embed1.add_field(name="Naval Battle", value=f"Immense Triumph: {round(results['nation1_naval_fail']*100)}%\nModerate Success: {round(results['nation1_naval_pyr']*100)}%\nPyrrhic Victory: {round(results['nation1_naval_mod']*100)}%\nUtter Failure: {round(results['nation1_naval_it']*100)}%")

        else:
            embed.add_field(name="Naval Battle", value="Nobody has any forces!")
            embed1.add_field(name="Naval Battle", value="Nobody has any forces!")

        embed.add_field(name="Casualties", value=f"Att. Sol.: {results['nation1_ground_nation1_avg_soldiers']:,} ± {results['nation1_ground_nation1_diff_soldiers']:,}\nAtt. Tnk.: {results['nation1_ground_nation1_avg_tanks']:,} ± {results['nation1_ground_nation1_diff_tanks']:,}\n\nDef. Sol.: {results['nation1_ground_nation2_avg_soldiers']:,} ± {results['nation1_ground_nation2_diff_soldiers']:,}\nDef. Tnk.: {results['nation1_ground_nation2_avg_tanks']:,} ± {results['nation1_ground_nation2_diff_tanks']:,}\n\n{results['aircas1']}")        
        embed1.add_field(name="results", value=f"Att. Sol.: {results['nation2_ground_nation2_avg_soldiers']:,} ± {results['nation2_ground_nation2_diff_soldiers']:,}\nAtt. Tnk.: {results['nation2_ground_nation2_avg_tanks']:,} ± {results['nation2_ground_nation2_diff_tanks']:,}\n\nDef. Sol.: {results['nation2_ground_nation1_avg_soldiers']:,} ± {results['nation2_ground_nation1_diff_soldiers']:,}\nDef. Tnk.: {results['nation2_ground_nation1_avg_tanks']:,} ± {results['nation2_ground_nation1_diff_tanks']:,}\n\n{results['aircas2']}")        
        
        embed.add_field(name="Casualties", value=f"*Targeting air:*\nAtt. Plane: {results['nation1_airtoair_nation1_avg']:,} ± {results['nation1_airtoair_nation1_diff']:,}\nDef. Plane: {results['nation1_airtoair_nation2_avg']:,} ± {results['nation1_airtoair_nation2_diff']:,}\n\n*Targeting other:*\nAtt. Plane: {results['nation1_airtoother_nation1_avg']:,} ± {results['nation1_airtoother_nation1_diff']:,}\nDef. Plane: {results['nation1_airtoother_nation2_avg']:,} ± {results['nation1_airtoother_nation2_diff']:,}")        
        embed1.add_field(name="Casualties", value=f"*Targeting air:*\nAtt. Plane: {results['nation2_airtoair_nation2_avg']:,} ± {results['nation2_airtoair_nation2_diff']:,}\nDef. Plane: {results['nation2_airtoair_nation1_avg']:,} ± {results['nation2_airtoair_nation1_diff']:,}\n\n*Targeting other:*\nAtt. Plane: {results['nation2_airtoother_nation2_avg']:,} ± {results['nation2_airtoother_nation2_diff']:,}\nDef. Plane: {results['nation2_airtoother_nation1_avg']:,} ± {results['nation2_airtoother_nation1_diff']:,}")        

        embed.add_field(name="Casualties", value=f"Att. Ships: {results['nation1_naval_nation1_avg']:,} ± {results['nation1_naval_nation1_diff']:,}\nDef. Ships: {results['nation1_naval_nation2_avg']:,} ± {results['nation1_naval_nation2_diff']:,}")        
        embed1.add_field(name="Casualties", value=f"Att. Ships: {results['nation2_naval_nation2_avg']:,} ± {results['nation2_naval_nation2_diff']:,}\nDef. Ships: {results['nation2_naval_nation1_avg']:,} ± {results['nation2_naval_nation1_diff']:,}")        

        await message.edit(embed=embed, content="")
        await message.add_reaction("↔️")
        cur_page = 1
                
        async def reaction_checker():
            #print('reaction')
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
                    #print('reaction break')
                    break

        reacttask = asyncio.create_task(reaction_checker())

        await asyncio.gather(reacttask)

        
    async def battle_calc(self, nation1_id, nation2_id):
        results = {}

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation1_id}){{data{{nation_name population id soldiers tanks aircraft ships defensive_wars{{groundcontrol airsuperiority navalblockade attpeace defpeace attid defid att_fortify def_fortify turnsleft}} offensive_wars{{groundcontrol airsuperiority navalblockade attpeace defpeace attid defid att_fortify def_fortify turnsleft}}}}}}}}"}) as temp:
                results['nation1_nation'] = (await temp.json())['data']['nations']['data'][0]
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation2_id}){{data{{nation_name population id soldiers tanks aircraft ships}}}}}}"}) as temp:
                results['nation2_nation'] = (await temp.json())['data']['nations']['data'][0]

        results['nation1_append'] = ""
        results['nation2_append'] = ""
        results['nation1_tanks'] = 1
        results['nation2_tanks'] = 1
        results['nation1_extra_cas'] = 1
        results['nation2_extra_cas'] = 1
        results['gc'] = None

        for war in results['nation1_nation']['defensive_wars'] + results['nation1_nation']['offensive_wars']:
            if war['attid'] == nation2_id and war['turnsleft'] > 0 and war in results['nation1_nation']['defensive_wars']:
                if war['groundcontrol'] == nation1_id:
                    results['gc'] = results['nation1_nation']
                    results['nation1_append'] += "<:small_gc:924988666613489685>"
                elif war['groundcontrol'] == nation2_id:
                    results['gc'] = results['nation2_nation']
                    results['nation2_append'] += "<:small_gc:924988666613489685>"
                if war['airsuperiority'] == nation1_id:
                    results['nation2_tanks'] = 0.5
                    results['nation1_append'] += "<:small_air:924988666810601552>"
                elif war['airsuperiority'] == nation2_id:
                    results['nation1_tanks'] = 0.5
                    results['nation2_append'] += "<:small_air:924988666810601552>"
                if war['navalblockade'] == nation1_id: #blockade is opposite than the others
                    results['nation2_append'] += "<:small_blockade:924988666814808114>"
                elif war['navalblockade'] == nation2_id:
                    results['nation1_append'] += "<:small_blockade:924988666814808114>"
                if war['att_fortify']:
                    results['nation2_append'] += "<:fortified:925465012955385918>"
                    results['nation1_extra_cas'] = 1.25
                if war['def_fortify']:
                    results['nation1_append'] += "<:fortified:925465012955385918>"
                    results['nation2_extra_cas'] = 1.25
                if war['attpeace']:
                    results['nation1_append'] += "<:peace:926855240655990836>"
                elif war['defpeace']:
                    results['nation2_append'] += "<:peace:926855240655990836>"
            elif war['defid'] == nation2_id and war['turnsleft'] > 0 and war in results['nation1_nation']['offensive_wars']:
                if war['groundcontrol'] == nation1_id:
                    results['gc'] = results['nation1_nation']
                    results['nation1_append'] += "<:small_gc:924988666613489685>"
                elif war['groundcontrol'] == nation2_id:
                    results['gc'] = results['nation2_nation']
                    results['nation2_append'] += "<:small_gc:924988666613489685>"
                if war['airsuperiority'] == nation1_id:
                    results['nation2_tanks'] = 0.5
                    results['nation1_append'] += "<:small_air:924988666810601552>"
                elif war['airsuperiority'] == nation2_id:
                    results['nation1_tanks'] = 0.5
                    results['nation2_append'] += "<:small_air:924988666810601552>"
                if war['navalblockade'] == nation1_id: #blockade is opposite than the others
                    results['nation2_append'] += "<:small_blockade:924988666814808114>"
                elif war['navalblockade'] == nation2_id:
                    results['nation1_append'] += "<:small_blockade:924988666814808114>"
                if war['att_fortify']:
                    results['nation1_append'] += "<:fortified:925465012955385918>"
                    results['nation2_extra_cas'] = 1.25
                if war['def_fortify']:
                    results['nation2_append'] += "<:fortified:925465012955385918>"
                    results['nation1_extra_cas'] = 1.25
                if war['attpeace']:
                    results['nation2_append'] += "<:peace:926855240655990836>"
                elif war['defpeace']:
                    results['nation1_append'] += "<:peace:926855240655990836>"
        
        nation2_army_value = results['nation2_nation']['soldiers'] * 1.75 + results['nation2_nation']['tanks'] * 40 * results['nation2_tanks'] + results['nation2_nation']['population'] * 0.0025
        nation1_army_value = results['nation1_nation']['soldiers'] * 1.75 + results['nation1_nation']['tanks'] * 40 * results['nation1_tanks']

        results['nation1_ground_win_rate'] = self.winrate_calc(nation1_army_value, nation2_army_value)
        
        results['aircas1'] = ""
        if results['gc'] == results['nation1_nation']:
            results['aircas1'] = f"Def. Plane: {round(results['nation1_nation']['tanks'] * 0.0075 * results['nation1_ground_win_rate'] ** 3)} ± {round(results['nation1_nation']['tanks'] * 0.0075 * (1 - results['nation1_ground_win_rate'] ** 3))}"
        
        winning = "loss"
        losing = "win"
        if nation1_army_value > nation2_army_value:
            winning = "win"
            losing = "loss"
        
        for party in ["nation2", "nation1"]:
            for variant in [{"type": "avg", "rate": 0.7}, {"type": "diff", "rate": 0.3}]:
                for fighter in [{"fighter": "soldiers", "win_cas_rate": 125, "loss_cas_rate": 125}, {"fighter": "tanks", "win_cas_rate": 1650, "loss_cas_rate": 1550}]:
                    if party == "nation1":
                        results[f"nation1_ground_{party}_{variant['type']}_{fighter['fighter']}"] = round(nation2_army_value * variant['rate'] / fighter[f"{winning}_cas_rate"] * 3 * results['nation1_extra_cas'])
                    elif party == "nation2":
                        results[f"nation1_ground_{party}_{variant['type']}_{fighter['fighter']}"] = round(nation1_army_value * variant['rate'] / fighter[f"{losing}_cas_rate"] * 3)

        nation2_army_value = results['nation2_nation']['soldiers'] * 1.75 + results['nation2_nation']['tanks'] * 40 * results['nation2_tanks']
        nation1_army_value = results['nation1_nation']['soldiers'] * 1.75 + results['nation1_nation']['tanks'] * 40 * results['nation1_tanks'] + results['nation1_nation']['population'] * 0.0025

        results['nation2_ground_win_rate'] = self.winrate_calc(nation2_army_value, nation1_army_value)
        
        results['aircas2'] = ""
        if results['gc'] == results['nation2_nation']:
            results['aircas2'] = f"Def. Plane: {round(results['nation2_nation']['tanks'] * 0.0075 * results['nation2_ground_win_rate'] ** 3)} ± {round(results['nation2_nation']['tanks'] * 0.0075 * (1 - results['nation2_ground_win_rate'] ** 3))}"
        
        winning = "loss"
        losing = "win"
        if nation2_army_value > nation1_army_value:
            winning = "win"
            losing = "loss"

        for party in ["nation2", "nation1"]:
            for variant in [{"type": "avg", "rate": 0.7}, {"type": "diff", "rate": 0.3}]:
                for fighter in [{"fighter": "soldiers", "win_cas_rate": 125, "loss_cas_rate": 125}, {"fighter": "tanks", "win_cas_rate": 1650, "loss_cas_rate": 1550}]:
                    if party == "nation2":
                        results[f"nation2_ground_{party}_{variant['type']}_{fighter['fighter']}"] = round(nation1_army_value * variant['rate'] / fighter[f"{winning}_cas_rate"] * 3 * results['nation2_extra_cas'])
                    elif party == "nation1":
                        results[f"nation2_ground_{party}_{variant['type']}_{fighter['fighter']}"] = round(nation2_army_value * variant['rate'] / fighter[f"{losing}_cas_rate"] * 3)

        results['nation1_air_win_rate'] = self.winrate_calc((results['nation1_nation']['aircraft'] * 3), (results['nation2_nation']['aircraft'] * 3))

        results['nation1_airtoair_nation1_avg'] = round(results['nation2_nation']['aircraft'] * 3 * 0.7 * 0.01 * 3 * results['nation1_extra_cas'])
        results['nation1_airtoair_nation1_diff'] = round(results['nation2_nation']['aircraft'] * 3 * 0.3 * 0.01 * 3 * results['nation1_extra_cas'])
        results['nation1_airtoother_nation1_avg'] = round(results['nation2_nation']['aircraft'] * 3 * 0.7 * 0.015385 * 3 * results['nation1_extra_cas'])
        results['nation1_airtoother_nation1_diff'] = round(results['nation2_nation']['aircraft'] * 3 * 0.3 * 0.015385 * 3 * results['nation1_extra_cas'])

        results['nation1_airtoair_nation2_avg'] = round(results['nation1_nation']['aircraft'] * 3 * 0.7 * 0.018337 * 3)
        results['nation1_airtoair_nation2_diff'] = round(results['nation1_nation']['aircraft'] * 3 * 0.3 * 0.018337 * 3)
        results['nation1_airtoother_nation2_avg'] = round(results['nation1_nation']['aircraft'] * 3 * 0.7 * 0.009091 * 3)
        results['nation1_airtoother_nation2_diff'] = round(results['nation1_nation']['aircraft'] * 3 * 0.3 * 0.009091 * 3)

        results['nation2_airtoair_nation2_avg'] = round(results['nation1_nation']['aircraft'] * 3 * 0.7 * 0.01 * 3 * results['nation2_extra_cas'])
        results['nation2_airtoair_nation2_diff'] = round(results['nation1_nation']['aircraft'] * 3 * 0.3 * 0.01 * 3 * results['nation2_extra_cas'])
        results['nation2_airtoother_nation2_avg'] = round(results['nation1_nation']['aircraft'] * 3 * 0.7 * 0.015385 * 3 * results['nation2_extra_cas'])
        results['nation2_airtoother_nation2_diff'] = round(results['nation1_nation']['aircraft'] * 3 * 0.3 * 0.015385 * 3 * results['nation2_extra_cas'])

        results['nation2_airtoair_nation1_avg'] = round(results['nation2_nation']['aircraft'] * 3 * 0.7 * 0.018337 * 3)
        results['nation2_airtoair_nation1_diff'] = round(results['nation2_nation']['aircraft'] * 3 * 0.3 * 0.018337 * 3)
        results['nation2_airtoother_nation1_avg'] = round(results['nation2_nation']['aircraft'] * 3 * 0.7 * 0.009091 * 3)
        results['nation2_airtoother_nation1_diff'] = round(results['nation2_nation']['aircraft'] * 3 * 0.3 * 0.009091 * 3)

        results['nation1_naval_win_rate'] = self.winrate_calc((results['nation1_nation']['ships'] * 4), (results['nation2_nation']['ships'] * 4))

        results['nation1_naval_nation2_avg'] = round(results['nation1_nation']['ships'] * 4 * 0.7 * 0.01375 * 3 * results['nation1_extra_cas'])
        results['nation1_naval_nation2_diff'] = round(results['nation1_nation']['ships'] * 4 * 0.3 * 0.01375 * 3 * results['nation1_extra_cas'])
        results['nation1_naval_nation1_avg'] = round(results['nation2_nation']['ships'] * 4 * 0.7 * 0.01375 * 3)
        results['nation1_naval_nation1_diff'] = round(results['nation2_nation']['ships'] * 4 * 0.3 * 0.01375 * 3)

        results['nation2_naval_nation2_avg'] = round(results['nation1_nation']['ships'] * 4 * 0.7 * 0.01375 * 3 * results['nation2_extra_cas'])
        results['nation2_naval_nation2_diff'] = round(results['nation1_nation']['ships'] * 4 * 0.3 * 0.01375 * 3 * results['nation2_extra_cas'])
        results['nation2_naval_nation1_avg'] = round(results['nation2_nation']['ships'] * 4 * 0.7 * 0.01375 * 3)
        results['nation2_naval_nation1_diff'] = round(results['nation2_nation']['ships'] * 4 * 0.3 * 0.01375 * 3)

        results['nation1_ground_it'] = results['nation1_ground_win_rate']**3
        results['nation1_ground_mod'] = results['nation1_ground_win_rate']**2 * (1 - results['nation1_ground_win_rate']) * 3
        results['nation1_ground_pyr'] = results['nation1_ground_win_rate'] * (1 - results['nation1_ground_win_rate'])**2 * 3
        results['nation1_ground_fail'] = (1 - results['nation1_ground_win_rate'])**3

        results['nation2_ground_it'] = results['nation2_ground_win_rate']**3
        results['nation2_ground_mod'] = results['nation2_ground_win_rate']**2 * (1 - results['nation2_ground_win_rate']) * 3
        results['nation2_ground_pyr'] = results['nation2_ground_win_rate'] * (1 - results['nation2_ground_win_rate'])**2 * 3
        results['nation2_ground_fail'] = (1 - results['nation2_ground_win_rate'])**3

        results['nation1_air_it'] = results['nation1_air_win_rate']**3
        results['nation1_air_mod'] = results['nation1_air_win_rate']**2 * (1 - results['nation1_air_win_rate']) * 3
        results['nation1_air_pyr'] = results['nation1_air_win_rate'] * (1 - results['nation1_air_win_rate'])**2 * 3
        results['nation1_air_fail'] = (1 - results['nation1_air_win_rate'])**3

        results['nation1_naval_it'] = results['nation1_naval_win_rate']**3
        results['nation1_naval_mod'] = results['nation1_naval_win_rate']**2 * (1 - results['nation1_naval_win_rate']) * 3
        results['nation1_naval_pyr'] = results['nation1_naval_win_rate'] * (1 - results['nation1_naval_win_rate'])**2 * 3
        results['nation1_naval_fail'] = (1 - results['nation1_naval_win_rate'])**3

        return results


def setup(bot):
    bot.add_cog(Military(bot))