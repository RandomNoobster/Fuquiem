import discord
import requests
import math
from main import mongo
from datetime import datetime, timedelta
from mako.template import Template
from discord.ext import commands
import aiohttp
from keep_alive import app
import random
from flask.views import MethodView
from flask import request
import pathlib
import re
import traceback
import asyncio
import utils
from typing import Union
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

    @commands.command(brief='Returns military statistics', help='Displays information about rebuys, warchests, mmr and ongoing wars for the Church and Convent.')
    @commands.has_any_role('Deacon', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def milcheck(self, ctx):
        async with aiohttp.ClientSession() as session:
            message = await ctx.send('Hang on...')
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:500 alliance_id:4729){{data{{id leader_name nation_name alliance_id color alliance_position num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available offensive_wars{{winner turnsleft}} defensive_wars{{winner turnsleft}} cities{{infrastructure barracks factory airforcebase drydock}}}}}}}}"}) as temp:
                nations = (await temp.json())['data']['nations']['data']
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={convent_key}", json={'query': f"{{nations(page:1 first:500 alliance_id:7531){{data{{id leader_name nation_name alliance_id color alliance_position num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available offensive_wars{{winner turnsleft}} defensive_wars{{winner turnsleft}} cities{{infrastructure barracks factory airforcebase drydock}}}}}}}}"}) as temp:
                nations += (await temp.json())['data']['nations']['data']

        fields2 = []
        fields3 = []
        fields4 = []
        fields5 = []

        for x in nations:
            if x['alliance_position'] == "APPLICANT":
                continue
            
            person = utils.find_user(self, x['id'])
            if not person:
                continue
            user = ctx.guild.get_member(person['user'])
            if not user:
                continue

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
                    {'name': user, 'value': rebuy})
            

            avg_bar = (barracks / x['num_cities'])
            avg_fac = (factories / x['num_cities'])
            avg_han = (hangars / x['num_cities'])
            avg_dry = (drydocks / x['num_cities'])

            fields3.append(
                {'name': user, 'value': f'Average improvements:\n{round(avg_bar, 1)}/{round(avg_fac, 1)}/{round(avg_han, 1)}/{round(avg_dry, 1)}'})
            
            city_count = x['num_cities']
            fields4.append({'name': user, 'value': f"Warchest:\nMoney: ${round(float(x['money']) / 1000000)}M/${round(city_count * 500000 / 1000000)}M\nMunis: {round(float(x['munitions']) / 1000)}k/{round(city_count * 361.2 / 1000)}k\nGas: {round(float(x['gasoline']) / 1000)}k/{round(city_count * 320.25 / 1000)}k\nSteel: {round(float(x['steel']) / 1000)}k/{round(city_count * 619.5 / 1000)}k\n Alum: {round(float(x['aluminum']) / 1000)}k/{round(city_count * 315 / 1000)}k"})

            offensive_used_slots = 0
            for war in x['offensive_wars']:
                if war['turnsleft'] > 0:
                    offensive_used_slots += 1

            defensive_used_slots = 0
            for war in x['defensive_wars']:
                if war['turnsleft'] > 0:
                    defensive_used_slots += 1

            fields5.append(
                {'name': user, 'value': f"Offensive: {offensive_used_slots} wars\nDefensive: {defensive_used_slots} wars"})

        embeds1 = utils.embed_pager("Rebuy", fields2)
        embeds2 = utils.embed_pager("MMR", fields3)
        embeds3 = utils.embed_pager("Warchest", fields4)
        embeds4 = utils.embed_pager("Slots", fields5)

        await message.edit(content="", embed=embeds1[0])
        asyncio.create_task(utils.reaction_checker(self, message, embeds1))
        message2 = await ctx.send(content="", embed = embeds2[0])
        asyncio.create_task(utils.reaction_checker(self, message2, embeds2))
        message3 = await ctx.send(content="", embed = embeds3[0])
        asyncio.create_task(utils.reaction_checker(self, message3, embeds3))
        message4 = await ctx.send(content="", embed = embeds4[0])
        asyncio.create_task(utils.reaction_checker(self, message4, embeds4))

    @commands.command(brief='Delete all threads in this channel.', help="Deletes any active thread in the channel the command was called.")
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def clear_threads(self, ctx):
        for thread in ctx.channel.threads:
            await thread.delete()
        print("done")
        return

    @commands.command(
        brief="Status of someone's ongoing wars.",
        aliases=['s'],
        help="Can be used without arguments in a war thread, or you can supply an argument to get the warring status of the supplied nation."
    )
    @commands.has_any_role('Pupil', 'Zealot', 'Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def status(self, ctx, arg=None):
        with open ('./data/attachments/marching.gif', 'rb') as gif:
            gif = discord.File(gif)
        message = await ctx.send(content="*Thinking...*", file=gif)
        if not arg:
            if isinstance(ctx.channel, discord.Thread) and "(" in ctx.channel.name and ")" in ctx.channel.name:
                nation_id = ctx.channel.name[ctx.channel.name.rfind("(")+1:-1]
                int(nation_id) # throw an error if not a number
            else:
                try:
                    person = utils.find_user(self, ctx.author.id)
                    nation_id = person['nationid']
                except:
                    await ctx.send("I do not know who to find the status of.")
                    return
        else:
            person = await utils.find_nation_plus(self, arg)
            nation_id = str(person['nationid'])

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation_id}){{data{{nation_name leader_name id alliance{{name}} cities{{barracks factory airforcebase drydock}} population score last_active beigeturns vmode pirate_economy color dompolicy alliance_id num_cities soldiers tanks aircraft ships missiles nukes offensive_wars{{defender{{nation_name leader_name alliance_id alliance{{name}} cities{{barracks factory airforcebase drydock}} id pirate_economy score last_active beigeturns vmode num_cities color defensive_wars{{turnsleft}} offensive_wars{{turnsleft}} soldiers tanks aircraft ships nukes missiles}} date id attid winner att_resistance def_resistance attpoints defpoints attpeace defpeace war_type groundcontrol airsuperiority navalblockade turnsleft att_fortify def_fortify}} defensive_wars{{attacker{{nation_name leader_name alliance_id alliance{{name}} id cities{{barracks factory airforcebase drydock}} pirate_economy score last_active beigeturns vmode num_cities color defensive_wars{{turnsleft}} offensive_wars{{turnsleft}} soldiers tanks aircraft ships nukes missiles}} date id attid winner att_resistance def_resistance attpoints defpoints attpeace defpeace war_type groundcontrol airsuperiority navalblockade turnsleft att_fortify def_fortify}}}}}}}}"}) as temp:
                try:
                    nation = (await temp.json())['data']['nations']['data'][0]
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
        embed.set_footer(text="_________________________________\nThe winrate is the chance for the nation in question to win a ground/air/naval roll against the main enemy. Battles consists of 3 rolls. A percentage abvove 50 is good. Use $battlesim for more detailed battle predictions.")
        embed1.set_footer(text="_________________________________\nThe winrate is the chance for the nation in question to win a ground/air/naval roll against the main enemy. Battles consists of 3 rolls. A percentage abvove 50 is good. Use $battlesim for more detailed battle predictions.")
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
                    break

        asyncio.create_task(reaction_checker())

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def war_scanner(self, ctx):
        await self.wars()

    async def add_to_thread(self, thread, atom_id: Union[str, int], atom: dict = None):
        #print("adding", atom)
        person = utils.find_user(self, atom_id)
        if person == {}:
            print("tried to add, but could not find", atom_id)
            if atom:
                await thread.send(f"I was unable to add {atom['leader_name']} of {atom['nation_name']} to the thread. Have they not linked their nation with their discord account?")
            else:
                await thread.send(f"I was unable to add nation {atom_id} from the thread. Have they not linked their nation with their discord account?")
            return
        user = await self.bot.fetch_user(person['user'])
        try:
            await thread.add_user(user)
        except Exception as e:
            await thread.send(f"I was unable to add {user} to the thread.\n```{e}```")
    
    async def remove_from_thread(self, thread, atom_id: Union[str, int], atom: dict = None):
        #print("removing ", atom)
        person = utils.find_user(self, atom_id)
        if person == {}:
            print("tried to remove, but could not find", atom_id)
            if atom:
                await thread.send(f"I was unable to remove {atom['leader_name']} of {atom['nation_name']} from the thread. Have they not linked their nation with their discord account?")
            else:
                await thread.send(f"I was unable to remove nation {atom_id} from the thread. Have they not linked their nation with their discord account?")
            return
        user = await self.bot.fetch_user(person['user'])
        try:
            await thread.remove_user(user)
        except:
            await thread.send(f"I was unable to remove {user} from the thread.")

    async def wars(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(923249186500116560) ## 923249186500116560
        debug_channel = self.bot.get_channel(739155202640183377)
        prev_wars = None

        async def cthread(war, non_atom, atom):
            attack_logs = {"id": war['id'], "attacks": [], "detected": datetime.utcnow(), "finished": False}
            mongo.war_logs.insert_one(attack_logs)

            url = f"https://politicsandwar.com/nation/war/timeline/war={war['id']}"
            embed = discord.Embed(title=f"New {war['war_type'].lower().capitalize()} War", url=url, description=f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) declared a{'n'[:(len(war['war_type'])-5)^1]} {war['war_type'].lower()} war on [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']})", color=0x2F3136)
            name = f"{non_atom['nation_name']} ({non_atom['id']})"
            found = False

            for thread in channel.threads:
                if f"({non_atom['id']})" in thread.name:
                    found = True
                    matching_thread = thread
                    break
            if not found:
                message = await channel.send(embed=embed)
                try:
                    thread = await channel.create_thread(name=name, message=message, auto_archive_duration=4320, type=discord.ChannelType.private_thread, reason="War declaration")
                except:
                    thread = await channel.create_thread(name=name, message=message, auto_archive_duration=1440, type=discord.ChannelType.private_thread, reason="War declaration")
                await self.add_to_thread(thread, atom['id'], atom)
            elif found:
                await matching_thread.send(embed=embed)
                await self.add_to_thread(matching_thread, atom['id'], atom)

            return attack_logs

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
            else:
                attacker = [new_war['attacker']['id'], new_war['defender']['id']]
                attacker.remove(attack['victor'])
                attacker = attacker[0]
            return attacker

        async def smsg(attacker_id, attack, war, atom, non_atom, peace):
            embed = discord.Embed(title=f"New {war['war_type'].lower().capitalize()} War", description=f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) declared a{'n'[:(len(war['war_type'])-5)^1]} {war['war_type'].lower()} war on [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']})", color=0x2F3136)
            
            for thread in channel.threads:
                if f"({non_atom['id']})" in thread.name:
                    url = f"https://politicsandwar.com/nation/war/timeline/war={war['id']}"
                    if peace != None:
                        embed = discord.Embed(title="Peace offering", url=url, description=f"[{peace['offerer']['nation_name']}](https://politicsandwar.com/nation/id={peace['offerer']['id']}) is offering peace to [{peace['reciever']['nation_name']}](https://politicsandwar.com/nation/id={peace['reciever']['id']}). The peace offering will be canceled if either side performs an act of aggression.", color=0xffffff)
                        await thread.send(embed=embed)
                        break
                    footer = f"<t:{round(datetime.strptime(attack['date'], '%Y-%m-%d %H:%M:%S').timestamp())}:R> <t:{round(datetime.strptime(attack['date'], '%Y-%m-%d %H:%M:%S').timestamp())}>"
                    if attack['type'] != "FORTIFY":
                        if attack['type'] in ["GROUND", "NAVAL", "AIRVINFRA", "AIRVSOLDIERS", "AIRVTANKS", "AIRVMONEY", "AIRVSHIPS", "AIRVAIR"]:
                            for nation in [war['attacker'], war['defender']]:
                                if nation['id'] == attacker_id:
                                    attacker_nation = nation
                                elif nation['id'] != attacker_id:
                                    defender_nation = nation

                            colors = [0xff0000, 0xffff00, 0xffff00, 0x00ff00]
                            if attacker_nation['id'] == non_atom['id']:
                                colors.reverse()

                            if attack['success'] == 3:
                                success = "Immense Triumph"
                            elif attack['success'] == 2:
                                success = "Moderate Success"
                            elif attack['success'] == 1:
                                success = "Pyrrhic Victory"
                            elif attack['success'] == 0:
                                success = "Utter Failure"

                            description = f"Success: {success}"

                            if attack['type'] == "GROUND":
                                title = "Ground battle"
                                att_casualties = f"{attack['attcas1']:,} soldiers\n{attack['attcas2']:,} tanks"
                                def_casualties = f"{attack['defcas1']:,} soldiers\n{attack['defcas2']:,} tanks"
                            elif attack['type'] == "NAVAL":
                                title = "Naval Battle"
                                att_casualties = f"{attack['attcas1']:,} ships"
                                def_casualties = f"{attack['defcas1']:,} ships"
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

                            embed = discord.Embed(title=title, description=description, color=colors[attack['success']], url=url)
                            embed.add_field(name=f"Attacker", value=f"[{attacker_nation['nation_name']}](https://politicsandwar.com/nation/id={attacker_nation['id']})\n{aaa_link}\n\n**Casualties**:\n{att_casualties}")
                            embed.add_field(name=f"Defender", value=f"[{defender_nation['nation_name']}](https://politicsandwar.com/nation/id={defender_nation['id']})\n{daa_link}\n\n**Casualties**:\n{def_casualties}")
                            embed.add_field(name="\u200b", value=footer, inline=False)
                            await thread.send(embed=embed)
                            mongo.war_logs.find_one_and_update({"id": war['id']}, {"$push": {"attacks": attack['id']}})
                            break
                        elif attack['type'] in ["PEACE", "VICTORY", "ALLIANCELOOT", "EXPIRATION"]:
                            if attack['type'] == "PEACE":
                                title = "White peace"
                                color = 0xffFFff
                                content = f"The peace offer was accepted, and [{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) is no longer fighting an offensive war against [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']})."
                            elif attack['type'] == "VICTORY":
                                if attack['victor'] == atom['id']:
                                    title = "Victory"
                                    color = 0x00ff00
                                else:
                                    title = "Defeat"
                                    color = 0xff0000
                                loot = attack['loot_info'].replace('\r\n                            ', '')
                                content = f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) is no longer fighting an offensive war against [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']}).\n\n{loot}"
                            elif attack['type'] == "ALLIANCELOOT":
                                if atom['nation_name'] in attack['loot_info']:
                                    color = 0x00ff00
                                else:
                                    color = 0xff0000
                                title = "Alliance loot"
                                loot = attack['loot_info'].replace('\r\n                            ', '')
                                content = f"{loot}"
                            elif attack['type'] == "EXPIRATION":
                                title = "War expiration"
                                color = 0xffFFff
                                content = f"The war has lasted 5 days, and has consequently expired. [{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) is no longer fighting an offensive war against [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']})."
                            embed = discord.Embed(title=title, url=url, description=content, color=color)
                            embed.add_field(name="\u200b", value=footer, inline=False)
                            await thread.send(embed=embed)
                            mongo.war_logs.find_one_and_update({"id": war['id']}, {"$push": {"attacks": attack['id']}})
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
                        
                            embed = discord.Embed(title=title, url=url, description=content, color=colors[attack['success']])
                            embed.add_field(name="\u200b", value=footer, inline=False)
                            await thread.send(embed=embed)
                            mongo.war_logs.find_one_and_update({"id": war['id']}, {"$push": {"attacks": attack['id']}})
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
                        
                        embed = discord.Embed(title="Fortification", url=url, description=content, color=color)
                        embed.add_field(name="\u200b", value=footer, inline=False)
                        await thread.send(embed=embed)
                        mongo.war_logs.find_one_and_update({"id": war['id']}, {"$push": {"attacks": attack['id']}})
                        break

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] days_ago:5 active:true){{id att_fortify war_type def_fortify attpeace defpeace turnsleft attacker{{nation_name leader_name alliance{{name}} id num_cities alliance_id cities{{id}}}} defender{{nation_name leader_name alliance{{name}} id num_cities alliance_id cities{{id}}}} attacks{{type id date loot_info victor moneystolen success cityid resistance_eliminated infradestroyed infra_destroyed_value improvementslost attcas1 attcas2 defcas1 defcas2}}}}}}"}) as temp:
                        try:
                            wars = (await temp.json())['data']['wars']
                        except:
                            print((await temp.json())['errors'])
                            await asyncio.sleep(60)
                            continue
                        if prev_wars == None:
                            prev_wars = wars
                            continue
                    async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] days_ago:5 active:false){{id att_fortify war_type def_fortify attpeace defpeace turnsleft attacker{{nation_name leader_name alliance{{name}} id num_cities alliance_id cities{{id}}}} defender{{nation_name leader_name alliance{{name}} id num_cities alliance_id cities{{id}}}} attacks{{type id date loot_info victor moneystolen success cityid resistance_eliminated infradestroyed infra_destroyed_value improvementslost attcas1 attcas2 defcas1 defcas2}}}}}}"}) as temp1:
                        try:
                            temp1 = (await temp1.json())['data']['wars']
                            done_wars = []
                            for war in temp1:
                                if war['turnsleft'] <= 0:
                                    done_wars.append(war)
                        except:
                            print((await temp1.json())['errors'])
                            await asyncio.sleep(60)
                            continue
                    for new_war in wars:
                        if new_war['attacker']['alliance_id'] in ['4729', '7531']: ## CHANGE T0 ATOM ---------------------------------------------------------
                            atom = new_war['attacker']
                            non_atom = new_war['defender']
                        else:
                            atom = new_war['defender']
                            non_atom = new_war['attacker']
                        attack_logs = mongo.war_logs.find_one({"id": new_war['id']})
                        if not attack_logs:
                            attack_logs = await cthread(new_war, non_atom, atom)
                        for old_war in prev_wars:
                            if new_war['id'] == old_war['id']:
                                if new_war['attpeace'] and not old_war['attpeace']:
                                    peace_obj = {"offerer": new_war['attacker'], "reciever": new_war['defender']}
                                    await smsg(None, None, new_war, atom, non_atom, peace_obj)
                                elif new_war['defpeace'] and not old_war['defpeace']:
                                    peace_obj = {"offerer": new_war['defender'], "reciever": new_war['attacker']}
                                    await smsg(None, None, new_war, atom, non_atom, peace_obj)
                                break
                        for attack in new_war['attacks']:
                            if attack['id'] not in attack_logs['attacks']:
                                attacker = await attack_check(attack, new_war)
                                await smsg(attacker, attack, new_war, atom, non_atom, None)
                    for done_war in done_wars:
                        if done_war['attacker']['alliance_id'] in ['4729', '7531']: ## CHANGE T0 ATOM ---------------------------------------------------------
                            atom = done_war['attacker']
                            non_atom = done_war['defender']
                        else:
                            atom = done_war['defender']
                            non_atom = done_war['attacker']
                        attack_logs = mongo.war_logs.find_one({"id": done_war['id']})
                        if not attack_logs:
                            attack_logs = await cthread(done_war, non_atom, atom)
                        elif attack_logs['finished']:
                            continue
                        for attack in done_war['attacks']:
                            if attack['id'] not in attack_logs['attacks']:
                                attacker = await attack_check(attack, done_war)
                                await smsg(attacker, attack, done_war, atom, non_atom, None)
                        if done_war['attacks'][-1]['type'] not in ["PEACE", "VICTORY", "ALLIANCELOOT"]:
                            attack = {"type": "EXPIRATION", "id": -1, "date": datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M:%S')}
                            await smsg(None, attack, done_war, atom, non_atom, None)
                        for thread in channel.threads:
                            if f"({non_atom['id']})" in thread.name:
                                await self.remove_from_thread(thread, atom['id'], atom)
                                if thread.member_count <= 1:
                                    await thread.edit(archived=True)
                                mongo.war_logs.find_one_and_update({"id": done_war['id']}, {"$set": {"finished": True}})
                                break
                prev_wars = wars
                await asyncio.sleep(60)
            except:
                await debug_channel.send(f"I encountered an error whilst scanning for wars:```{traceback.format_exc()}```")

    @commands.command(
        brief='Add someone to the military coordination thread.',
        help="Must be used in a thread. Very wasteful command, since you can also add people by pinging them."
        )
    @commands.has_any_role('Pupil', 'Zealot', 'Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def add(self, ctx, *, user):
        await self.add_to_thread(ctx.channel, user)

    @commands.command(
        brief='Remove someone from the military coordination thread.',
        help="Must be used in a thread. Supply the user you wish to remove from the thread."
        )
    @commands.has_any_role('Deacon', 'Advisor', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def remove(self, ctx, *, user):
        await self.remove_from_thread(ctx.channel, user)

    @commands.command(
        aliases=['counter'],
        brief='Accepts one argument, gives you a pre-filled link to slotter.',
        help='Accepted arguments include nation name, leader name, nation id and nation link. When browsing the databse, Fuquiem will use the first match, so it can be wise to double check that it returns a slotter link for the correct person.'
        )
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

    @commands.command(
        aliases=['spherecounters'],
        brief='Accepts one argument, gives you a pre-filled link to slotter.',
        help='Accepted arguments include nation name, leader name, nation id and nation link. When browsing the databse, Fuquiem will use the first match, so it can be wise to double check that it returns a slotter link for the correct person.'
        )
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

    @commands.command(
        aliases=['target'],
        brief='Sends you a pre-filled link to slotter',
        help="Lets you find the easiest targets during a global war."
        )
    async def targets(self, ctx):
        await ctx.send('This command has been disabled.')
        return
        person = utils.find_user(self, ctx.author.id)
        embed = discord.Embed(title="Targets",
                              description=f"[Explore targets on slotter](https://slotter.bsnk.dev/search?nation={person['nationid']}&alliances=7452,8841,8624,9000,7450,6088,7306,4648,9187,8335,5476,8594&countersMode=false&threatsMode=false&vm=false&grey=true&beige=false)", color=0x00ff00)
        await ctx.send(embed=embed)

    @commands.command(
        aliases=['wc'],
        brief="Sends a warchest top up to the people in need",
        help="Requires admin perms, sends people the resources they need in addition to telling people what to deposit."
        )
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

            await self.top_up(ctx, aa['nations'])
            await ctx.send("Finished!")
                    
    @commands.command(
        brief="Sends a warchest top up to the specified person",
        help="Requires admin perms. It's basically the $warchest command, but it's limited to the person you specified."
        )
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def resupply(self, ctx, *, arg):
        async with aiohttp.ClientSession() as session:
            person = utils.find_user(self, arg)

            async with session.get(f"http://politicsandwar.com/api/nation/id={person['nationid']}&key={api_key}") as temp:
                nation = (await temp.json())
            if nation['allianceid'] == '4729':
                async with session.get(f"http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}") as temp1:
                    aa = (await temp1.json())
            elif nation['allianceid'] == '7531':
                async with session.get(f"http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}") as temp2:
                    aa = (await temp2.json())
            else:
                await ctx.send(content="They are not in CoA.")

            for member in aa['nations']:
                if str(member['nationid']) == nation['nationid']:
                    nation = member
                    break

            await self.top_up(ctx, [nation])
            await ctx.send("Finished!")

    async def top_up(self, ctx, nations: list):
        randy = utils.find_user(self, 465463547200012298)
        if len(randy['email']) <= 1 or len(randy['pwd']) <= 1:
            await ctx.send(content="<@465463547200012298>'s credentials are wrong?")
        async with aiohttp.ClientSession() as session:            
            for nation in nations:
                try:
                    if int(nation['vacmode']) > 0:
                        continue
                    city_count = nation['cities']
                    user = None
                    excess = ""
                    person = utils.find_user(self, 465463547200012298)
                    minmoney = round(city_count * 500000 - float(nation['money']))
                    maxmoney = round(city_count * 500000 * 3 - float(nation['money']))
                    if maxmoney < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_money=" + str(round(abs(city_count * 500000 * 2 - float(nation['money']))))
                    if minmoney < 0:
                        minmoney = 0
                    mingasoline = round(city_count * 320.25 - float(nation['gasoline']))
                    maxgasoline = round(city_count * 320.25 * 3 - float(nation['gasoline']))
                    if maxgasoline < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_gasoline=" + str(round(abs(city_count * 320.25 * 2 - float(nation['gasoline']))))
                    if mingasoline < 0:
                        mingasoline = 0
                    minmunitions = round(city_count * 361.2 - float(nation['munitions']))
                    maxmunitions = round(city_count * 361.2 * 3 - float(nation['munitions']))
                    if maxmunitions < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_munitions=" + str(round(abs(city_count * 361.2 * 2 - float(nation['munitions']))))
                    if minmunitions < 0:
                        minmunitions = 0
                    minsteel = round(city_count * 619.5 - float(nation['steel']))
                    maxsteel = round(city_count * 619.5 * 3 - float(nation['steel']))
                    if maxsteel < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_steel=" + str(round(abs(city_count * 619.5 * 2 - float(nation['steel']))))
                    if minsteel < 0:
                        minsteel = 0
                    minaluminum = round(city_count * 315 - float(nation['aluminum']))
                    maxaluminum = round(city_count * 315 * 3 - float(nation['aluminum']))
                    if maxaluminum < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_aluminum=" + str(round(abs(city_count * 315 * 2 - float(nation['aluminum']))))
                    if minaluminum < 0:
                        minaluminum = 0

                    if excess:
                        try:
                            if user == None:
                                pass
                            else:
                                await user.send(f"Hey, you have an excess of resources! Please use this pre-filled link to deposit the resources for safekeeping: <https://politicsandwar.com/alliance/id={nation['allianceid']}&display=bank{excess}>")
                                await ctx.send(f"Sent a message to {user}")
                        except discord.Forbidden:
                            await ctx.send(f"{user} does not allow my DMs")
                        except:
                            await ctx.send(f"cannot message {nation['nation']} yet they did not block me")
                    
                    if minmoney == 0 and mingasoline == 0 and minmunitions == 0 and minsteel == 0 and minaluminum == 0:
                        continue

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
                        success = False
                        async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={person['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                            txids = await txids.json()
                        for x in txids['data']:
                            if x['note'] == 'Resupplying warchest' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                                success = True
                        if success:
                            await ctx.send(f"I can confirm that the transaction to **{nation['nation']} ({nation['leader']})** has successfully commenced.")
                        else:
                            await ctx.send(f"<@465463547200012298> the transaction to **{nation['nation']} ({nation['leader']})** might have failed. Check this page to be sure:\nhttps://politicsandwar.com/nation/id={nation['nationid']}&display=bank")
                except Exception as e:
                    print(e)
                    await ctx.send(e)
            
    async def spies_msg(self): #enable in times of war
        return
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': "{nations(page:1 first:500 alliance_id:4729 vmode:false){data{id leader_name nation_name score warpolicy spies cia spy_satellite espionage_available}}}"}) as temp:
                church = (await temp.json())['data']['nations']['data']
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={convent_key}', json={'query': "{nations(page:1 first:500 alliance_id:7531 vmode:false){data{id leader_name nation_name score warpolicy spies cia spy_satellite espionage_available}}}"}) as temp:
                convent = (await temp.json())['data']['nations']['data']
            sum = church + convent
            for member in sum:
                if member['espionage_available']:
                    person = utils.find_user(self, member['id'])
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

    @commands.command(brief='Manually update the #threats channel')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def check_wars(self, ctx):
        await self.wars_check()
        await ctx.send(f'Done!')
        # merely a debugging command

    async def wars_check(self):
        async with aiohttp.ClientSession() as session:
            channel = self.bot.get_channel(842116871322337370) ## 842116871322337370
            await channel.purge()
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] days_ago:5 active:true){{id att_resistance def_resistance attacker{{nation_name score beigeturns alliance_position alliance{{name}} id num_cities alliance_id defensive_wars{{turnsleft}}}} defender{{nation_name score beigeturns alliance_position alliance{{name}} id num_cities alliance_id defensive_wars{{turnsleft}}}}}}}}"}) as temp:
                try:
                    wars = (await temp.json())['data']['wars']
                except:
                    print("not finding threaths", (await temp.json())['errors'])
                    return

            enemy_list = []
            for war in wars:
                if war['attacker']['alliance_id'] in ['4729', '7531']:
                    atom = war['attacker']
                    non_atom = war['defender']
                    non_atom['atom_res'] = war['att_resistance']
                    non_atom['non_atom_res'] = war['def_resistance']
                    non_atom['status'] = "defender"
                elif war['defender']['alliance_id'] in ['4729', '7531']:
                    atom = war['defender']
                    non_atom = war['attacker']
                    non_atom['atom_res'] = war['def_resistance']
                    non_atom['non_atom_res'] = war['att_resistance']
                    non_atom['status'] = "attacker"
                else:
                    continue

                if not non_atom['alliance']:
                    continue

                non_atom['currently_fighting'] = atom['alliance_position']

                to_append = {"id": non_atom['id'], "engagements": [non_atom]}
                
                found = next((elem for elem in enemy_list if elem['id'] == non_atom['id']), None)
                if not found:
                    def_wars = 0
                    for war in non_atom['defensive_wars']:
                        if war['turnsleft'] > 0:
                            def_wars += 1
                    to_append['def_wars'] = def_wars
                    enemy_list.append(to_append)
                else:
                    enemy_list.remove(found)
                    found["engagements"].append(non_atom)
                    enemy_list.append(found)

            await channel.send("~~strikethrough~~ = this person is merely fighting our applicants\n\❗ = a follower of atom is currently losing against this opponent\n\⚔️ = this person is fighting offensive wars against atom\n\🛡️ = this person is fighting defensive wars against atom\n🟢 = you are able to attack this person\n🟡 = this person is in beige\n🔴 = this person is fully slotted")
            enemy_list = sorted(enemy_list, key=lambda k: k['engagements'][0]['score'])
            
            content = ""
            n = 0
            for enemy in enemy_list:
                n += 1
                circle = '🟢'
                exclamation = ''
                sword = ''
                shield = ''
                str_start = '~~'
                str_end = '~~'
                applicant = ''
                if enemy['def_wars'] == 3:
                    circle = '🔴'
                for engagement in enemy['engagements']:
                    if engagement['alliance_position'] == "APPLICANT":
                        applicant = ' (Applicant)'
                    if engagement['non_atom_res'] > engagement['atom_res']: 
                        exclamation = '\❗'
                    if engagement['beigeturns'] > 0 and circle != '🔴':
                        circle = '🟡'
                    if engagement['currently_fighting'] != "APPLICANT":
                        str_start = ''
                        str_end = ''
                    if engagement['status'] == "attacker":
                        sword = '\⚔️'
                    elif engagement['status'] == "defender":
                        shield = '\🛡️'

                minscore = round(engagement['score'] / 1.75)
                maxscore = round(engagement['score'] / 0.75)
                content += f"{str_start}Priority target! {sword}{shield}{exclamation}{circle} Defensive range: {minscore} - {maxscore} <https://politicsandwar.com/nation/id={enemy['id']}>, {engagement['alliance']['name']}{applicant}{str_end}\n"
                if n % 10 == 0:
                    await channel.send(content)
                    content = ""
            if len(content) > 0:
                await channel.send(content)
            

    @commands.command(brief='Change the global mmr setting')
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

    @commands.command(
        brief='Find raid targets',
        aliases=['raid'],
        help="When going through the setup wizard, you can choose to get the results on discord or as a webpage. If you decide to get the targets on discord, you will be able to react with the arrows in order to view different targets. You can also type 'page 62' to go nation number 62. This will of course work for any number. By reacting with the clock, you will add a beige reminder for the nation if they are in beige. Fuquiem will then DM you when the nation exits beige. You can use $reminders to view active reminders. If you choose to get the targets on a webpage, you will get a link to a page with a table. The table will include all nations that match the criteria you specified in the wizard. If you want beige reminders, there is a 'remind me'-button for every nation currently in beige. You can press the table headers to sort by different attributes. By default it's sorted by monetary net income."
        )
    @commands.has_any_role('Pupil', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def raids(self, ctx, *, arg=None):
        invoker = str(ctx.author.id)
        async with aiohttp.ClientSession() as session:
            message = await ctx.send('Finding person...')
            if arg == None:
                arg = ctx.author.id
            attacker = utils.find_user(self, arg)
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

            temp, colors, prices, treasures, radiation, seasonal_mod = await utils.pre_revenue_calc(api_key, message, query_for_nation=False, parsed_nation=atck_ntn)

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

                rev_obj = await utils.revenue_calc(message, target, radiation, treasures, prices, colors, seasonal_mod)

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

    @commands.command(
        aliases=['bsim', 'bs'],
        brief='Simulate battles between two nations',
        help="Accepts up to two arguments. The first argument is the attacking nation, whilst the latter is the defending nation. If only one argument is provided, Fuquiem will assume that you are the defender. If no arguments are provided, it will assume you are attacking yourself. If it is used in a war thread, it will use the enemy in the thread as the defender if you have not supplied any other defender."
        )
    @commands.has_any_role('Pupil', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def battlesim(self, ctx, nation1=None, nation2=None):
        #check is any wars are active, and if they have air superiority, ground control, fortified etc
        message = await ctx.send('Alright, give me a sec to calculate the winrates...')
        if nation1 == None:
            nation1 = ctx.author.id
        nation1_nation = utils.find_user(self, nation1)
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
            nation2_nation = utils.find_user(self, nation2)
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

        embed = discord.Embed(title="Battle Simulator", description=f"These are the results for when [{results['nation1']['nation_name']}](https://politicsandwar.com/nation/id={results['nation1']['id']}){results['nation1_append']} attacks [{results['nation2']['nation_name']}](https://politicsandwar.com/nation/id={results['nation2']['id']}){results['nation2_append']}\nIf you want to use custom troop counts, you can use the [in-game battle simulators](https://politicsandwar.com/tools/)", color=0x00ff00)
        embed1 = discord.Embed(title="Battle Simulator", description=f"These are the results for when [{results['nation2']['nation_name']}](https://politicsandwar.com/nation/id={results['nation2']['id']}){results['nation2_append']} attacks [{results['nation1']['nation_name']}](https://politicsandwar.com/nation/id={results['nation1']['id']}){results['nation1_append']}\nIf you want to use custom troop counts, you can use the [in-game battle simulators](https://politicsandwar.com/tools/)", color=0x00ff00)

        if results['nation2']['soldiers'] + results['nation2']['tanks'] + results['nation1']['soldiers'] + results['nation1']['tanks'] == 0:
            embed.add_field(name="Ground Attack", value="Nobody has any forces!")
            embed1.add_field(name="Ground Attack", value="Nobody has any forces!")
        else:
            embed.add_field(name="Ground Attack", value=f"Immense Triumph: {round(results['nation1_ground_it']*100)}%\nModerate Success: {round(results['nation1_ground_mod']*100)}%\nPyrrhic Victory: {round(results['nation1_ground_pyr']*100)}%\nUtter Failure: {round(results['nation1_ground_fail']*100)}%")
            embed1.add_field(name="Ground Attack", value=f"Immense Triumph: {round(results['nation2_ground_it']*100)}%\nModerate Success: {round(results['nation2_ground_mod']*100)}%\nPyrrhic Victory: {round(results['nation2_ground_pyr']*100)}%\nUtter Failure: {round(results['nation2_ground_fail']*100)}%")
        
        if results['nation2']['aircraft'] + results['nation1']['aircraft'] != 0:
            embed.add_field(name="Airstrike", value=f"Immense Triumph: {round(results['nation1_air_it']*100)}%\nModerate Success: {round(results['nation1_air_mod']*100)}%\nPyrrhic Victory: {round(results['nation1_air_pyr']*100)}%\nUtter Failure: {round(results['nation1_air_fail']*100)}%")
            embed1.add_field(name="Airstrike", value=f"Immense Triumph: {round(results['nation1_air_fail']*100)}%\nModerate Success: {round(results['nation1_air_pyr']*100)}%\nPyrrhic Victory: {round(results['nation1_air_mod']*100)}%\nUtter Failure: {round(results['nation1_air_it']*100)}%")
        else:
            embed.add_field(name="Airstrike", value="Nobody has any forces!")
            embed1.add_field(name="Airstrike", value="Nobody has any forces!")

        if results['nation2']['ships'] + results['nation1']['ships'] != 0:
            embed.add_field(name="Naval Battle", value=f"Immense Triumph: {round(results['nation1_naval_it']*100)}%\nModerate Success: {round(results['nation1_naval_mod']*100)}%\nPyrrhic Victory: {round(results['nation1_naval_pyr']*100)}%\nUtter Failure: {round(results['nation1_naval_fail']*100)}%")
            embed1.add_field(name="Naval Battle", value=f"Immense Triumph: {round(results['nation1_naval_fail']*100)}%\nModerate Success: {round(results['nation1_naval_pyr']*100)}%\nPyrrhic Victory: {round(results['nation1_naval_mod']*100)}%\nUtter Failure: {round(results['nation1_naval_it']*100)}%")

        else:
            embed.add_field(name="Naval Battle", value="Nobody has any forces!")
            embed1.add_field(name="Naval Battle", value="Nobody has any forces!")

        embed.add_field(name="Casualties", value=f"Att. Sol.: {results['nation1_ground_nation1_avg_soldiers']:,} ± {results['nation1_ground_nation1_diff_soldiers']:,}\nAtt. Tnk.: {results['nation1_ground_nation1_avg_tanks']:,} ± {results['nation1_ground_nation1_diff_tanks']:,}\n\nDef. Sol.: {results['nation1_ground_nation2_avg_soldiers']:,} ± {results['nation1_ground_nation2_diff_soldiers']:,}\nDef. Tnk.: {results['nation1_ground_nation2_avg_tanks']:,} ± {results['nation1_ground_nation2_diff_tanks']:,}\n\n{results['nation2']['aircas']}")        
        embed1.add_field(name="Casualties", value=f"Att. Sol.: {results['nation2_ground_nation2_avg_soldiers']:,} ± {results['nation2_ground_nation2_diff_soldiers']:,}\nAtt. Tnk.: {results['nation2_ground_nation2_avg_tanks']:,} ± {results['nation2_ground_nation2_diff_tanks']:,}\n\nDef. Sol.: {results['nation2_ground_nation1_avg_soldiers']:,} ± {results['nation2_ground_nation1_diff_soldiers']:,}\nDef. Tnk.: {results['nation2_ground_nation1_avg_tanks']:,} ± {results['nation2_ground_nation1_diff_tanks']:,}\n\n{results['nation1']['aircas']}")        
        
        embed.add_field(name="Casualties", value=f"*Targeting air:*\nAtt. Plane: {results['nation1_airtoair_nation1_avg']:,} ± {results['nation1_airtoair_nation1_diff']:,}\nDef. Plane: {results['nation1_airtoair_nation2_avg']:,} ± {results['nation1_airtoair_nation2_diff']:,}\n\n*Targeting other:*\nAtt. Plane: {results['nation1_airtoother_nation1_avg']:,} ± {results['nation1_airtoother_nation1_diff']:,}\nDef. Plane: {results['nation1_airtoother_nation2_avg']:,} ± {results['nation1_airtoother_nation2_diff']:,}\n\u200b")        
        embed1.add_field(name="Casualties", value=f"*Targeting air:*\nAtt. Plane: {results['nation2_airtoair_nation2_avg']:,} ± {results['nation2_airtoair_nation2_diff']:,}\nDef. Plane: {results['nation2_airtoair_nation1_avg']:,} ± {results['nation2_airtoair_nation1_diff']:,}\n\n*Targeting other:*\nAtt. Plane: {results['nation2_airtoother_nation2_avg']:,} ± {results['nation2_airtoother_nation2_diff']:,}\nDef. Plane: {results['nation2_airtoother_nation1_avg']:,} ± {results['nation2_airtoother_nation1_diff']:,}\n\u200b")        

        embed.add_field(name="Casualties", value=f"Att. Ships: {results['nation1_naval_nation1_avg']:,} ± {results['nation1_naval_nation1_diff']:,}\nDef. Ships: {results['nation1_naval_nation2_avg']:,} ± {results['nation1_naval_nation2_diff']:,}")        
        embed1.add_field(name="Casualties", value=f"Att. Ships: {results['nation2_naval_nation2_avg']:,} ± {results['nation2_naval_nation2_diff']:,}\nDef. Ships: {results['nation2_naval_nation1_avg']:,} ± {results['nation2_naval_nation1_diff']:,}")        

        embed.set_footer(text="_________________________\nIf the attacker gets an Utter Failure *and* consumes less munitions/gasoline than the amount predicted for the defender, the defender will consume the same amount of munitions and/or gasoline as the attacker.")
        embed1.set_footer(text="_________________________\nIf the attacker gets an Utter Failure *and* consumes less munitions/gasoline than the amount predicted for the defender, the defender will consume the same amount of munitions and/or gasoline as the attacker.")

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

    @commands.command(
        aliases=["dmg"],
        brief="Shows you how much damage each war attack would do",
        help="You can supply arguments just like what you'd do for $battlesim. It links to a page with some tables showing the damage dealt for each kind of attack."
        )
    async def damage(self, ctx, nation1=None, nation2=None):
        message = await ctx.send('Alright, give me a sec to calculate your mom...')
        if nation1 == None:
            nation1 = ctx.author.id
        nation1_nation = utils.find_user(self, nation1)
        if not nation1_nation:
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
            nation2_nation = utils.find_user(self, nation2)
            if not nation2_nation:
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
        endpoint = datetime.utcnow().strftime('%d%H%M%S%f')
        class webraid(MethodView):
            def get(raidclass):
                with open('./data/templates/damage.txt', 'r') as file:
                    template = file.read()
                result = Template(template).render(results=results)
                return str(result)
        app.add_url_rule(f"/damage/{endpoint}", view_func=webraid.as_view(str(datetime.utcnow())), methods=["GET", "POST"]) # this solution of adding a new page instead of updating an existing for the same nation is kinda dependent on the bot resetting every once in a while, bringing down all the endpoints
        await message.edit(content=f"Go to https://fuquiem.karemcbob.repl.co/damage/{endpoint}", attachments=[])

        
    async def battle_calc(self, nation1_id, nation2_id):
        results = {}

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation1_id}){{data{{nation_name population warpolicy id soldiers tanks aircraft ships irond vds cities{{infrastructure land}} defensive_wars{{groundcontrol airsuperiority navalblockade attpeace defpeace attid defid att_fortify def_fortify turnsleft war_type}} offensive_wars{{groundcontrol airsuperiority navalblockade attpeace defpeace attid defid att_fortify def_fortify turnsleft war_type}}}}}}}}"}) as temp:
                results['nation1'] = (await temp.json())['data']['nations']['data'][0]
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation2_id}){{data{{nation_name population warpolicy id soldiers tanks aircraft ships irond vds cities{{infrastructure land}}}}}}}}"}) as temp:
                results['nation2'] = (await temp.json())['data']['nations']['data'][0]

        results['nation1_append'] = ""
        results['nation2_append'] = ""
        results['nation1_tanks'] = 1
        results['nation2_tanks'] = 1
        results['nation1_extra_cas'] = 1
        results['nation2_extra_cas'] = 1
        results['gc'] = None
        results['nation1_war_infra_mod'] = 0.5
        results['nation2_war_infra_mod'] = 0.5
        results['nation1_war_loot_mod'] = 0.5
        results['nation2_war_loot_mod'] = 0.5

        for war in results['nation1']['defensive_wars'] + results['nation1']['offensive_wars']:
            if war['attid'] == nation2_id and war['turnsleft'] > 0 and war in results['nation1']['defensive_wars']:
                if war['groundcontrol'] == nation1_id:
                    results['gc'] = results['nation1']
                    results['nation1_append'] += "<:small_gc:924988666613489685>"
                elif war['groundcontrol'] == nation2_id:
                    results['gc'] = results['nation2']
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
                    results['nation2_append'] += "<:peace:926855240655990836>"
                elif war['defpeace']:
                    results['nation1_append'] += "<:peace:926855240655990836>"
                if war['war_type'] == "RAID":
                    results['nation2_war_infra_mod'] = 0.25
                    results['nation1_war_infra_mod'] = 0.5
                    results['nation2_war_loot_mod'] = 1
                    results['nation1_war_loot_mod'] = 1
                elif war['war_type'] == "ORDINARY":
                    results['nation2_war_infra_mod'] = 0.5
                    results['nation1_war_infra_mod'] = 0.5
                    results['nation2_war_loot_mod'] = 0.5
                    results['nation1_war_loot_mod'] = 0.5
                elif war['war_type'] == "ATTRITION":
                    results['nation2_war_infra_mod'] = 1
                    results['nation1_war_infra_mod'] = 1
                    results['nation2_war_loot_mod'] = 0.25
                    results['nation1_war_loot_mod'] = 0.5
            elif war['defid'] == nation2_id and war['turnsleft'] > 0 and war in results['nation1']['offensive_wars']:
                if war['groundcontrol'] == nation1_id:
                    results['gc'] = results['nation1']
                    results['nation1_append'] += "<:small_gc:924988666613489685>"
                elif war['groundcontrol'] == nation2_id:
                    results['gc'] = results['nation2']
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
                    results['nation1_append'] += "<:peace:926855240655990836>"
                elif war['defpeace']:
                    results['nation2_append'] += "<:peace:926855240655990836>"
                if war['war_type'] == "RAID":
                    results['nation1_war_infra_mod'] = 0.25
                    results['nation2_war_infra_mod'] = 0.5
                    results['nation1_war_loot_mod'] = 1
                    results['nation2_war_loot_mod'] = 1
                elif war['war_type'] == "ORDINARY":
                    results['nation1_war_infra_mod'] = 0.5
                    results['nation2_war_infra_mod'] = 0.5
                    results['nation1_war_loot_mod'] = 0.5
                    results['nation2_war_loot_mod'] = 0.5
                elif war['war_type'] == "ATTRITION":
                    results['nation1_war_infra_mod'] = 1
                    results['nation2_war_infra_mod'] = 1
                    results['nation1_war_loot_mod'] = 0.25
                    results['nation2_war_loot_mod'] = 0.5
        
        for attacker, defender in [("nation1", "nation2"), ("nation2", "nation1")]:
            defender_tanks_value = results[defender]['tanks'] * 40 * results[f'{defender}_tanks']
            defender_soldiers_value = results[defender]['soldiers'] * 1.75 + results[defender]['population'] * 0.0025
            defender_army_value = defender_soldiers_value + defender_tanks_value

            attacker_tanks_value = results[attacker]['tanks'] * 40 * results[f'{attacker}_tanks']
            attacker_soldiers_value = results[attacker]['soldiers'] * 1.75
            attacker_army_value = attacker_soldiers_value + attacker_tanks_value

            results[f'{attacker}_ground_win_rate'] = self.winrate_calc(attacker_army_value, defender_army_value)
            results[f'{attacker}_ground_it'] = results[f'{attacker}_ground_win_rate']**3
            results[f'{attacker}_ground_mod'] = results[f'{attacker}_ground_win_rate']**2 * (1 - results[f'{attacker}_ground_win_rate']) * 3
            results[f'{attacker}_ground_pyr'] = results[f'{attacker}_ground_win_rate'] * (1 - results[f'{attacker}_ground_win_rate'])**2 * 3
            results[f'{attacker}_ground_fail'] = (1 - results[f'{attacker}_ground_win_rate'])**3

            results[f'{attacker}_air_win_rate'] = self.winrate_calc((results[f'{attacker}']['aircraft'] * 3), (results[f'{defender}']['aircraft'] * 3))
            results[f'{attacker}_air_it'] = results[f'{attacker}_air_win_rate']**3
            results[f'{attacker}_air_mod'] = results[f'{attacker}_air_win_rate']**2 * (1 - results[f'{attacker}_air_win_rate']) * 3
            results[f'{attacker}_air_pyr'] = results[f'{attacker}_air_win_rate'] * (1 - results[f'{attacker}_air_win_rate'])**2 * 3
            results[f'{attacker}_air_fail'] = (1 - results[f'{attacker}_air_win_rate'])**3

            results[f'{attacker}_naval_win_rate'] = self.winrate_calc((results[f'{attacker}']['ships'] * 4), (results[f'{defender}']['ships'] * 4))
            results[f'{attacker}_naval_it'] = results[f'{attacker}_naval_win_rate']**3
            results[f'{attacker}_naval_mod'] = results[f'{attacker}_naval_win_rate']**2 * (1 - results[f'{attacker}_naval_win_rate']) * 3
            results[f'{attacker}_naval_pyr'] = results[f'{attacker}_naval_win_rate'] * (1 - results[f'{attacker}_naval_win_rate'])**2 * 3
            results[f'{attacker}_naval_fail'] = (1 - results[f'{attacker}_naval_win_rate'])**3
            
            if results['gc'] == results[attacker]:
                results[f'{attacker}_ground_{defender}_avg_aircraft'] = avg_air = min(results[f'{attacker}']['tanks'] * 0.0075 * results[f'{attacker}_ground_win_rate'] ** 3, results[defender]['aircraft'])
                results[defender]['aircas'] = f"Def. Plane: {avg_air} ± {round(results[f'{attacker}']['tanks'] * 0.0075 * (1 - results[f'{attacker}_ground_win_rate'] ** 3))}"
            else:
                results[defender]['aircas'] = ""
                results[f'{attacker}_ground_{defender}_avg_aircraft'] = 0
            
            for type, cas_rate in [("avg", 0.7), ("diff", 0.3)]:
                results[f'{attacker}_ground_{attacker}_{type}_soldiers'] = min(round(((defender_soldiers_value * 0.0084) + (defender_tanks_value * 0.0092)) * cas_rate * 3), results[attacker]['soldiers'])
                results[f'{attacker}_ground_{attacker}_{type}_tanks'] = min(round((((defender_soldiers_value * 0.0004060606) + (defender_tanks_value * 0.00066666666)) * results[f'{attacker}_ground_win_rate'] + ((defender_soldiers_value * 0.00043225806) + (defender_tanks_value * 0.00070967741)) * (1 - results[f'{attacker}_ground_win_rate'])) * cas_rate * 3), results[attacker]['tanks'])
                results[f'{attacker}_ground_{defender}_{type}_soldiers'] = min(round(((attacker_soldiers_value * 0.0084) + (attacker_tanks_value * 0.0092)) * cas_rate * 3), results[defender]['soldiers'])
                results[f'{attacker}_ground_{defender}_{type}_tanks'] = min(round((((attacker_soldiers_value * 0.00043225806) + (attacker_tanks_value * 0.00070967741)) * results[f'{attacker}_ground_win_rate'] + ((attacker_soldiers_value * 0.0004060606) + (attacker_tanks_value * 0.00066666666)) * (1 - results[f'{attacker}_ground_win_rate'])) * cas_rate * 3), results[defender]['tanks'])

            results[f'{attacker}_airtoair_{attacker}_avg'] = min(round(results[f'{defender}']['aircraft'] * 3 * 0.7 * 0.01 * 3 * results[f'{attacker}_extra_cas']), results[f'{attacker}']['aircraft'])
            results[f'{attacker}_airtoair_{attacker}_diff'] = min(round(results[f'{defender}']['aircraft'] * 3 * 0.3 * 0.01 * 3 * results[f'{attacker}_extra_cas']), results[f'{attacker}']['aircraft'])
            results[f'{attacker}_airtoother_{attacker}_avg'] = min(round(results[f'{defender}']['aircraft'] * 3 * 0.7 * 0.015385 * 3 * results[f'{attacker}_extra_cas']), results[f'{attacker}']['aircraft'])
            results[f'{attacker}_airtoother_{attacker}_diff'] = min(round(results[f'{defender}']['aircraft'] * 3 * 0.3 * 0.015385 * 3 * results[f'{attacker}_extra_cas']), results[f'{attacker}']['aircraft'])

            results[f'{attacker}_airtoair_{defender}_avg'] = min(round(results[f'{attacker}']['aircraft'] * 3 * 0.7 * 0.018337 * 3), results[f'{defender}']['aircraft'])
            results[f'{attacker}_airtoair_{defender}_diff'] = min(round(results[f'{attacker}']['aircraft'] * 3 * 0.3 * 0.018337 * 3), results[f'{defender}']['aircraft'])
            results[f'{attacker}_airtoother_{defender}_avg'] = min(round(results[f'{attacker}']['aircraft'] * 3 * 0.7 * 0.009091 * 3), results[f'{defender}']['aircraft'])
            results[f'{attacker}_airtoother_{defender}_diff'] = min(round(results[f'{attacker}']['aircraft'] * 3 * 0.3 * 0.009091 * 3), results[f'{defender}']['aircraft'])

            results[f'{attacker}_naval_{defender}_avg'] = min(round(results[f'{attacker}']['ships'] * 4 * 0.7 * 0.01375 * 3 * results[f'{attacker}_extra_cas']), results[f'{defender}']['aircraft'])
            results[f'{attacker}_naval_{defender}_diff'] = min(round(results[f'{attacker}']['ships'] * 4 * 0.3 * 0.01375 * 3 * results[f'{attacker}_extra_cas']), results[f'{defender}']['aircraft'])
            results[f'{attacker}_naval_{attacker}_avg'] = min(round(results[f'{defender}']['ships'] * 4 * 0.7 * 0.01375 * 3), results[f'{attacker}']['aircraft'])
            results[f'{attacker}_naval_{attacker}_diff'] = min(round(results[f'{defender}']['ships'] * 4 * 0.3 * 0.01375 * 3), results[f'{attacker}']['aircraft'])

        def def_rss_consumption(winrate: Union[int, float]) -> float:
            rate = -0.4624 * winrate**2 + 1.06256 * winrate + 0.3999            
            if rate < 0.4:
                rate = 0.4
            return rate
            ## See note

        results["nation1"]['city'] = sorted(results['nation1']['cities'], key=lambda k: k['infrastructure'], reverse=True)[0]
        results["nation2"]['city'] = sorted(results['nation2']['cities'], key=lambda k: k['infrastructure'], reverse=True)[0]

        for nation in ["nation1", "nation2"]:
            results[f'{nation}_policy_infra_dealt'] = 1
            results[f'{nation}_policy_loot_stolen'] = 1
            results[f'{nation}_policy_infra_lost'] = 1
            results[f'{nation}_policy_loot_lost'] = 1
            results[f'{nation}_policy_improvements_lost'] = 1
            results[f'{nation}_policy_loot_stolen'] = 1
            results[f'{nation}_policy_improvements_destroyed'] = 1
            results[f'{nation}_vds_mod'] = 1
            results[f'{nation}_irond_mod'] = 1

            if results[f'{nation}']['warpolicy'] == "Attrition":
                results[f'{nation}_policy_infra_dealt'] = 1.1
                results[f'{nation}_policy_loot_stolen'] = 0.8
            elif results[f'{nation}']['warpolicy'] == "Turtle":
                results[f'{nation}_policy_infra_lost'] = 0.9
                results[f'{nation}_policy_loot_lost'] = 1.2
            elif results[f'{nation}']['warpolicy'] == "Moneybags":
                results[f'{nation}_policy_infra_lost'] = 1.05
                results[f'{nation}_policy_loot_lost'] = 0.6
            elif results[f'{nation}']['warpolicy'] == "Pirate":
                results[f'{nation}_policy_improvements_lost'] = 2.0
                results[f'{nation}_policy_loot_stolen'] = 1.4
            elif results[f'{nation}']['warpolicy'] == "Tactician":
                results[f'{nation}_policy_improvements_destroyed'] = 2.0
            elif results[f'{nation}']['warpolicy'] == "Guardian":
                results[f'{nation}_policy_improvements_lost'] = 0.5
                results[f'{nation}_policy_loot_lost'] = 1.2
            elif results[f'{nation}']['warpolicy'] == "Covert":
                results[f'{nation}_policy_infra_lost'] = 1.05
            elif results[f'{nation}']['warpolicy'] == "Arcane":
                results[f'{nation}_policy_infra_lost'] = 1.05
            elif results[f'{nation}']['vds']:
                results[f'{nation}_vds_mod'] = 0.8
            elif results[f'{nation}']['irond']:
                results[f'{nation}_irond_mod'] = 0.5
        
        def airstrike_casualties(winrate: Union[int, float]) -> float:
            rate = -0.4624 * winrate**2 + 1.06256 * winrate + 0.3999            
            if rate < 0.4:
                rate = 0.4
            return rate

        for attacker, defender in [("nation1", "nation2"), ("nation2", "nation1")]:
            results[f'{attacker}_ground_{defender}_lost_infra_avg'] = max(min(((results[f'{attacker}']['soldiers'] - results[f'{defender}']['soldiers'] * 0.5) * 0.000606061 + (results[f'{attacker}']['tanks'] - (results[f'{defender}']['tanks'] * 0.5)) * 0.01) * 0.95 * results[f'{attacker}_ground_win_rate'], results[defender]['city']['infrastructure'] * 0.2 + 25), 0) * results[f'{attacker}_war_infra_mod'] * results[f'{attacker}_policy_infra_dealt'] * results[f'{defender}_policy_infra_lost']
            results[f'{attacker}_ground_{defender}_lost_infra_diff'] = results[f'{attacker}_ground_{defender}_lost_infra_avg'] / 0.95 * 0.15
            results[f'{attacker}_ground_loot_avg'] = (results[f'{attacker}']['soldiers'] * 1.1 + results[f'{attacker}']['tanks'] * 25.15) * results[f'{attacker}_ground_win_rate'] * 3 * 0.95 * results[f'{attacker}_war_loot_mod'] * results[f'{attacker}_policy_loot_stolen'] * results[f'{defender}_policy_loot_lost']
            results[f'{attacker}_ground_loot_diff'] = results[f'{attacker}_ground_loot_avg'] / 0.95 * 0.1

            results[f'{attacker}_air_{defender}_lost_infra_avg'] = max(min((results[f'{attacker}']['aircraft'] - results[f'{defender}']['aircraft'] * 0.5) * 0.35353535 * 0.95 * results[f'{attacker}_air_win_rate'], results[defender]['city']['infrastructure'] * 0.5 + 100), 0) * results[f'{attacker}_war_infra_mod'] * results[f'{attacker}_policy_infra_dealt'] * results[f'{defender}_policy_infra_lost']
            results[f'{attacker}_air_{defender}_lost_infra_diff'] = results[f'{attacker}_air_{defender}_lost_infra_avg'] / 0.95 * 0.15
            results[f'{attacker}_air_{defender}_soldiers_destroyed_avg'] = round(max(min(results[f'{defender}']['soldiers'], results[f'{defender}']['soldiers'] * 0.75 + 1000, (results[f'{attacker}']['aircraft'] - results[f'{defender}']['aircraft'] * 0.5) * 35 * 0.95), 0)) * airstrike_casualties(results[f'{attacker}_air_win_rate'])
            results[f'{attacker}_air_{defender}_soldiers_destroyed_diff'] = results[f'{attacker}_air_{defender}_soldiers_destroyed_avg'] / 0.95 * 0.1
            results[f'{attacker}_air_{defender}_tanks_destroyed_avg'] = round(max(min(results[f'{defender}']['tanks'], results[f'{defender}']['tanks'] * 0.75 + 10, (results[f'{attacker}']['aircraft'] - results[f'{defender}']['aircraft'] * 0.5) * 1.25 * 0.95), 0)) * airstrike_casualties(results[f'{attacker}_air_win_rate'])
            results[f'{attacker}_air_{defender}_tanks_destroyed_diff'] = results[f'{attacker}_air_{defender}_tanks_destroyed_avg'] / 0.95 * 0.1
            results[f'{attacker}_air_{defender}_ships_destroyed_avg'] = round(max(min(results[f'{defender}']['ships'], results[f'{defender}']['ships'] * 0.75 + 4, (results[f'{attacker}']['aircraft'] - results[f'{defender}']['aircraft'] * 0.5) * 0.0285 * 0.95), 0)) * airstrike_casualties(results[f'{attacker}_air_win_rate'])
            results[f'{attacker}_air_{defender}_ships_destroyed_diff'] = results[f'{attacker}_air_{defender}_ships_destroyed_avg'] / 0.95 * 0.1

            results[f'{attacker}_naval_{defender}_lost_infra_avg'] = max(min((results[f'{attacker}']['ships'] - results[f'{attacker}']['ships'] * 0.5) * 2.625 * 0.95 * results[f'{attacker}_naval_win_rate'], results[defender]['city']['infrastructure'] * 0.5 + 25), 0) * results[f'{attacker}_war_infra_mod'] * results[f'{attacker}_policy_infra_dealt'] * results[f'{defender}_policy_infra_lost']
            results[f'{attacker}_naval_{defender}_lost_infra_diff'] = results[f'{attacker}_naval_{defender}_lost_infra_avg'] / 0.95 * 0.15

            results[f'{attacker}_nuke_{defender}_lost_infra_avg'] = max(min((1700 + max(2000, results[defender]['city']['infrastructure'] * 100 / results[defender]['city']['land'] * 13.5)) / 2, results[defender]['city']['infrastructure'] * 0.8 + 150), 0) * results[f'{attacker}_war_infra_mod'] * results[f'{attacker}_policy_infra_dealt'] * results[f'{defender}_policy_infra_lost'] * results[f'{attacker}_vds_mod']
            results[f'{attacker}_missile_{defender}_lost_infra_avg'] = max(min((300 + max(350, results[defender]['city']['infrastructure'] * 100 / results[defender]['city']['land'] * 3)) / 2, results[defender]['city']['infrastructure'] * 0.3 + 100), 0) * results[f'{attacker}_war_infra_mod'] * results[f'{attacker}_policy_infra_dealt'] * results[f'{defender}_policy_infra_lost'] * results[f'{attacker}_irond_mod']
            
            for infra in [
                f"{attacker}_ground_{defender}_lost_infra",
                f"{attacker}_air_{defender}_lost_infra",
                f"{attacker}_naval_{defender}_lost_infra",
                f"{attacker}_nuke_{defender}_lost_infra",
                f"{attacker}_missile_{defender}_lost_infra",
                ]:
                results[f'{infra}_avg_value'] = utils.infra_cost(results[defender]['city']['infrastructure'] - results[f'{infra}_avg'], results[defender]['city']['infrastructure'])
                try:
                    results[f'{infra}_diff_value'] = utils.infra_cost(results[defender]['city']['infrastructure'] - results[f'{infra}_diff'], results[defender]['city']['infrastructure'])
                except:
                    pass
            
            for attack in ['airvair', 'airvsoldiers', 'airvtanks', 'airvships']:
                results[f"{attacker}_{attack}_{defender}_lost_infra_avg_value"] = results[f"{attacker}_air_{defender}_lost_infra_avg_value"] * 1/3
            results[f"{attacker}_airvinfra_{defender}_lost_infra_avg_value"] = results[f"{attacker}_air_{defender}_lost_infra_avg_value"]

            results[f'{attacker}_ground_{attacker}_mun'] = results[f'{attacker}']['soldiers'] * 0.0002 + results[f'{attacker}']['tanks'] * 0.01
            results[f'{attacker}_ground_{attacker}_gas'] = results[f'{attacker}']['tanks'] * 0.01
            results[f'{attacker}_ground_{attacker}_alum'] = 0
            results[f'{attacker}_ground_{attacker}_steel'] = results[f'{attacker}_ground_{attacker}_avg_tanks'] * 0.5
            results[f'{attacker}_ground_{attacker}_money'] = -results[f'{attacker}_ground_loot_avg'] + results[f'{attacker}_ground_{attacker}_avg_tanks'] * 50 + results[f'{attacker}_ground_{attacker}_avg_soldiers'] * 5
            results[f'{attacker}_ground_{attacker}_total'] = results[f'{attacker}_ground_{attacker}_alum'] * 2971 + results[f'{attacker}_ground_{attacker}_steel'] * 3990 + results[f'{attacker}_ground_{attacker}_gas'] * 3340 + results[f'{attacker}_ground_{attacker}_mun'] * 1960 + results[f'{attacker}_ground_{attacker}_money'] 

            base_mun = (results[f'{defender}']['soldiers'] * 0.0002 + results[f'{defender}']['population'] / 2000000 + results[f'{defender}']['tanks'] * 0.01) * def_rss_consumption(results[f'{attacker}_ground_win_rate'])
            results[f'{attacker}_ground_{defender}_mun'] = (base_mun * (1 - results[f'{attacker}_ground_fail']) + min(base_mun, results[f'{attacker}_ground_{attacker}_mun']) * results[f'{attacker}_ground_fail'])
            base_gas = results[f'{defender}']['tanks'] * 0.01 * def_rss_consumption(results[f'{attacker}_ground_win_rate'])
            results[f'{attacker}_ground_{defender}_gas'] = (base_gas * (1 - results[f'{attacker}_ground_fail']) + min(base_gas, results[f'{attacker}_ground_{attacker}_gas']) * results[f'{attacker}_ground_fail'])
            results[f'{attacker}_ground_{defender}_alum'] = results[f'{attacker}_ground_{defender}_avg_aircraft'] * 5
            results[f'{attacker}_ground_{defender}_steel'] = results[f'{attacker}_ground_{defender}_avg_tanks'] * 0.5
            results[f'{attacker}_ground_{defender}_money'] = results[f'{attacker}_ground_loot_avg'] + results[f'{attacker}_ground_{defender}_avg_aircraft'] * 4000 + results[f'{attacker}_ground_{defender}_avg_tanks'] * 50 + results[f'{attacker}_ground_{defender}_avg_soldiers'] * 5 + results[f'{attacker}_ground_{defender}_lost_infra_avg_value']
            results[f'{attacker}_ground_{defender}_total'] = results[f'{attacker}_ground_{defender}_alum'] * 2971 + results[f'{attacker}_ground_{defender}_steel'] * 3990 + results[f'{attacker}_ground_{defender}_gas'] * 3340 + results[f'{attacker}_ground_{defender}_mun'] * 1960 + results[f'{attacker}_ground_{defender}_money'] 
            results[f'{attacker}_ground_net'] = results[f'{attacker}_ground_{defender}_total'] - results[f'{attacker}_ground_{attacker}_total']
            

            for attack in ['air', 'airvair', 'airvinfra', 'airvsoldiers', 'airvtanks', 'airvships']:
                results[f'{attacker}_{attack}_{attacker}_gas'] = results[f'{attacker}_{attack}_{attacker}_mun'] = results[f'{attacker}']['aircraft'] / 4
                base_gas = results[f'{defender}']['aircraft'] / 4 * def_rss_consumption(results[f'{attacker}_air_win_rate'])
                results[f'{attacker}_{attack}_{defender}_gas'] = results[f'{attacker}_{attack}_{defender}_mun'] = (base_gas * (1 - results[f'{attacker}_air_fail']) + min(base_gas, results[f'{attacker}_air_{attacker}_gas']) * results[f'{attacker}_air_fail'])


            results[f'{attacker}_airvair_{attacker}_alum'] = results[f'{attacker}_airtoair_{attacker}_avg'] * 5
            results[f'{attacker}_airvair_{attacker}_steel'] = 0
            results[f'{attacker}_airvair_{attacker}_money'] = results[f'{attacker}_airtoair_{attacker}_avg'] * 4000
            results[f'{attacker}_airvair_{attacker}_total'] = results[f'{attacker}_airvair_{attacker}_alum'] * 2971 + results[f'{attacker}_airvair_{attacker}_steel'] * 3990 + results[f'{attacker}_air_{attacker}_gas'] * 3340 + results[f'{attacker}_air_{attacker}_mun'] * 1960 + results[f'{attacker}_airvair_{attacker}_money'] 
           
            results[f'{attacker}_airvair_{defender}_alum'] = results[f'{attacker}_airtoair_{defender}_avg'] * 5
            results[f'{attacker}_airvair_{defender}_steel'] = 0
            results[f'{attacker}_airvair_{defender}_money'] = results[f'{attacker}_airtoair_{defender}_avg'] * 4000 + results[f'{attacker}_air_{defender}_lost_infra_avg_value'] * 1/3
            results[f'{attacker}_airvair_{defender}_total'] = results[f'{attacker}_airvair_{defender}_alum'] * 2971 + results[f'{attacker}_airvair_{defender}_steel'] * 3990 + results[f'{attacker}_air_{defender}_gas'] * 3340 + results[f'{attacker}_air_{defender}_mun'] * 1960 + results[f'{attacker}_airvair_{defender}_money'] 
            results[f'{attacker}_airvair_net'] = results[f'{attacker}_airvair_{defender}_total'] - results[f'{attacker}_airvair_{attacker}_total']


            results[f'{attacker}_airvinfra_{attacker}_alum'] = results[f'{attacker}_airtoother_{attacker}_avg'] * 5
            results[f'{attacker}_airvinfra_{attacker}_steel'] = 0
            results[f'{attacker}_airvinfra_{attacker}_money'] = results[f'{attacker}_airtoother_{attacker}_avg'] * 4000
            results[f'{attacker}_airvinfra_{attacker}_total'] = results[f'{attacker}_airvinfra_{attacker}_alum'] * 2971 + results[f'{attacker}_airvinfra_{attacker}_steel'] * 3990 + results[f'{attacker}_air_{attacker}_gas'] * 3340 + results[f'{attacker}_air_{attacker}_mun'] * 1960 + results[f'{attacker}_airvinfra_{attacker}_money'] 

            results[f'{attacker}_airvinfra_{defender}_alum'] = results[f'{attacker}_airtoother_{defender}_avg'] * 5
            results[f'{attacker}_airvinfra_{defender}_steel'] = 0
            results[f'{attacker}_airvinfra_{defender}_money'] = results[f'{attacker}_airtoother_{defender}_avg'] * 4000 + results[f'{attacker}_air_{defender}_lost_infra_avg_value']
            results[f'{attacker}_airvinfra_{defender}_total'] = results[f'{attacker}_airvinfra_{defender}_alum'] * 2971 + results[f'{attacker}_airvinfra_{defender}_steel'] * 3990 + results[f'{attacker}_air_{defender}_gas'] * 3340 + results[f'{attacker}_air_{defender}_mun'] * 1960 + results[f'{attacker}_airvinfra_{defender}_money'] 
            results[f'{attacker}_airvinfra_net'] = results[f'{attacker}_airvinfra_{defender}_total'] - results[f'{attacker}_airvinfra_{attacker}_total']


            results[f'{attacker}_airvsoldiers_{attacker}_alum'] = results[f'{attacker}_airtoother_{attacker}_avg'] * 5
            results[f'{attacker}_airvsoldiers_{attacker}_steel'] = 0
            results[f'{attacker}_airvsoldiers_{attacker}_money'] = results[f'{attacker}_airtoother_{attacker}_avg'] * 4000
            results[f'{attacker}_airvsoldiers_{attacker}_total'] = results[f'{attacker}_airvsoldiers_{attacker}_alum'] * 2971 + results[f'{attacker}_airvsoldiers_{attacker}_steel'] * 3990 + results[f'{attacker}_air_{attacker}_gas'] * 3340 + results[f'{attacker}_air_{attacker}_mun'] * 1960 + results[f'{attacker}_airvsoldiers_{attacker}_money'] 
            
            results[f'{attacker}_airvsoldiers_{defender}_alum'] = results[f'{attacker}_airtoother_{defender}_avg'] * 5
            results[f'{attacker}_airvsoldiers_{defender}_steel'] = 0
            results[f'{attacker}_airvsoldiers_{defender}_money'] = results[f'{attacker}_airtoother_{defender}_avg'] * 4000 + results[f'{attacker}_air_{defender}_lost_infra_avg_value'] * 1/3 + results[f'{attacker}_air_{defender}_soldiers_destroyed_avg'] * 5
            results[f'{attacker}_airvsoldiers_{defender}_total'] = results[f'{attacker}_airvsoldiers_{defender}_alum'] * 2971 + results[f'{attacker}_airvsoldiers_{defender}_steel'] * 3990 + results[f'{attacker}_air_{defender}_gas'] * 3340 + results[f'{attacker}_air_{defender}_mun'] * 1960 + results[f'{attacker}_airvsoldiers_{defender}_money'] 
            results[f'{attacker}_airvsoldiers_net'] = results[f'{attacker}_airvair_{defender}_total'] - results[f'{attacker}_airvsoldiers_{attacker}_total']


            results[f'{attacker}_airvtanks_{attacker}_alum'] = results[f'{attacker}_airtoother_{attacker}_avg'] * 5
            results[f'{attacker}_airvtanks_{attacker}_steel'] = 0
            results[f'{attacker}_airvtanks_{attacker}_money'] = results[f'{attacker}_airtoother_{attacker}_avg'] * 4000
            results[f'{attacker}_airvtanks_{attacker}_total'] = results[f'{attacker}_airvtanks_{attacker}_alum'] * 2971 + results[f'{attacker}_airvtanks_{attacker}_steel'] * 3990 + results[f'{attacker}_air_{attacker}_gas'] * 3340 + results[f'{attacker}_air_{attacker}_mun'] * 1960 + results[f'{attacker}_airvtanks_{attacker}_money'] 
            
            results[f'{attacker}_airvtanks_{defender}_alum'] = results[f'{attacker}_airtoother_{defender}_avg'] * 5
            results[f'{attacker}_airvtanks_{defender}_steel'] = results[f'{attacker}_air_{defender}_tanks_destroyed_avg'] * 0.5
            results[f'{attacker}_airvtanks_{defender}_money'] = results[f'{attacker}_airtoother_{defender}_avg'] * 4000 + results[f'{attacker}_air_{defender}_lost_infra_avg_value'] * 1/3 + results[f'{attacker}_air_{defender}_tanks_destroyed_avg'] * 60
            results[f'{attacker}_airvtanks_{defender}_total'] = results[f'{attacker}_airvtanks_{defender}_alum'] * 2971 + results[f'{attacker}_airvtanks_{defender}_steel'] * 3990 + results[f'{attacker}_air_{defender}_gas'] * 3340 + results[f'{attacker}_air_{defender}_mun'] * 1960 + results[f'{attacker}_airvtanks_{defender}_money'] 
            results[f'{attacker}_airvtanks_net'] = results[f'{attacker}_airvtanks_{defender}_total'] - results[f'{attacker}_airvtanks_{attacker}_total']


            results[f'{attacker}_airvships_{attacker}_alum'] = results[f'{attacker}_airtoother_{attacker}_avg'] * 5
            results[f'{attacker}_airvships_{attacker}_steel'] = 0
            results[f'{attacker}_airvships_{attacker}_money'] = results[f'{attacker}_airtoother_{attacker}_avg'] * 4000
            results[f'{attacker}_airvships_{attacker}_total'] = results[f'{attacker}_airvships_{attacker}_alum'] * 2971 + results[f'{attacker}_airvships_{attacker}_steel'] * 3990 + results[f'{attacker}_air_{attacker}_gas'] * 3340 + results[f'{attacker}_air_{attacker}_mun'] * 1960 + results[f'{attacker}_airvships_{attacker}_money'] 
            
            results[f'{attacker}_airvships_{defender}_alum'] = results[f'{attacker}_airtoother_{defender}_avg'] * 5
            results[f'{attacker}_airvships_{defender}_steel'] = results[f'{attacker}_air_{defender}_ships_destroyed_avg'] * 30
            results[f'{attacker}_airvships_{defender}_money'] = results[f'{attacker}_airtoother_{defender}_avg'] * 4000 + results[f'{attacker}_air_{defender}_lost_infra_avg_value'] * 1/3 + results[f'{attacker}_air_{defender}_ships_destroyed_avg'] * 50000
            results[f'{attacker}_airvships_{defender}_total'] = results[f'{attacker}_airvships_{defender}_alum'] * 2971 + results[f'{attacker}_airvships_{defender}_steel'] * 3990 + results[f'{attacker}_air_{defender}_gas'] * 3340 + results[f'{attacker}_air_{defender}_mun'] * 1960 + results[f'{attacker}_airvships_{defender}_money'] 
            results[f'{attacker}_airvships_net'] = results[f'{attacker}_airvships_{defender}_total'] - results[f'{attacker}_airvships_{attacker}_total']


            results[f'{attacker}_naval_{attacker}_mun'] = results[f'{attacker}']['ships'] * 3
            results[f'{attacker}_naval_{attacker}_gas'] = results[f'{attacker}']['ships'] * 2
            results[f'{attacker}_naval_{attacker}_alum'] = 0
            results[f'{attacker}_naval_{attacker}_steel'] = results[f'{attacker}_naval_{attacker}_avg'] * 30
            results[f'{attacker}_naval_{attacker}_money'] = results[f'{attacker}_naval_{attacker}_avg'] * 50000
            results[f'{attacker}_naval_{attacker}_total'] = results[f'{attacker}_naval_{attacker}_alum'] * 2971 + results[f'{attacker}_naval_{attacker}_steel'] * 3990 + results[f'{attacker}_naval_{attacker}_gas'] * 3340 + results[f'{attacker}_naval_{attacker}_mun'] * 1960 + results[f'{attacker}_naval_{attacker}_money'] 
           
            base_mun = results[f'{defender}']['ships'] * 3 * def_rss_consumption(results[f'{attacker}_air_win_rate'])
            results[f'{attacker}_naval_{defender}_mun'] = results[f'{attacker}_naval_{defender}_mun'] = (base_mun * (1 - results[f'{attacker}_naval_fail']) + min(base_gas, results[f'{attacker}_naval_{attacker}_mun']) * results[f'{attacker}_naval_fail'])
            base_gas = results[f'{defender}']['ships'] * 2 * def_rss_consumption(results[f'{attacker}_air_win_rate'])
            results[f'{attacker}_naval_{defender}_gas'] = results[f'{attacker}_naval_{defender}_gas'] = (base_gas * (1 - results[f'{attacker}_naval_fail']) + min(base_gas, results[f'{attacker}_naval_{attacker}_gas']) * results[f'{attacker}_naval_fail'])
            results[f'{attacker}_naval_{defender}_alum'] = 0
            results[f'{attacker}_naval_{defender}_steel'] = results[f'{attacker}_naval_{defender}_avg'] * 30
            results[f'{attacker}_naval_{defender}_money'] = results[f'{attacker}_naval_{defender}_lost_infra_avg_value'] + results[f'{attacker}_naval_{defender}_avg'] * 50000
            results[f'{attacker}_naval_{defender}_total'] = results[f'{attacker}_naval_{defender}_alum'] * 2971 + results[f'{attacker}_naval_{defender}_steel'] * 3990 + results[f'{attacker}_naval_{defender}_gas'] * 3340 + results[f'{attacker}_naval_{defender}_mun'] * 1960 + results[f'{attacker}_naval_{defender}_money'] 
            results[f'{attacker}_naval_net'] = results[f'{attacker}_naval_{defender}_total'] - results[f'{attacker}_naval_{attacker}_total']


            results[f'{attacker}_nuke_{attacker}_alum'] = 750
            results[f'{attacker}_nuke_{attacker}_steel'] = 0
            results[f'{attacker}_nuke_{attacker}_gas'] = 500
            results[f'{attacker}_nuke_{attacker}_mun'] = 0
            results[f'{attacker}_nuke_{attacker}_money'] = 1750000
            results[f'{attacker}_nuke_{attacker}_total'] = results[f'{attacker}_nuke_{attacker}_alum'] * 2971 + results[f'{attacker}_nuke_{attacker}_steel'] * 3990 + results[f'{attacker}_nuke_{attacker}_gas'] * 3340 + results[f'{attacker}_nuke_{attacker}_mun'] * 1960 + results[f'{attacker}_nuke_{attacker}_money'] + 250 * 3039 #price of uranium
            
            results[f'{attacker}_nuke_{defender}_alum'] = 0
            results[f'{attacker}_nuke_{defender}_steel'] = 0
            results[f'{attacker}_nuke_{defender}_gas'] = 0
            results[f'{attacker}_nuke_{defender}_mun'] = 0
            results[f'{attacker}_nuke_{defender}_money'] = results[f'{attacker}_nuke_{defender}_lost_infra_avg_value']
            results[f'{attacker}_nuke_{defender}_total'] = results[f'{attacker}_nuke_{defender}_alum'] * 2971 + results[f'{attacker}_nuke_{defender}_steel'] * 3990 + results[f'{attacker}_nuke_{defender}_gas'] * 3340 + results[f'{attacker}_nuke_{defender}_mun'] * 1960 + results[f'{attacker}_nuke_{defender}_money'] 
            results[f'{attacker}_nuke_net'] = results[f'{attacker}_nuke_{defender}_total'] - results[f'{attacker}_nuke_{attacker}_total']


            results[f'{attacker}_missile_{attacker}_alum'] = 100
            results[f'{attacker}_missile_{attacker}_steel'] = 0
            results[f'{attacker}_missile_{attacker}_gas'] = 75
            results[f'{attacker}_missile_{attacker}_mun'] = 75
            results[f'{attacker}_missile_{attacker}_money'] = 150000
            results[f'{attacker}_missile_{attacker}_total'] = results[f'{attacker}_missile_{attacker}_alum'] * 2971 + results[f'{attacker}_missile_{attacker}_steel'] * 3990 + results[f'{attacker}_missile_{attacker}_gas'] * 3340 + results[f'{attacker}_missile_{attacker}_mun'] * 1960 + results[f'{attacker}_missile_{attacker}_money']
            
            results[f'{attacker}_missile_{defender}_alum'] = 0
            results[f'{attacker}_missile_{defender}_steel'] = 0
            results[f'{attacker}_missile_{defender}_gas'] = 0
            results[f'{attacker}_missile_{defender}_mun'] = 0
            results[f'{attacker}_missile_{defender}_money'] = results[f'{attacker}_missile_{defender}_lost_infra_avg_value']
            results[f'{attacker}_missile_{defender}_total'] = results[f'{attacker}_missile_{defender}_alum'] * 2971 + results[f'{attacker}_missile_{defender}_steel'] * 3990 + results[f'{attacker}_missile_{defender}_gas'] * 3340 + results[f'{attacker}_missile_{defender}_mun'] * 1960 + results[f'{attacker}_missile_{defender}_money'] 
            results[f'{attacker}_missile_net'] = results[f'{attacker}_missile_{defender}_total'] - results[f'{attacker}_missile_{attacker}_total']

        return results

def setup(bot):
    bot.add_cog(Military(bot))