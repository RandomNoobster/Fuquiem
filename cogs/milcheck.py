import discord
import requests
import math
from main import mongo
from datetime import datetime, timezone, timedelta
import traceback
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
    @commands.has_any_role(*utils.low_gov_plus_perms)
    async def milcheck(self, ctx):
        async with aiohttp.ClientSession() as session:
            message = await ctx.send('Hang on...')
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 first:500 alliance_id:4729){{data{{id leader_name nation_name alliance_id color alliance_position num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available wars{{winner turnsleft attacker{{id}} defender{{id}}}} cities{{infrastructure barracks factory airforcebase drydock}}}}}}}}"}) as temp:
                nations = (await temp.json())['data']['nations']['data']
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={convent_key}", json={'query': f"{{nations(page:1 first:500 alliance_id:7531){{data{{id leader_name nation_name alliance_id color alliance_position num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium espionage_available wars{{winner turnsleft attacker{{id}} defender{{id}}}} cities{{infrastructure barracks factory airforcebase drydock}}}}}}}}"}) as temp:
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
            defensive_used_slots = 0
            for war in x['wars']:
                if war['turnsleft'] > 0 and war['attacker']['id'] == x['id']:
                    offensive_used_slots += 1
                elif war['turnsleft'] > 0 and war['defender']['id'] == x['id']:
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
    @commands.has_any_role(*utils.mid_gov_plus_perms)
    async def clear_threads(self, ctx):
        for thread in ctx.channel.threads:
            await thread.delete()
        print("done")
        return
    
    async def add_to_thread(self, thread, atom_id: Union[str, int], atom: dict = None):
        await asyncio.sleep(1.1)
        person = utils.find_user(self, atom_id)
        if person == {}:
            print("tried to add, but could not find", atom_id)
            if atom:
                await thread.send(f"I was unable to add {atom['leader_name']} of {atom['nation_name']} to the thread. Have they not linked their nation with their discord account?")
            else:
                await thread.send(f"I was unable to add nation {atom_id} to the thread. Have they not linked their nation with their discord account?")
            return
        user = await self.bot.fetch_user(person['user'])
        try:
            await thread.add_user(user)
        except Exception as e:
            await thread.send(f"I was unable to add {user} to the thread.\n```{e}```")
    
    async def remove_from_thread(self, thread, atom_id: Union[str, int], atom: dict = None):
        await asyncio.sleep(1.1)
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
        #channel_id = int(os.getenv("channel_id"))
        channel = self.bot.get_channel(923249186500116560) #923249186500116560 | 842115066424852510
        debug_channel = self.bot.get_channel(739155202640183377)
        prev_wars = None

        async def cthread(war, non_atom, atom):
            await asyncio.sleep(1.1)

            url = f"https://politicsandwar.com/nation/war/timeline/war={war['id']}"
            if war['att_alliance_id'] in ["4719", "7531"]:
                war_type = "Offensive"
            else:
                war_type = "Defensive"
            embed = discord.Embed(title=f"New {war_type} War", url=url, description=f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) declared a{'n'[:(len(war['war_type'])-5)^1]} {war['war_type'].lower()} war on [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']}) for the reason of: ```{war['reason']}```", color=0x2F3136)
            name = f"{non_atom['nation_name']} ({non_atom['id']})"
            found = False

            for thread in channel.threads:
                if f"({non_atom['id']})" in thread.name:
                    found = True
                    matching_thread = thread
                    break
            if not found:
                async for thread in channel.archived_threads():
                    if f"({non_atom['id']})" in thread.name:
                        found = True
                        matching_thread = thread
                        break
            if not found:
                message = await channel.send(embed=embed)
                try:
                    try:
                        thread = await channel.create_thread(name=name, message=message, auto_archive_duration=4320, type=discord.ChannelType.private_thread, reason="War declaration")
                    except:
                        thread = await channel.create_thread(name=name, message=message, auto_archive_duration=1440, type=discord.ChannelType.private_thread, reason="War declaration")
                except discord.errors.HTTPException as e:
                    await debug_channel.send(f"I encountered an error when creating a thread: ```{e}```")
                    return
                await self.add_to_thread(thread, atom['id'], atom)
            elif found:
                await matching_thread.send(embed=embed)
                await self.add_to_thread(matching_thread, atom['id'], atom)
            
            attack_logs = {"id": war['id'], "attacks": [], "detected": datetime.utcnow(), "finished": False}
            mongo.war_logs.insert_one(attack_logs)

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
            await asyncio.sleep(1.1)

            url = f"https://politicsandwar.com/nation/war/timeline/war={war['id']}"
            if war['att_alliance_id'] in ["4719", "7531"]:
                war_type = "Offensive"
            else:
                war_type = "Defensive"
            embed = discord.Embed(title=f"New {war_type} War", url=url, description=f"[{war['attacker']['nation_name']}](https://politicsandwar.com/nation/id={war['attacker']['id']}) declared a{'n'[:(len(war['war_type'])-5)^1]} {war['war_type'].lower()} war on [{war['defender']['nation_name']}](https://politicsandwar.com/nation/id={war['defender']['id']}) for the reason of: ```{war['reason']}```", color=0x2F3136)
            
            found = False
            for thread in channel.threads:
                if f"({non_atom['id']})" in thread.name:
                    matching_thread = thread
                    found = True
                    break
            
            if not found:
                async for thread in channel.archived_threads():
                    if f"({non_atom['id']})" in thread.name:
                        matching_thread = thread
                        found = True
                        person = utils.find_user(self, atom['id'])
                        if not person:
                            print("tried to add to archived thread, but could not find", atom['id'])
                            await thread.send(f"I was unable to add nation {atom['id']} to the thread. Have they not linked their nation with their discord account?")
                            break
                        user = await self.bot.fetch_user(person['user'])
                        try:
                            await thread.add_user(user)
                        except:
                            pass
                        break
            
            if not found:
                print("making thread")
                await cthread(war, non_atom, atom)
                for thread in channel.threads:
                    if f"({non_atom['id']})" in thread.name:
                        print("found thread")
                        matching_thread = thread
                        found = True
                        break
                
            if found:
                thread = matching_thread
                url = f"https://politicsandwar.com/nation/war/timeline/war={war['id']}"
                if peace != None:
                    embed = discord.Embed(title="Peace offering", url=url, description=f"[{peace['offerer']['nation_name']}](https://politicsandwar.com/nation/id={peace['offerer']['id']}) is offering peace to [{peace['reciever']['nation_name']}](https://politicsandwar.com/nation/id={peace['reciever']['id']}). The peace offering will be canceled if either side performs an act of aggression.", color=0xffffff)
                    await thread.send(embed=embed)
                    return
                footer = f"<t:{round(datetime.strptime(attack['date'], '%Y-%m-%dT%H:%M:%S%z').timestamp())}:R> <t:{round(datetime.strptime(attack['date'], '%Y-%m-%dT%H:%M:%S%z').timestamp())}>"
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
                            if attack['aircraft_killed_by_tanks']:
                                aircraft = f"\n{attack['aircraft_killed_by_tanks']:,} aircraft"
                            else:
                                aircraft = ""
                            title = "Ground battle"
                            att_casualties = f"{attack['attcas1']:,} soldiers\n{attack['attcas2']:,} tanks"
                            def_casualties = f"{attack['defcas1']:,} soldiers\n{attack['defcas2']:,} tanks{aircraft}"
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
            else:
                print("could not find or create thread", war['id'], peace, non_atom, atom)

        min_id = 0
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    has_more_pages = True
                    n = 1
                    wars = []
                    while has_more_pages:
                        async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] page:{n} active:true){{paginatorInfo{{hasMorePages}} data{{id att_fortify war_type def_fortify attpeace defpeace turnsleft reason date att_alliance_id def_alliance_id attacker{{nation_name leader_name alliance{{name}} alliance_id id num_cities cities{{id}}}} defender{{nation_name leader_name alliance{{name}} alliance_id id num_cities cities{{id}}}} attacks{{type id date loot_info victor moneystolen success cityid resistance_eliminated infradestroyed infra_destroyed_value improvementslost aircraft_killed_by_tanks attcas1 attcas2 defcas1 defcas2}}}}}}}}"}) as temp:
                            n += 1
                            try:
                                wars += (await temp.json())['data']['wars']['data']
                                has_more_pages = (await temp.json())['data']['wars']['paginatorInfo']['hasMorePages']
                            except:
                                print((await temp.json())['errors'])
                                await asyncio.sleep(60)
                                continue
                            if prev_wars == None:
                                prev_wars = wars
                                continue
                    has_more_pages = True
                    n = 1
                    done_wars = []
                    all_wars = []
                    if random.random() < 0.2:
                        n = 0
                    while has_more_pages:
                        async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] page:{n} min_id:{min_id} active:false days_ago:5 orderBy:{{column: ID order:DESC}}){{paginatorInfo{{hasMorePages}} data{{id att_fortify war_type def_fortify attpeace defpeace turnsleft reason date att_alliance_id def_alliance_id attacker{{nation_name leader_name alliance{{name}} alliance_id id num_cities cities{{id}}}} defender{{nation_name leader_name alliance{{name}} alliance_id id num_cities cities{{id}}}} attacks{{type id date loot_info victor moneystolen success cityid resistance_eliminated infradestroyed infra_destroyed_value improvementslost aircraft_killed_by_tanks attcas1 attcas2 defcas1 defcas2}}}}}}}}"}) as temp1:
                            n += 1
                            try:
                                all_wars += (await temp1.json())['data']['wars']['data']
                                has_more_pages = (await temp1.json())['data']['wars']['paginatorInfo']['hasMorePages']
                            except:
                                print((await temp1.json())['errors'])
                                await asyncio.sleep(60)
                                continue
                    for war in all_wars:
                        if war['turnsleft'] <= 0:
                            declaration = datetime.strptime(war['date'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
                            if (datetime.utcnow() - declaration).days <= 5:
                                done_wars.append(war)
                    for new_war in wars:
                        try:
                            if new_war['att_alliance_id'] in ['4729', '7531']: ## CHANGE T0 ATOM ---------------------------------------------------------
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
                        except discord.errors.Forbidden:
                            pass
                        except Exception as e:
                            await debug_channel.send(f"I encountered an error when iterating through `wars` ```{e}```")
                    for done_war in done_wars:
                        try:
                            if done_war['att_alliance_id'] in ['4729', '7531']: ## CHANGE T0 ATOM ---------------------------------------------------------
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
                            if len(done_war['attacks']) == 0:
                                attack = {"type": "EXPIRATION", "id": -1, "date": datetime.strftime(datetime.utcnow().replace(tzinfo=timezone.utc), '%Y-%m-%dT%H:%M:%S%z')}
                                await smsg(None, attack, done_war, atom, non_atom, None)
                            elif done_war['attacks'][-1]['type'] not in ["PEACE", "VICTORY", "ALLIANCELOOT"]:
                                attack = {"type": "EXPIRATION", "id": -1, "date": datetime.strftime(datetime.utcnow().replace(tzinfo=timezone.utc), '%Y-%m-%dT%H:%M:%S%z')}
                                await smsg(None, attack, done_war, atom, non_atom, None)
                            for thread in channel.threads:
                                if f"({non_atom['id']})" in thread.name:
                                    await self.remove_from_thread(thread, atom['id'], atom)
                                    members = await thread.fetch_members()
                                    member_count = 0
                                    for member in members:
                                        user = await self.bot.fetch_user(member.id)
                                        if user.bot:
                                            continue
                                        else:
                                            member_count += 1
                                    if member_count == 0:
                                        await thread.edit(archived=True)
                                    mongo.war_logs.find_one_and_update({"id": done_war['id']}, {"$set": {"finished": True}})
                                    break
                        except discord.errors.Forbidden:
                            pass
                        except Exception as e:
                            await debug_channel.send(f"I encountered an error when iterating through `done_wars` ```{e}```")
                if len(all_wars) > 0:
                    min_id = all_wars[0]['id']
                prev_wars = wars
                await asyncio.sleep(60)
            except:
                await debug_channel.send(f"I encountered an error whilst scanning for wars:```{traceback.format_exc()}```")

    @commands.command(
        brief="Status of someone's ongoing wars.",
        aliases=['s'],
        help="Can be used without arguments in a war thread, or you can supply an argument to get the warring status of the supplied nation."
    )
    @commands.has_any_role(*utils.pupil_plus_perms)
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
            person = utils.find_nation_plus(self, arg)
            nation_id = str(person['id'])

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation_id}){{ data{{ nation_name leader_name id alliance{{ name }} cities{{ barracks factory airforcebase drydock }} population score last_active beigeturns vmode pirate_economy color dompolicy alliance_id num_cities soldiers tanks aircraft ships missiles nukes wars{{ defender{{ nation_name leader_name alliance_id alliance{{ name }} cities{{ barracks factory airforcebase drydock }} wars{{ attid defid turnsleft }} id pirate_economy score last_active beigeturns vmode num_cities color soldiers tanks aircraft ships nukes missiles }} attacker{{ nation_name leader_name alliance_id alliance{{ name }} cities{{ barracks factory airforcebase drydock }} wars{{ attid defid turnsleft }} id pirate_economy score last_active beigeturns vmode num_cities color soldiers tanks aircraft ships nukes missiles }} date id attid defid winner att_resistance def_resistance attpoints defpoints attpeace defpeace war_type groundcontrol airsuperiority navalblockade turnsleft att_fortify def_fortify }} }} }}}}"}) as temp:
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
        
        for war in nation['wars']:
            if war['defender']['alliance_id'] in ['4729', '7531']:
                if war['turnsleft'] <= 0:
                    await self.remove_from_thread(ctx.channel, war['defender']['id'])
                else:
                    await self.add_to_thread(ctx.channel, war['defender']['id'])
            if war['attacker']['alliance_id'] in ['4729', '7531']:
                if war['turnsleft'] <= 0:
                    await self.remove_from_thread(ctx.channel, war['attacker']['id'])
                else:
                    await self.add_to_thread(ctx.channel, war['attacker']['id'])

        nation['offensive_wars'] = [y for y in nation['wars'] if y['turnsleft'] > 0 and y['attid'] == nation['id']]
        nation['defensive_wars'] = [y for y in nation['wars'] if y['turnsleft'] > 0 and y['defid'] == nation['id']]
        nation['wars'] = nation['offensive_wars'] + nation['defensive_wars']

        if nation['alliance']:
            alliance = f"[{nation['alliance']['name']}](https://politicsandwar.com/alliance/id={nation['alliance_id']})"
        else:
            alliance = "No alliance"

        desc = f"[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']}) | {alliance}\n\nLast login: <t:{round(datetime.strptime(nation['last_active'], '%Y-%m-%dT%H:%M:%S%z').timestamp())}:R>\nOffensive wars: {len(nation['offensive_wars'])}/{max_offense}\nDefensive wars: {len(nation['defensive_wars'])}/3\nDefensive range: {round(nation['score'] / 1.75)} - {round(nation['score'] / 0.75)}{beige}\n\nSoldiers: **{nation['soldiers']:,}** / {max_sol:,}\nTanks: **{nation['tanks']:,}** / {max_tnk:,}\nPlanes: **{nation['aircraft']:,}** / {max_pln:,}\nShips: **{nation['ships']:,}** / {max_shp:,}"
        embed = discord.Embed(title=f"{nation['nation_name']} ({nation['id']}) & their wars", description=desc, color=0x00ff00)
        embed1 = discord.Embed(title=f"{nation['nation_name']} ({nation['id']}) & their wars", description=desc, color=0x00ff00)
        embed.set_footer(text="_________________________________\nThe chance to get immense triumphs is if the nation in question attacks the main enemy. On average, it's worth attacking if the percentage is above 13%. Use $battlesim for more detailed battle predictions.")
        embed1.set_footer(text="_________________________________\nThe chance to get immense triumphs is if the nation in question attacks the main enemy. On average, it's worth attacking if the percentage is above 13%. Use $battlesim for more detailed battle predictions.")
        n = 1

        for war in nation['wars']:
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

            if x['pirate_economy']:
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

            x['offensive_wars'] = [y for y in x['wars'] if y['turnsleft'] > 0 and y['attid'] == x['id']]
            x['defensive_wars'] = [y for y in x['wars'] if y['turnsleft'] > 0 and y['defid'] == x['id']]

            if x['alliance']:
                alliance = f"[{x['alliance']['name']}](https://politicsandwar.com/alliance/id={x['alliance_id']})"
            else:
                alliance = "No alliance"

            embed.add_field(name=f"\{war_emoji} {x['nation_name']} ({x['id']})", value=f"{vmstart}[War timeline](https://politicsandwar.com/nation/war/timeline/war={war['id']}) | [Message](https://politicsandwar.com/inbox/message/receiver={x['leader_name'].replace(' ', '+')})\n{alliance}\n\n**[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']})**{result['nation1_append']}\n{main_enemy_bar}\n**{main_enemy_res}/100** | MAPs: **{main_enemy_points}/12**\n\n**[{x['nation_name']}](https://politicsandwar.com/nation/id={x['id']})**{result['nation2_append']}\n{their_enemy_bar}\n**{their_enemy_res}/100** | MAPs: **{their_enemy_points}/12**\n\nExpiration (turns): {war['turnsleft']}\nLast login: <t:{round(datetime.strptime(x['last_active'], '%Y-%m-%dT%H:%M:%S%z').timestamp())}:R>\nOngoing wars: {len(x['offensive_wars'] + x['defensive_wars'])}\n\nGround IT chance: **{round(100 * result['nation2_ground_win_rate']**3)}%**\nAir IT chance: **{round(100 * result['nation2_air_win_rate']**3)}%**\nNaval IT chance: **{round(100 * result['nation2_naval_win_rate']**3)}%**{vmend}", inline=True)
            embed1.add_field(name=f"\{war_emoji} {x['nation_name']} ({x['id']})", value=f"{vmstart}[War timeline](https://politicsandwar.com/nation/war/timeline/war={war['id']}) | [Message](https://politicsandwar.com/inbox/message/receiver={x['leader_name'].replace(' ', '+')})\n{alliance}\n\n**[{nation['nation_name']}](https://politicsandwar.com/nation/id={nation['id']})**{result['nation1_append']}\n**[{x['nation_name']}](https://politicsandwar.com/nation/id={x['id']})**{result['nation2_append']}\n\nOffensive wars: {len(x['offensive_wars'])}/{max_offense}\nDefensive wars: {len(x['defensive_wars'])}/3{beige}\n\n Soldiers: **{x['soldiers']:,}** / {max_sol:,}\nTanks: **{x['tanks']:,}** / {max_tnk:,}\nPlanes: **{x['aircraft']:,}** / {max_pln:,}\nShips: **{x['ships']:,}** / {max_shp:,}\n\nGround IT chance: **{round(100 * result['nation2_ground_win_rate']**3)}%**\nAir IT chance: **{round(100 * result['nation2_air_win_rate']**3)}%**\nNaval IT chance: **{round(100 * result['nation2_naval_win_rate']**3)}%**{vmend}", inline=True)

        class status_view(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="General", style=discord.ButtonStyle.primary, custom_id="status_general", disabled=True)
            async def general_callback(self, b: discord.Button, i: discord.Interaction):
                general_button = [x for x in self.children if x.custom_id == "status_general"][0]
                military_button = [x for x in self.children if x.custom_id == "status_military"][0]
                general_button.disabled = True
                military_button.disabled = False
                await i.response.edit_message(content="", embed=embed, view=view)
            
            @discord.ui.button(label="Military", style=discord.ButtonStyle.primary, custom_id="status_military")
            async def right_callback(self, b: discord.Button, i: discord.Interaction):
                general_button = [x for x in self.children if x.custom_id == "status_general"][0]
                military_button = [x for x in self.children if x.custom_id == "status_military"][0]
                military_button.disabled = True
                general_button.disabled = False
                await i.response.edit_message(content="", embed=embed1, view=view)
        
        view = status_view()
        await message.edit(content="", attachments=[], embed=embed, view=view)
    
    @commands.command(
        brief='Add someone to the military coordination thread.',
        help="Must be used in a thread. Very wasteful command, since you can also add people by pinging them."
        )
    @commands.has_any_role(*utils.pupil_plus_perms)
    async def add(self, ctx, *, user):
        await self.add_to_thread(ctx.channel, user)

    @commands.command(
        brief='Remove someone from the military coordination thread.',
        help="Must be used in a thread. Supply the user you wish to remove from the thread."
        )
    @commands.has_any_role(*utils.low_gov_plus_perms)
    async def remove(self, ctx, *, user):
        await self.remove_from_thread(ctx.channel, user)

    @commands.command(
        aliases=['counter'],
        brief='Accepts one argument, gives you a pre-filled link to slotter.',
        help='Accepted arguments include nation name, leader name, nation id and nation link. When browsing the databse, Fuquiem will use the first match, so it can be wise to double check that it returns a slotter link for the correct person.'
        )
    async def counters(self, ctx, *, arg):
        result = utils.find_nation(arg)
        embed = discord.Embed(title="Counters",
                              description=f"[Explore counters against {result['nation_name']} on slotter](https://slotter.bsnk.dev/search?nation={result['id']}&alliances=4729,7531&countersMode=true&threatsMode=false&vm=false&grey=true&beige=false)", color=0x00ff00)
        await ctx.send(embed=embed)

    @commands.command(
        aliases=['spherecounters'],
        brief='Accepts one argument, gives you a pre-filled link to slotter.',
        help='Accepted arguments include nation name, leader name, nation id and nation link. When browsing the databse, Fuquiem will use the first match, so it can be wise to double check that it returns a slotter link for the correct person.'
        )
    async def allcounters(self, ctx, *, arg):
        result = utils.find_nation(arg)
        embed = discord.Embed(title="Sphere Counters",
                              description=f"[Explore counters against {result['nation_name']} on slotter](https://slotter.bsnk.dev/search?nation={result['id']}&alliances=4729,7531,790,5012,2358,6877,8804&countersMode=true&threatsMode=false&vm=false&grey=true&beige=false)", color=0x00ff00)
        await ctx.send(embed=embed)

    @commands.command(
        aliases=['target'],
        brief='Sends you a pre-filled link to slotter',
        help="Lets you find the easiest targets during a global war."
        )
    async def targets(self, ctx):
        #await ctx.send('This command has been disabled.')
        #return
        person = utils.find_user(self, ctx.author.id)
        embed = discord.Embed(title="Targets",
                              description=f"[Explore targets on slotter](https://slotter.bsnk.dev/search?nation={person['nationid']}&alliances=3427,1742,8777,7484,5049,7580,2510,8535,9620,5039,8280,9829,9618,4397,9465,9793&countersMode=false&threatsMode=false&vm=false&grey=true&beige=false)", color=0x00ff00)
        await ctx.send(embed=embed)

    @commands.command(
        aliases=['wc'],
        brief="Sends a warchest top up to the people in need",
        help="Requires admin perms, sends people the resources they need in addition to telling people what to deposit."
        )
    @commands.has_any_role(*utils.mid_gov_plus_perms)
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
    @commands.has_any_role(*utils.mid_gov_plus_perms)
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
                    person = utils.find_user(self, nation['nationid'])
                    minmoney = round(city_count * 500000 - float(nation['money']))
                    maxmoney = round(city_count * 500000 * 3 - float(nation['money']))
                    if maxmoney < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_money=" + str(round(abs(city_count * 500000 * 2 - float(nation['money']))))
                    if minmoney < 0:
                        minmoney = 0
                    mingasoline = round(city_count * 350 * 2 - float(nation['gasoline']))
                    maxgasoline = round(city_count * 350 * 3 - float(nation['gasoline']))
                    if maxgasoline < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_gasoline=" + str(round(abs(city_count * 350 * 2 - float(nation['gasoline']))))
                    if mingasoline < 0:
                        mingasoline = 0
                    minmunitions = round(city_count * 400 * 2 - float(nation['munitions']))
                    maxmunitions = round(city_count * 400 * 3 - float(nation['munitions']))
                    if maxmunitions < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_munitions=" + str(round(abs(city_count * 400 * 2 - float(nation['munitions']))))
                    if minmunitions < 0:
                        minmunitions = 0
                    minsteel = round(city_count * 600 * 2 - float(nation['steel']))
                    maxsteel = round(city_count * 600 * 3 - float(nation['steel']))
                    if maxsteel < 0:
                        if person != {}:
                            user = await self.bot.fetch_user(person['user'])
                            excess += "&d_steel=" + str(round(abs(city_count * 600 * 2 - float(nation['steel']))))
                    if minsteel < 0:
                        minsteel = 0
                    minaluminum = round(city_count * 315 * 2 - float(nation['aluminum']))
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
                            await ctx.send(f"I can confirm that the transaction to {nation['nation']} ({nation['leader']}) has successfully commenced.")
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
    @commands.has_any_role(*utils.low_gov_plus_perms)
    async def check_wars(self, ctx):
        await self.wars_check()
        await ctx.send(f'Done!')

    async def wars_check(self):
        async with aiohttp.ClientSession() as session:
            has_more_pages = True
            n = 1
            while has_more_pages:
                async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{wars(alliance_id:[4729,7531] page:{n} active:true){{paginatorInfo{{hasMorePages}} data{{id att_resistance def_resistance attacker{{nation_name score beigeturns alliance_position alliance{{name}} id num_cities alliance_id wars{{attid defid def_alliance_id turnsleft}}}} defender{{nation_name score beigeturns alliance_position alliance{{name}} id num_cities alliance_id wars{{attid defid def_alliance_id turnsleft}}}}}}}}}}"}) as temp:
                    n += 1
                    try:
                        wars = (await temp.json())['data']['wars']['data']
                        has_more_pages = (await temp.json())['data']['wars']['paginatorInfo']['hasMorePages']
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
                    for war in non_atom['wars']:
                        if war['turnsleft'] > 0 and war['def_alliance_id'] in ['4729', '7531']:
                            def_wars += 1
                    to_append['def_wars'] = def_wars
                    enemy_list.append(to_append)
                else:
                    enemy_list.remove(found)
                    found["engagements"].append(non_atom)
                    enemy_list.append(found)

            channel = self.bot.get_channel(842116871322337370) ## 842116871322337370
            await channel.purge()
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
    @commands.has_any_role(*utils.mid_gov_plus_perms)
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
    @commands.has_any_role(*utils.pupil_plus_perms)
    async def raids(self, ctx, *, arg=None):
        await ctx.send("Use Autolycus' `/raids` instead! <:randy:677159205848743947>")
        
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
    @commands.has_any_role(*utils.pupil_plus_perms)
    async def battlesim(self, ctx, nation1=None, nation2=None):
        #check is any wars are active, and if they have air superiority, ground control, fortified etc
        message = await ctx.send('Alright, give me a sec to calculate the winrates...')
        if nation1 == None:
            nation1 = ctx.author.id
        nation1_nation = utils.find_nation_plus(self, nation1)
        if not nation1_nation:
            if nation2 == None:
                await message.edit(content='I could not find that nation!')
                return
            else:
                await message.edit(content='I could not find nation 1!')
                return 
        nation1_id = str(nation1_nation['id'])

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
            nation2_nation = utils.find_nation_plus(self, nation2)
            if not nation2_nation:
                if nation2 == None:
                    await message.edit(content='I was able to find the nation you linked, but I could not find *your* nation!')
                    return
                else:
                    await message.edit(content='I could not find nation 2!')
                    return 
            nation2_id = str(nation2_nation['id'])
        
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

        cur_page = 1

        class switch(discord.ui.View):
            @discord.ui.button(label="Switch attacker/defender", style=discord.ButtonStyle.primary)
            async def callback(self, b: discord.Button, i: discord.Interaction):
                nonlocal cur_page
                if cur_page == 1:
                    cur_page = 2
                    await i.response.edit_message(embed=embed1)
                else:
                    cur_page = 1
                    await i.response.edit_message(embed=embed)
            
            async def interaction_check(self, interaction) -> bool:
                if interaction.user != ctx.author:
                    await interaction.response.send_message("These buttons are reserved for someone else!", ephemeral=True)
                    return False
                else:
                    return True
            
            async def on_timeout(self):
                await message.edit(content=f"<@{ctx.author.id}> The command timed out!")
                
        await message.edit(embed=embed, content="", view=switch())

    @commands.command(
        aliases=["dmg"],
        brief="Shows you how much damage each war attack would do",
        help="You can supply arguments just like what you'd do for $battlesim. It links to a page with some tables showing the damage dealt for each kind of attack."
        )
    async def damage(self, ctx, nation1=None, nation2=None):
        message = await ctx.send('Alright, give me a sec to calculate your mom...')
        if nation1 == None:
            nation1 = ctx.author.id
        nation1_nation = utils.find_nation_plus(self, nation1)
        if not nation1_nation:
            if nation2 == None:
                await message.edit(content='I could not find that nation!')
                return
            else:
                await message.edit(content='I could not find nation 1!')
                return 
        nation1_id = str(nation1_nation['id'])

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
            nation2_nation = utils.find_nation_plus(self, nation2)
            if not nation2_nation:
                if nation2 == None:
                    await message.edit(content='I was able to find the nation you linked, but I could not find *your* nation!')
                    return
                else:
                    await message.edit(content='I could not find nation 2!')
                    return 
            nation2_id = str(nation2_nation['id'])
        
        results = await self.battle_calc(nation1_id, nation2_id)
        endpoint = datetime.utcnow().strftime('%d%H%M%S%f')
        class webraid(MethodView):
            def get(raidclass):
                with open('./data/templates/damage.txt', 'r') as file:
                    template = file.read()
                result = Template(template).render(results=results)
                return str(result)
        app.add_url_rule(f"/damage/{endpoint}", view_func=webraid.as_view(str(datetime.utcnow())), methods=["GET", "POST"]) # this solution of adding a new page instead of updating an existing for the same nation is kinda dependent on the bot resetting every once in a while, bringing down all the endpoints
        await message.edit(content=f"Go to http://130.162.174.7:5000/damage/{endpoint}", attachments=[])

        
    async def battle_calc(self, nation1_id, nation2_id):
        results = {}

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation1_id}){{data{{nation_name population warpolicy id soldiers tanks aircraft ships irond vds cities{{infrastructure land}} wars{{groundcontrol airsuperiority navalblockade attpeace defpeace attid defid att_fortify def_fortify turnsleft war_type}}}}}}}}"}) as temp:
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

        for war in results['nation1']['wars']:
            if war['attid'] == nation2_id and war['turnsleft'] > 0 and war['defid'] == nation1_id:
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
            elif war['defid'] == nation2_id and war['turnsleft'] > 0 and war['attid'] == nation1_id:
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
