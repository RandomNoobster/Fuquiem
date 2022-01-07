import os
import aiohttp
from discord.ext import commands
import discord
import requests
import asyncio
from datetime import datetime, timedelta
from main import mongo
from cryptography.fernet import Fernet
import pathlib
import math
import math
import random
from mako.template import Template
import re
from keep_alive import app
from flask.views import MethodView
from lxml import html
from cryptography.fernet import Fernet
import dload
from csv import DictReader
import utils

key = os.getenv("encryption_key")
api_key = os.getenv("api_key")
convent_key = os.getenv("convent_api_key")
cipher_suite = Fernet(key)

class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def links(self, ctx):
        other = "[Role Guidelines](https://docs.google.com/document/d/1t0xxlafFyrM8MU8k_q3lcyD1R1f8DOsN60avSHNe8_s/edit#)\n[Official Church of Atom Charter](https://docs.google.com/document/d/1ayTELdfE9ogawwDv_14-q5k4NoLysCiUKOxAuWABqlM/edit)\n[Church alliance page](https://politicsandwar.com/alliance/id=4729)\n[Convent alliance page](https://politicsandwar.com/alliance/id=7531)\n[Convent join page](https://politicsandwar.com/alliance/join/id=7531)\n"
        milcom = "[Raiding Guide](https://docs.google.com/document/d/1a5xWQUKVH8-vJmBdXgQVUpR_U-DhLwPWMPjPvEVTFqQ/edit#)\n[CTO](https://ctowned.net)\n[Slotter](https://slotter.bsnk.dev/search)\n[WarNet Plus](https://plus.bsnk.dev)"
        ia = "[CoA's Guide to P&W](https://docs.google.com/document/u/1/d/1lrPGQpaAGygRCmZP1U6y5S2ryzMApByPagFNUzdwtJU/edit#)\n[Nations sheet](https://fuquiem.karemcbob.repl.co/sheet)\n[Multi-Buster Tool](https://politicsandwar.com/index.php?id=178)\n"
        fa = "[Discord invite link](https://discord.gg/uszcTxr)\n[FA Discord invite link](https://discord.gg/dZ9u53Tqpm)\n"
        embed = discord.Embed(title='Links:', description="", color=0x00ff00)
        embed.add_field(name="Internal Affairs", value=ia)
        embed.add_field(name="Military Affairs", value=milcom)
        embed.add_field(name="Foreign Affairs", value=fa)
        embed.add_field(name="Other", value=other)
        await ctx.send(embed=embed)

    async def change_perm(self, message, api_nation, level: str):
        if api_nation['allianceposition'] > '2':
            if message:
                await message.edit(content="I cannot let you change the perms of a person of such high ranking!")
            return {}
        if api_nation['allianceid'] == '4729':
            admin_id = 465463547200012298
        elif api_nation['allianceid'] == '7531':
            admin_id = 154886766275461120
        else:
            if message:
                await message.edit(content='They are not affiliated with the Church nor the Convent!')
            return {}
        admin = await utils.find_user(self, admin_id)
        if admin['email'] == '' or admin['pwd'] == '':
            if message:
                await message.edit(content='The admin has not registered their PnW credentials with Fuquiem.')
            return {}

        cipher_suite = Fernet(key)

        with requests.Session() as s:
            login_url = "https://politicsandwar.com/login/"
            login_data = {
                "email": str(cipher_suite.decrypt(admin['email'].encode()))[2:-1],
                "password": str(cipher_suite.decrypt(admin['pwd'].encode()))[2:-1],
                "loginform": "Login"
            }
            s.post(login_url, data=login_data)

            withdraw_url = f"https://politicsandwar.com/alliance/id={api_nation['allianceid']}"
            withdraw_data = {
                "nationperm": api_nation['leadername'],
                "level": level,
                "permsubmit": 'Go',
            }
            s.post(withdraw_url, data=withdraw_data)

            if requests.get(f"http://politicsandwar.com/api/nation/id={api_nation['nationid']}&key=e5171d527795e8").json()['allianceposition'] == level:
                if message:
                    await message.edit(content='Their status was successfully changed.')
                await asyncio.sleep(2)
            else:
                if message:
                    await message.edit(content=f"I might have failed at changing their status, check their nation page to be sure: https://politicsandwar.com/nation/id={api_nation['nationid']}")
                return {}

    @commands.command(aliases=['message'], brief="Send a premade message to someone")
    @commands.has_any_role('Internal Affairs')
    async def msg(self, ctx, arg):
        message = await ctx.send("Working on it..")

        nation = await utils.find_nation(arg)
        if nation == None:
            nation = await utils.find_user(self, arg)
            if nation == {}:
                await message.edit(content='I could not find that nation!')
                return
            else:
                nation = await utils.find_nation(nation['nationid'])
                if nation == None:
                    await message.edit(content='I could not find that nation!')
                    return

        msg_hist = mongo.message_history.find_one({"nationid": nation['nationid']})

        api_nation = requests.get(f"http://politicsandwar.com/api/nation/id={nation['nationid']}&key=e5171d527795e8").json()

        invoker = await utils.find_user(self, ctx.author.id)
        if invoker == {}:
            await message.edit(content='I could not find you in the database!')
            return
        name = invoker['leader']
            
        pontifex = ctx.guild.get_role(434258420456095744)
        primus = ctx.guild.get_role(484572512731136001)
        cardinal = ctx.guild.get_role(434258149474697216)
        acolyte = ctx.guild.get_role(434258659288154112)
        deacon = ctx.guild.get_role(790688418429665300)
        roles = ctx.author.roles

        if pontifex in roles:
            title = "Pontifex Atomicus"
        elif primus in roles:
            title = "Primus Inter Pares"
        elif cardinal in roles:
            title = "Cardinal of Internal Affairs"
        elif acolyte in roles:
            title = "Acolyte of Internal Affairs"
        elif deacon in roles:
            title = "Deacon of Internal Affairs"

        embed = discord.Embed(title=f"Type of message", description="Do you want to send a message about...\n\n:one: - removal from our applicant pool\n:two: - closing a ticket\n:three: - them having to join the discord\n:four: - them being moved to applicant due to inactivity", color=0x00ff00)
        await message.edit(content="", embed=embed)

        react01 = asyncio.create_task(message.add_reaction("1\N{variation selector-16}\N{combining enclosing keycap}"))
        react02 = asyncio.create_task(message.add_reaction("2\N{variation selector-16}\N{combining enclosing keycap}"))
        react03 = asyncio.create_task(message.add_reaction("3\N{variation selector-16}\N{combining enclosing keycap}"))
        react04 = asyncio.create_task(message.add_reaction("4\N{variation selector-16}\N{combining enclosing keycap}"))
        await asyncio.gather(react01, react02, react03, react04)

        dm = False
        user = mongo.users.find_one({"nationid": api_nation['nationid']})

        async def discord_dm():
            nonlocal dm, ctx, user, message
            if user == None:
                await message.edit(content="Do you want to cancel this process and add them to the db? Then I can attempt to DM them on discord. (y/n)")
                try:
                    while True:
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=60)
                        if msg.content.lower() in ['yes', 'y']:
                            await msg.delete()
                            await message.edit(content="I canceled this process, now you can use $dba to add them to the database.")
                            return {}
                        elif msg.content.lower() in ['no', 'n']:
                            await msg.delete()
                            await message.edit(content="Alright, I'll keep on going then.")
                            await asyncio.sleep(2)
                            break
                except asyncio.TimeoutError:
                    await message.edit(content='Command timed out, you were too slow to respond.')
                    return {}
            else:
                await message.edit(content="Do you want me to DM them on discord? (y/n)")
                try:
                    while True:
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=60)
                        if msg.content.lower() in ['yes', 'y']:
                            await msg.delete()
                            dm = True
                            await message.edit(content="Alright, will do.")
                            await asyncio.sleep(2)
                            break
                        elif msg.content.lower() in ['no', 'n']:
                            await msg.delete()
                            await message.edit(content="Calm your tits, no reason to be rude. I suppose I won't do that then.")
                            await asyncio.sleep(2)
                            break
                except asyncio.TimeoutError:
                    await message.edit(content='Command timed out, you were too slow to respond.')
                    return {}

        async def last_message(variant):
            nonlocal ctx, message, msg_hist
            if msg_hist == None:
                return
            #print(msg_hist)
            relevant_msg_hist = [x for x in msg_hist['log'] if x['variant'] == variant]
            if len(relevant_msg_hist) > 0:
                message_content = "A message with regards to this was sent by"
                n = 0
                for x in relevant_msg_hist:
                    n += 1
                    sender = await self.bot.fetch_user(x['sender'])
                    message_content += f" `{sender}` <t:{x['epoch']}:R>"
                    if len(relevant_msg_hist) - n == 1:
                        message_content += " and"
                    elif len(relevant_msg_hist) - n == 0:
                        message_content += ""
                    else:
                        message_content += ","
                message_content += ". Do you want to continue?"
                await message.edit(content=message_content)
                try:
                    while True:
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=60)
                        if msg.content.lower() in ['yes', 'y']:
                            await msg.delete()
                            await message.edit(content="Continue I shall.")
                            await asyncio.sleep(2)
                            break
                        elif msg.content.lower() in ['no', 'n']:
                            await msg.delete()
                            await message.edit(content="Canceled by user.")
                            return {}
                except asyncio.TimeoutError:
                    await message.edit(content='Command timed out, you were too slow to respond.')
                    return {}

        while True:
            reaction, reacting_user = await self.bot.wait_for("reaction_add", timeout=300)
            if reaction.message != message or reacting_user.id != ctx.author.id:
                continue

            if str(reaction.emoji) == "1\N{variation selector-16}\N{combining enclosing keycap}":
                variant = 1
                await message.edit(embed=None, content="Thinking...")
                await message.clear_reactions()
                res = await last_message(variant)
                if res == {}:
                    return
                if api_nation['allianceposition'] == '1':
                    try:
                        while True:
                            await message.edit(content=f"I noticed that {api_nation['leadername']} of {api_nation['name']} (<https://politicsandwar.com/nation/id={api_nation['nationid']}>) is currently an applicant, do you want me to remove them?")
                            msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=60)

                            if msg.content.lower() in ['yes', 'y']:
                                await msg.delete()
                                await message.edit(content='I will attempt to change their status.')
                                await asyncio.sleep(2)
                                res = await self.change_perm(message, api_nation, "0")
                                if res == {}:
                                    return
                                break
                            elif msg.content.lower() in ['no', 'n']:
                                await msg.delete()
                                await message.edit(content='I will not change their status.')
                                await asyncio.sleep(2)
                                return

                    except asyncio.TimeoutError:
                        await ctx.send('Command timed out, you were too slow to respond.')
                        return
               
                elif api_nation['allianceposition'] > '1':
                    await message.edit(content="They are a member, not an applicant!")
                    return

                res = await discord_dm()
                if res == {}:
                    return
                subject = "Removal from our applicant pool, sorry!"
                text = f"Hi {nation['leader']},\n\nWe do our best to defend our applicants, but your inactivity leads us to believe that you are incapable of winning any attacks against your nation. We have therefore decided to retract your status as an applicant to our alliance. If you ever turn active again, you are welcome to re-apply.\n\nPlease follow these steps if you wish to re-apply:\n1) Apply in-game <a href=\"https://politicsandwar.com/alliance/join/id=7531\">here</a>\n2) Join our discord <a href=\"https://discord.gg/uszcTxr\">here</a>\n3) There is a channel called #apply-here in our discord server. Go there and create a ticket. We will take care of it from there!\n\nSent on behalf of\n{name}, {title}\n{str(ctx.author)} on discord"
                break

            elif str(reaction.emoji) == "2\N{variation selector-16}\N{combining enclosing keycap}":
                variant = 2
                await message.edit(embed=None, content="Thinking...")
                await message.clear_reactions()
                res = await last_message(variant)
                if res == {}:
                    return
                res = await discord_dm()                
                if res == {}:
                    return
                subject = "Application ticket closed, sorry!"
                text = f"Hi {nation['leader']},\n\nYour application ticket to the Convent of Atom has been closed because you haven't completed the application process and have been inactive for more than 48 hours. If you wish to continue your application, you can create a new ticket. Let me know if you have any questions, or need help with anything.\n\nSent on behalf of\n{name}, {title}\n{str(ctx.author)} on discord"
                break
                
            elif str(reaction.emoji) == "3\N{variation selector-16}\N{combining enclosing keycap}":
                variant = 3
                await message.edit(embed=None, content="Thinking...")
                await message.clear_reactions()
                res = await last_message(variant)
                if res == {}:
                    return
                subject = "Incomplete application, please complete it!"
                text = f"Hi {nation['leader']},\n\nI can see that you are currently applying to our alliance. Please note that you have to apply on discord as well in order to become a member.\n\nJoin the Church of Atom discord <a href=\"https://discord.gg/uszcTxr\">here</a>. After joining the discord, go to the channel called #apply-here to create an application ticket.\n\nLet me know if you have any questions.\n\nSent on behalf of\n{name}, {title}\n{str(ctx.author)} on discord"
                break

            elif str(reaction.emoji) == "4\N{variation selector-16}\N{combining enclosing keycap}":
                variant = 4
                await message.edit(embed=None, content="Thinking...")
                await message.clear_reactions()
                res = await last_message(variant)
                if res == {}:
                    return
                try:
                    while True:
                        await message.edit(content=f"I noticed that {api_nation['leadername']} of {api_nation['name']} (<https://politicsandwar.com/nation/id={api_nation['nationid']}>) is currently a member, do you want me to move them to applicant?")
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=60)

                        if msg.content.lower() in ['yes', 'y']:
                            await msg.delete()
                            await message.edit(content='I will attempt to change their status.')
                            await asyncio.sleep(2)
                            res = await self.change_perm(message, api_nation, "1")
                            if res == {}:
                                return
                            break
                        elif msg.content.lower() in ['no', 'n']:
                            await msg.delete()
                            await message.edit(content='I will not change their status.')
                            await asyncio.sleep(2)
                            break

                except asyncio.TimeoutError:
                    await ctx.send('Command timed out, you were too slow to respond.')
                    return
                
                res = await discord_dm()
                if res == {}:
                    return
                subject = "Moved to applicant status, check in on discord!"
                text = f"Hi {nation['leader']},\n\nIf a member loses a war, the alliance bank is looted. Due to your inactivity, we are worried that you might lose if you were to be attacked. To avoid the bank being looted, we have therefore decided to change your ingame status from member to applicant. Please note that you are still a member on discord. All you need to do to get repromoted ingame is to reach out to us and let us know that you are once again active.\n\nLet me know if you have any questions.\n\nSent on behalf of\n{name}, {title}\n{str(ctx.author)} on discord"
                break

        await message.edit(embed=None, content=f"Do you want to send {nation['leader']} of {nation['nation']} (<https://politicsandwar.com/nation/id={nation['nationid']}>) this message? (y/n)\n\n```{text}```")
        try:
            while True:
                msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=60)
                if msg.content.lower() in ['yes', 'y']:
                    await msg.delete()
                    res = requests.post('https://politicsandwar.com/api/send-message/', data={'key': api_key, 'to': api_nation['nationid'], 'subject': subject, 'message': text})
                    if res.status_code == 200:
                        await message.edit(content="Ingame message was sent!")
                    else:
                        await message.edit(content=f"Error {res.status_code} Ingame message was not sent!")
                    break
                elif msg.content.lower() in ['no', 'n']:
                    await msg.delete()
                    await message.edit(content='Sending of message was canceled.')
                    break
        except asyncio.TimeoutError:
            await message.edit(content='Command timed out, you were too slow to respond.')
            return
        
        if dm:
            dm_chan = await self.bot.fetch_user(user['user'])
            try:
                await dm_chan.send(text)
                await ctx.send("DM was successfuly sent!")
            except discord.errors.Forbidden:
                await ctx.send(f"{dm_chan} doesn't accept my DMs <:sadcat:787450782747590668>")
            except Exception as error:
                await ctx.send(f"Some error occured, so I couldn't DM them <:sadcat:787450782747590668>\n\n```{error}```")
        
        mongo.message_history.find_one_and_update({"nationid": nation['nationid']}, {"$push": {"log": {"sender": ctx.author.id, "epoch": round(datetime.now().timestamp()), "dm": dm, "variant": variant}}}, upsert=True)
        
    @commands.command(brief='Displays a list the 25 first people sorted by shortest timer', help='Accepts an optional argument "convent"', aliases=['ct', 'citytimers', 'timers', 'timer'])
    async def citytimer(self, ctx, aa='church'):
        aa.lower()
        if aa in 'church':
            nations = requests.get(
                f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}').json()['nations']
        elif aa in 'convent':
            nations = requests.get(
                f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}').json()['nations']
        else:
            ctx.send('That was not a valid alliance, please try again.')
            return

        embed = discord.Embed(title='City timers:', description='Here is up to 25 people sorted by the shortest timer:',
                              color=0x00ff00, timestamp=datetime.utcnow())
        people = sorted(nations, key=lambda k: k['turns_since_last_city'], reverse=True)
        content = ''
        n = 1
        for x in people:
            if n < 25:
                content = f"[{x['leader']}](https://politicsandwar.com/nation/id={x['nationid']}) has {120-x['turns_since_last_city']} turns"
                embed.add_field(name='\u200b', value=content, inline=False)
                n += 1
            else:
                break
        await ctx.send(embed=embed)

    @commands.command(brief='Displays a list the 25 first people sorted by shortest timer', help='Accepts an optional argument "convent"', aliases=['pt', 'projecttimers'])
    async def projecttimer(self, ctx, aa='church'):
        aa.lower()
        if aa in 'church':
            nations = requests.get(
                f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}').json()['nations']
        elif aa in 'convent':
            nations = requests.get(
                f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}').json()['nations']
        else:
            ctx.send('That was not a valid alliance, please try again.')
            return

        embed = discord.Embed(title='Project timers:', description='Here is up to 25 people sorted by the shortest timer:',
                              color=0x00ff00, timestamp=datetime.utcnow())
        people = sorted(nations, key=lambda k: k['turns_since_last_project'], reverse=True)
        content = ''
        n = 1
        for x in people:
            if n < 25:
                content = f"[{x['leader']}](https://politicsandwar.com/nation/id={x['nationid']}) has {120-x['turns_since_last_project']} turns"
                embed.add_field(name='\u200b', value=content, inline=False)
                n += 1
            else:
                break
        await ctx.send(embed=embed)

    @commands.command(brief='Show all your active beige reminders', help='', aliases=['alerts', 'rems'])
    async def reminders(self, ctx):
        message = await ctx.send('Fuck requiem...')
        person = mongo.users.find_one({"user": ctx.author.id})
        #print(person)
        if person == None:
            await message.edit(content="I cannot find you in the database!")
        insults = ['ha loser', 'what a nub', 'such a pleb', 'get gud', 'u suc lol']
        insult = random.choice(insults)
        if person['beige_alerts'] == []:
            await message.edit(content=f"You have no beige reminders!\n\n||{insult}||")
            return
        reminders = ""
        person['beige_alerts'] = sorted(person['beige_alerts'], key=lambda k: k['time'], reverse=True)
        for x in person['beige_alerts']:
            reminders += (f"\n<t:{round(x['time'].timestamp())}> (<t:{round(x['time'].timestamp())}:R>) - <https://politicsandwar.com/nation/id={x['id']}>")
        await message.edit(content=f"Here are your reminders:\n{reminders}")
    
    @commands.command(brief='Delete a beige reminder', help='', aliases=['delalert', 'delrem', 'del_reminder'])
    async def delreminder(self, ctx, id):
        message = await ctx.send('Fuck requiem...')
        id = str(re.sub("[^0-9]", "", id))
        person = mongo.users.find_one({"user": ctx.author.id})
        found = False
        for alert in person['beige_alerts']:
            if alert['id'] == id:
                alert_list = person['beige_alerts'].remove(alert)
                if not alert_list:
                    alert_list = []
                mongo.users.find_one_and_update({"user": person['user']}, {"$set": {"beige_alerts": alert_list}})
                found = True
        if not found:
            await message.edit(content="I did not find a reminder for that nation!")
        await message.edit(content=f"Your beige reminder for https://politicsandwar.com/nation/id={id} was deleted.")

    @commands.command(brief='Add a beige reminder', help='', aliases=['ar', 'remindme', 'addreminder', 'add_reminder'])
    async def remind(self, ctx, arg):
        message = await ctx.send('Fuck requiem...')
        nation = await utils.find_nation(arg)
        if nation == None:
            await message.edit(content='I could not find that nation!')
            return
        #print(nation)
        res = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{nation['nationid']}){{data{{beigeturns}}}}}}"}).json()['data']['nations']['data'][0]
        if res['beigeturns'] == 0:
            await message.edit(content="They are not beige!")
            return
        reminder = {}
        #print(data)
        turns = int(res['beigeturns'])
        time = datetime.utcnow()
        if time.hour % 2 == 0:
            time += timedelta(hours=turns*2)
        else:
            time += timedelta(hours=turns*2-1)
        reminder['time'] = datetime(time.year, time.month, time.day, time.hour)
        reminder['id'] = str(nation['nationid'])
        mongo.users.find_one_and_update({"user": ctx.author.id}, {"$push": {"beige_alerts": reminder}})
        await message.edit(content=f"A beige reminder for https://politicsandwar.com/nation/id={nation['nationid']} was added.")

    @commands.command(brief='When Deacons audit someone they can use "$audited <personyoujustaudited>" to register this to the spreadsheet')
    @commands.has_any_role('Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def audited(self, ctx, person):
        person = await utils.find_user(self, person)
        if person['audited']:
            try:
                await ctx.send(f"Are you sure you want to change `{await self.bot.fetch_user(person['user'])}`'s `audited` attribute from `{person['audited']}` to `{ctx.author.name}`?")
                msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=40)

                if msg.content.lower() in ['yes', 'y']:
                    mongo.users.find_one_and_update({"user": person['user']}, {'$set': {'audited': ctx.author.name}})
                    await ctx.send(f"`{await self.bot.fetch_user(person['user'])}`'s `audited` attribute was changed from `{person['audited']}` to `{ctx.author.name}`.")
                    return
                elif msg.content.lower() in ['no', 'n']:
                    await ctx.send('Changes were canceled.')
                    return
            except asyncio.TimeoutError:
                await ctx.send('Command timed out, you were too slow to respond.')
        else:
            mongo.users.find_one_and_update({"user": person['user']}, {'$set': {'audited': ctx.author.name}})
            await ctx.send(f"`{await self.bot.fetch_user(person)}`'s `audited` attribute was added as `{ctx.author.name}`.")


    @commands.command(aliases=['trades', 'trader', 'traders'],brief='A list of the 10 traders with the largest amount of the resource you specify')
    @commands.has_any_role('Pupil', 'Zealot', 'Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def trade(self, ctx, resource):
        resource = resource.lower()
        church = requests.get(
            f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}').json()
        convent = requests.get(
            f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}').json()
        nations = church['nations'] + convent['nations']
        current = current = list(mongo['users'].find({}))
        rss = ['food', 'coal', 'oil', 'uranium', 'bauxite',
               'iron', 'lead', 'gasoline', 'munitions', 'aluminum', 'steel']
        found = False
        role = ctx.guild.get_role(796057460502298684)

        for rs in rss:
            if resource in rs:
                resource = rs
                found = True
                break
        if not found:
            await ctx.send('That is not a valid resource!')
            return

        embed = discord.Embed(title=f'Traders with {resource}:', description='',
                              color=0x00ff00, timestamp=datetime.utcnow())

        people = sorted(nations, key=lambda k: float(k[resource]), reverse=True)
        n = 0
        for person in people:
            if n == 10:
                break
            for x in current:
                if x['nationid'] == str(person['nationid']):
                    user = ctx.guild.get_member(x['user'])
                    if user == None:
                        continue
                    if role in user.roles:
                        embed.add_field(name=user,value=f"[They](https://politicsandwar.com/nation/id={person['nationid']}) have {person[resource]} {resource}",inline=False)
                        n += 1
        await ctx.send(embed=embed)
                            
    @commands.command(brief='Shows a list of alliances with treasures')
    async def treasures(self, ctx):
        res = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{treasures{{bonus spawndate nation{{id alliance_position num_cities score nation_name alliance{{name id}}}}}}}}"}).json()['data']['treasures']
        embed = discord.Embed(title=f'Treasures', description='',
                              color=0x00ff00, timestamp=datetime.utcnow())
        n = 0
        for x in res:
            if n == 25:
                await ctx.send(embed=embed)
                embed.clear_fields()
                n = 0
            seconds = (datetime.strptime(x['spawndate'], "%Y-%m-%d") - datetime.utcnow()).total_seconds() + 60 * 24 * 60 * 60
            days = round(seconds / (24 * 3600))
            embed.add_field(name=f"{x['nation']['nation_name']}", value=f"[Link to nation](https://politicsandwar.com/nation/id={x['nation']['id']})\nRespawn in {days} days\n{x['bonus']}% bonus\nC{x['nation']['num_cities']}, {round(x['nation']['score'])} score\n{x['nation']['alliance_position'].lower().capitalize()} of [{x['nation']['alliance']['name']}](https://politicsandwar.com/alliance/id={x['nation']['alliance']['id']})")
            n += 1
        if len(embed.fields) > 0:
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"I didn't find anything!")
    
    @commands.command(brief='Send an informative message')
    @commands.has_any_role('Internal Affairs')
    async def welcome(self, ctx, arg):
        user = await utils.find_user(self, arg)
        dm_chan = ctx.guild.get_member(user['user'])
        content = ""
        heathen_role = ctx.guild.get_role(434248817005690880)
        pupil_role = ctx.guild.get_role(711385354929700905)
        try:
            await dm_chan.remove_roles(heathen_role)
            content += "Removed `Heathen`.\n"
        except:
            content += "Did not remove `Heathen`, did they not have it in the first place?\n"
        try:
            await dm_chan.add_roles(pupil_role)
            content += "Added `Pupil`.\n"
        except:
            content += "Did not add `Pupil`, did they have it already?\n"
        try:
            response = requests.get(f"http://politicsandwar.com/api/nation/id={user['nationid']}&key=e5171d527795e8").json()
            if response['allianceposition'] > '1':
                content += "Did not admit them. They are already a member.\n"
            elif response['allianceposition'] < '1':
                content += "Did not admit them. They are not an applicant.\n"
            else:
                res = await self.change_perm(None, response, "2")
                if res == {}:
                    content += "Did (probably) not admit them. Are Randy's credentials wrong?\n"
                else:
                    content += "Admitted them to the in-game alliance.\n"
        except:
            content += "Did (probably) not admit them. Is the API broken?\n"
        message = f"Hey, {dm_chan.name}!\n\nFirst of all, welcome to the Convent! If you are wondering who I am, wonder no more! I am but one of Randy's slaves. He keeps me locked up in his basement, and he doesn't feed me if I don't do as he says. I'm not sure about the legality of it all, but seeing as I'm locked up, there's really not a lot I can do about it. Anyhow, it's time for some practical information!\n\nAn overview of the channels can be found here: https://discord.com/channels/434071714893398016/838342085031231508/844978316868190248\nRole explanations and chain of command can be found here: https://discord.com/channels/434071714893398016/838342085031231508/849229725025173554\n\nWhen it comes to educational material, we have a couple guides. The raiding guide is by far the best one, and the one you should prioritize reading.\nOur raiding guide: <https://docs.google.com/document/d/1a5xWQUKVH8-vJmBdXgQVUpR_U-DhLwPWMPjPvEVTFqQ/edit#heading=h.jgynban3l6c3>\nOur general guide: <https://docs.google.com/document/d/1lrPGQpaAGygRCmZP1U6y5S2ryzMApByPagFNUzdwtJU/edit?usp=sharing>\nHow to automate rewarded ads and get $2 million daily for free: <https://www.youtube.com/watch?v=N71RrRfztv4>\n\nOn the topic of free money, you can go to <#850302301838114826> and type $login to sign up for the daily raffle. The size and number of prizes depends on the number of people which have signed up. If there are less than 5 people, the prize is $2.5 million. If there are more than 5 people, the prize is $5 million. If there are more than 20 people signed up, there will be 2 winners of $5 million. If you get the raffle reminders role in <#688464249932349607>, I'll make sure to DM you a few hours before the raffle ends (if you haven't signed up yet).\n\nThat's all for now! If you have any questions, you can go to <#853361013361737809> or <#849362037003124757>. I will get in touch again if I ever notice anything wrong with your nation, but until then; have fun - and praise Atom!"
        try:
            await dm_chan.send(message)
            content += "DMed them practical information.\n"
        except:
            content += "Did not DM them practical information. Are they not accepting DMs?\n"
        await ctx.send(content)

    @commands.command(brief='Admits an applicant, accepts 1 argument')
    @commands.has_any_role('Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def admit(self, ctx, arg):
        message = await ctx.send("<:thonk:787399051582504980>")
        nation = await utils.find_nation_plus(arg)
        if nation == None:
            await message.edit(content="Run $update or wait until daychange")
            return
        response = requests.get(
            f"http://politicsandwar.com/api/nation/id={nation['nationid']}&key=e5171d527795e8").json()
        if response['allianceposition'] > '1':
            await ctx.send('They are already a member!')
            return
        elif response['allianceposition'] < '1':
            await ctx.send('They are not an applicant!')
            return
        try:
            await message.edit(content=f"Are you sure that you want to promote {response['leadername']} of {response['name']} (<https://politicsandwar.com/nation/id={response['nationid']}>) to member?")
            msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=60)

            if msg.content.lower() in ['yes', 'y']:
                await msg.delete()
                await message.edit(content='I will attempt to change their status.')
                await asyncio.sleep(2)
                res = await self.change_perm(message, response, "2")
                if res == {}:
                    return
            elif msg.content.lower() in ['no', 'n']:
                await msg.delete()
                await message.edit(content='I will not change their status.')
                await asyncio.sleep(2)
                return
        except asyncio.TimeoutError:
            await ctx.send('Command timed out, you were too slow to respond.')
            return
        
    @commands.command(brief='Shows information about applicants', aliases=['apps'])
    @commands.has_any_role('Pupil', 'Zealot', 'Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def applicants(self, ctx):
        message = await ctx.send("Finding plebs...")

        heathen_role = ctx.guild.get_role(584676265932488705)
        pupil_role = ctx.guild.get_role(711385354929700905)
        zealot_role = ctx.guild.get_role(434258764221251584)

        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{tradeprices(limit:1){{coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}}}"}) as temp:
                prices = (await temp.json())['data']['tradeprices'][0]
                prices['money'] = 1
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(page:1 alliance_position:1 first:500 alliance_id:4729){{data{{id leader_name nation_name alliance{{name}} color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium cities{{infrastructure barracks factory airforcebase drydock}}}}}}}}"}) as temp:
                apps = (await temp.json())['data']['nations']['data']
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={convent_key}", json={'query': f"{{nations(page:1 alliance_position:1 first:500 alliance_id:7531){{data{{id leader_name nation_name alliance{{name}} color num_cities score vmode beigeturns last_active soldiers tanks aircraft ships missiles nukes aluminum bauxite coal food gasoline iron lead money munitions oil steel uranium cities{{infrastructure barracks factory airforcebase drydock}}}}}}}}"}) as temp:
                apps += (await temp.json())['data']['nations']['data']

        for app in apps:
            app['last_active'] = f"<t:{round(datetime.strptime(app['last_active'], '%Y-%m-%d %H:%M:%S').timestamp())}:R>"

        apps = sorted(apps, key=lambda k: k['last_active'], reverse=True)
        fields = []

        for app in apps:
            on_hand = 0
            try:
                for rs in ['aluminum', 'bauxite', 'coal', 'food', 'gasoline', 'iron', 'lead', 'money', 'munitions', 'oil', 'steel', 'uranium']:
                    on_hand += app[rs] * prices[rs]
            except:
                pass
            res = mongo.users.find_one({"nationid": app['id']})
            if res == None:
                res = mongo.leaved_users.find_one({"nationid": app['id']})
                if res == None:
                    db = "Not registered"
                else:
                    db = "**Secondary database**"
            else:
                db = "**Primary database**"

            disc = ""
            if "**" in db:
                try:
                    member = ctx.guild.get_member(res['user'])
                    if zealot_role in member.roles:
                        disc = zealot_role.mention
                    elif pupil_role in member.roles:
                        disc = pupil_role.mention
                    elif heathen_role in member.roles:
                        disc = heathen_role.mention
                except:
                    pass
            fields.append({"name": app['leader_name'], "value": f"[{app['nation_name']}](https://politicsandwar.com/nation/id={app['id']})\n{app['alliance']['name'][:app['alliance']['name'].find(' ')]}\n{db} {disc}\nLast active: {app['last_active']}\nCities: {app['num_cities']}\nValue of rss: ${round(on_hand):,}"})

        embeds = utils.embed_pager("Applicants", fields)

        await message.edit(content="", embed=embeds[0])
        await utils.reaction_checker(self, message, embeds)

    @commands.command(aliases=['builds'], brief="Shows you the best city builds", help="After calling the command, you have to tell Fuquiem 3 things. 1) How much infra you want. 2) How much land you want. 3) What MMR you want. When you're done with this, Fuquiem will link to a webpage showing the best builds for producing every resource. Note that these are the best builds for YOU and YOU only! I takes your projects and continent into consideration when calculating the revenue of each build. When calling the command, you can therefore supply a person for whom you want the builds to be calculated for. IMPORTANT! - This tool only shows builds that are currently being used somewhere in Orbis. This means that you may very well be able to improve upon these builds. It's worth mentioning that even though this shows the best builds for producing every type of resource (except for the ones you can't produce due to continent restrictions), the \"best build for net income\" is in reality best for every resource. This is because the higher monetary income lets you buy more of a resource than you could get by producing it. Another important thing to mention, is that the monetary net income is dependent on market prices. This means that in times of war, manufactured resources will increase in price, increasing the profitability of builds producing these resources. The \"best\" build for net income may therefore not always be the same.")
    @commands.has_any_role('Pupil', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def build(self, ctx, arg_infra: str = None, arg_land: str = None, arg_mmr: str = None, person: str = None):
        now = datetime.now()
        yesterday = now + timedelta(days=-1)
        date = yesterday.strftime("%Y-%m-%d")
        if os.path.isfile(pathlib.Path.cwd() / 'data' / 'dumps' / 'cities' / f'cities-{date}.csv'):
            print('That file already exists')
        else:
            dload.save_unzip(f"https://politicsandwar.com/data/cities/cities-{date}.csv.zip", str(
                pathlib.Path.cwd() / 'data' / 'dumps' / 'cities'), True)
        
        message = await ctx.send('Stay with me...')
        if person == None:
            person = ctx.author.id
        db_nation = await utils.find_user(self, person)

        if db_nation == {}:
            try:
                db_nation = list(mongo.world_nations.find({"nation": person}).collation(
                    {"locale": "en", "strength": 1}))[0]
            except:
                try:
                    db_nation = list(mongo.world_nations.find({"leader": person}).collation(
                        {"locale": "en", "strength": 1}))[0]
                except:
                    try:
                        person = int(re.sub("[^0-9]", "", person))
                        db_nation = list(mongo.world_nations.find({"nationid": person}).collation(
                            {"locale": "en", "strength": 1}))[0]
                    except:
                        db_nation = None
            if not db_nation:
                await message.edit(content='I could not find that person!')
                return
        
        nation = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{db_nation['nationid']}){{data{{id continent date color dompolicy alliance{{name}} alliance_id num_cities ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap}}}}}}"}).json()['data']['nations']['data']
        if len(nation) == 0:
            await message.edit(content="That person was not in the API!")
            return
        else:
            nation = nation[0]
        
        if not arg_infra:
            embed = discord.Embed(title=f"Infrastructure", description="How much infrastructure do you want the build to be for?\n\nex. \"1500\"\nex. \"2.5k\"\nex. \"any\"", color=0x00ff00)
            await message.edit(content="", embed=embed)

        while True:
            try:
                if not arg_infra:
                    command = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=600)
                    infra = command.content
                    text = command.content
                else:
                    infra = arg_infra
                    text = arg_infra
                try:
                    if "." in infra:
                        num_inf = re.sub("[A-z]", "", infra)
                        infra = int(num_inf.replace(".", "")) / 10**(len(num_inf) - num_inf.rfind(".") - 1)
                except:
                    if not arg_infra:
                        await message.edit(content="**I did not understand that, please call the command again!**")
                        return
                    else:
                        await message.edit(content="**I did not understand that, please try again!**")
                        continue

                if "k" in text:
                    infra = int(float(re.sub("[A-z]", "", str(infra))) * 1000)
                else:
                    try:
                        infra = int(infra)
                    except:
                        if not arg_infra:
                            await message.edit(content="**I did not understand that, please call the command again!**")
                            return
                        else:
                            await message.edit(content="**I did not understand that, please try again!**")
                            continue

                if not isinstance(infra, int) and str(infra).lower() not in "any":
                    await message.edit(content="**I did not understand that, please try again!**")
                    continue

                if not arg_infra:
                    await command.delete()
                break

            except asyncio.TimeoutError:
                await message.edit(content="**Command timed out!**")
                print('message break')
                break

        if not arg_land:
            embed = discord.Embed(title=f"Land", description="How much land should I assume the cities to have when calculating their revenue?\n\nex. \"1500\"\nex. \"2.5k\"", color=0x00ff00)
            await message.edit(content="", embed=embed)

        while True:
            try:
                if not arg_land:
                    command = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=600)
                    land = command.content
                    text = command.content
                else:
                    land = arg_land
                    text = arg_land
                try:
                    if "." in land:
                        num_land = re.sub("[A-z]", "", land)
                        land = int(num_land.replace(".", "")) / 10**(len(num_land) - num_land.find(".") + num_land.rfind(".") - 2)
                except:
                    if not arg_land:
                        await message.edit(content="**I did not understand that, please call the command again!**")
                        return
                    else:
                        await message.edit(content="**I did not understand that, please try again!**")
                        continue

                if "k" in text:
                    land = int(float(re.sub("[A-z]", "", str(land))) * 1000)
                else:
                    try:
                        land = int(land)
                    except:
                        if not arg_land:
                            await message.edit(content="**I did not understand that, please call the command again!**")
                            return
                        else:
                            await message.edit(content="**I did not understand that, please try again!**")
                            continue

                if not arg_infra:
                    await command.delete()
                break

            except asyncio.TimeoutError:
                await message.edit(content="**Command timed out!**")
                print('message break')
                break

        if not arg_mmr:
            embed = discord.Embed(title=f"MMR", description="What should the minimum military requirement be?\n\nex. \"1/2/5/1\"\nex. \"0351\"\nex. \"any\"", color=0x00ff00)
            await message.edit(content="", embed=embed)

        while True:
            try:
                if not arg_mmr:
                    command = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=600)
                    mmr = command.content
                    await command.delete()
                else:
                    mmr = arg_mmr
                try:
                    if mmr.lower() == "any":
                        pass
                    else:
                        mmr = re.sub("[^0-9]", "", mmr)
                        min_bar = int(mmr[0])
                        min_fac = int(mmr[1])
                        min_han = int(mmr[2])
                        min_dry = int(mmr[3])
                    break
                except:
                    if not arg_mmr:
                        await message.edit(content="**I did not understand that, please call the command again!**")
                        return
                    else:
                        await message.edit(content="**I did not understand that, please try again!**")
                        continue
            except asyncio.TimeoutError:
                await message.edit(content="**Command timed out!**")
                print('message break')
                break
        await message.edit(content="Doing some filtering...", embed=None)
        
        to_scan = []
        rss = []
        all_rss = ['net income', 'aluminum', 'bauxite', 'coal', 'food', 'gasoline', 'iron', 'lead', 'money', 'munitions', 'oil', 'steel', 'uranium']
        if nation['continent'] == "af":
            cont_rss = ['coal_mines', 'iron_mines', 'lead_mines']
            rss = [rs for rs in all_rss if rs + "_mines" not in cont_rss and rs + "_wells" not in cont_rss]
        elif nation['continent'] == "as":
            cont_rss = ['coal_mines', 'bauxite_mines', 'lead_mines']
            rss = [rs for rs in all_rss if rs + "_mines" not in cont_rss and rs + "_wells" not in cont_rss]
        elif nation['continent'] == "au":
            cont_rss = ['oil_wells', 'iron_mines', 'uranium_mines']
            rss = [rs for rs in all_rss if rs + "_mines" not in cont_rss and rs + "_wells" not in cont_rss]
        elif nation['continent'] == "eu":
            cont_rss = ['oil_wells', 'bauxite_mines', 'uranium_mines']
            rss = [rs for rs in all_rss if rs + "_mines" not in cont_rss and rs + "_wells" not in cont_rss]
        elif nation['continent'] == "na":
            cont_rss = ['oil_wells', 'bauxite_mines', 'lead_mines']
            rss = [rs for rs in all_rss if rs + "_mines" not in cont_rss and rs + "_wells" not in cont_rss]
        elif nation['continent'] == "sa":
            cont_rss = ['coal_mines', 'iron_mines', 'uranium_mines']
            rss = [rs for rs in all_rss if rs + "_mines" not in cont_rss and rs + "_wells" not in cont_rss]

        with open(pathlib.Path.cwd() / 'data' / 'dumps' / 'cities' / f'cities-{date}.csv', encoding='cp437') as f1:
            csv_dict_reader = DictReader(f1)
            nation_age = nation['date'][:nation['date'].index(" ")]
            for city in csv_dict_reader:
                if str(infra).lower() not in "any":
                    if float(city['infrastructure']) != float(infra):
                        continue
                    if int(infra) / 50 < int(city['oil_power_plants']) + int(city['nuclear_power_plants']) + int(city['wind_power_plants']) + int(city['coal_power_plants']) + int(city['coal_mines']) + int(city['oil_wells']) + int(city['uranium_mines']) + int(city['iron_mines']) + int(city['lead_mines']) + int(city['bauxite_mines']) + int(city['farms']) + int(city['police_stations']) + int(city['hospitals']) + int(city['recycling_centers']) + int(city['subway']) + int(city['supermarkets']) + int(city['banks']) + int(city['shopping_malls']) + int(city['stadiums']) + int(city['oil_refineries']) + int(city['aluminum_refineries']) + int(city['steel_mills']) + int(city['munitions_factories']) + int(city['barracks']) + int(city['factories']) + int(city['hangars']) + int(city['drydocks']):
                        continue
                if str(mmr).lower() not in "any":
                    if int(city['barracks']) < min_bar:
                        continue
                    if int(city['factories']) < min_fac:
                        continue
                    if int(city['hangars']) < min_han:
                        continue
                    if int(city['drydocks']) < min_dry:
                        continue
                
                skip = False
                for mine in cont_rss:
                    if int(city[mine]) > 0:
                        skip = True
                        break
                if skip:
                    continue
                
                city.pop('\u2229\u2557\u2510city_id')
                city.pop('nation_id')
                city.pop('date_created')
                city.pop('name')
                city.pop('capital')
                city.pop('maxinfra')
                city.pop('last_nuke_date')

                city['powered'] = "am powered" #must be string to work when being in the webpage
                city['land'] = land
                city['date'] = nation_age
                city['infrastructure'] = round(float(city['infrastructure']))
                city['oilpower'] = int(city.pop('oil_power_plants'))
                city['windpower'] = int(city.pop('wind_power_plants'))
                city['coalpower'] = int(city.pop('coal_power_plants'))
                city['nuclearpower'] = int(city.pop('nuclear_power_plants'))
                city['coalmine'] = int(city.pop('coal_mines'))
                city['oilwell'] = int(city.pop('oil_wells'))
                city['uramine'] = int(city.pop('uranium_mines'))
                city['barracks'] = int(city.pop('barracks'))
                city['farm'] = int(city.pop('farms'))
                city['policestation'] = int(city.pop('police_stations'))
                city['hospital'] = int(city.pop('hospitals'))
                city['recyclingcenter'] = int(city.pop('recycling_centers'))
                city['subway'] = int(city.pop('subway'))
                city['supermarket'] = int(city.pop('supermarkets'))
                city['bank'] = int(city.pop('banks'))
                city['mall'] = int(city.pop('shopping_malls'))
                city['stadium'] = int(city.pop('stadiums'))
                city['leadmine'] = int(city.pop('lead_mines'))
                city['ironmine'] = int(city.pop('iron_mines'))
                city['bauxitemine'] = int(city.pop('bauxite_mines'))
                city['gasrefinery'] = int(city.pop('oil_refineries'))
                city['aluminumrefinery'] = int(city.pop('aluminum_refineries'))
                city['steelmill'] = int(city.pop('steel_mills'))
                city['munitionsfactory'] = int(city.pop('munitions_factories'))
                city['factory'] = int(city.pop('factories'))
                city['airforcebase'] = int(city.pop('hangars'))
                city['drydock'] = int(city.pop('drydocks'))

                to_scan.append(city)
        
        temp, colors, prices, treasures, radiation, seasonal_mod = await utils.pre_revenue_calc(mongo, cipher_suite, api_key, message, query_for_nation=False, parsed_nation=nation)

        await message.edit(content="Calculating revenue...")
        cities = []
        for city in to_scan:
            nation['cities'] = [city]
            cities.append(await utils.revenue_calc(message, nation, radiation, treasures, prices, colors, seasonal_mod, single_city=True))

        if len(cities) == 0:
            await message.edit(content="No active builds matched your criteria <:derp:846795730210783233>")
            return

        unique_builds = [dict(t) for t in {tuple(d.items()) for d in cities}]
        unique_builds = sorted(unique_builds, key=lambda k: k['net income'], reverse=True)
                        
        builds = {}
        for rs in rss:
            sorted_builds = sorted(unique_builds, key=lambda k: k[rs], reverse=True)
            best_builds = [city for city in sorted_builds if city[rs] == sorted_builds[0][rs]]
            builds[rs] = sorted(best_builds, key=lambda k: k['net income'], reverse=True)[0]
            builds[rs]['template'] = f"""
{{
    "infra_needed": {builds[rs]['infrastructure']},
    "imp_total": {math.floor(float(builds[rs]['infrastructure'])/50)},
    "imp_coalpower": {builds[rs]['coalpower']},
    "imp_oilpower": {builds[rs]['oilpower']},
    "imp_windpower": {builds[rs]['windpower']},
    "imp_nuclearpower": {builds[rs]['nuclearpower']},
    "imp_coalmine": {builds[rs]['coalmine']},
    "imp_oilwell": {builds[rs]['oilwell']},
    "imp_uramine": {builds[rs]['uramine']},
    "imp_leadmine": {builds[rs]['leadmine']},
    "imp_ironmine": {builds[rs]['ironmine']},
    "imp_bauxitemine": {builds[rs]['bauxitemine']},
    "imp_farm": {builds[rs]['farm']},
    "imp_gasrefinery": {builds[rs]['gasrefinery']},
    "imp_aluminumrefinery": {builds[rs]['aluminumrefinery']},
    "imp_munitionsfactory": {builds[rs]['munitionsfactory']},
    "imp_steelmill": {builds[rs]['steelmill']},
    "imp_policestation": {builds[rs]['policestation']},
    "imp_hospital": {builds[rs]['hospital']},
    "imp_recyclingcenter": {builds[rs]['recyclingcenter']},
    "imp_subway": {builds[rs]['subway']},
    "imp_supermarket": {builds[rs]['supermarket']},
    "imp_bank": {builds[rs]['bank']},
    "imp_mall": {builds[rs]['mall']},
    "imp_stadium": {builds[rs]['stadium']},
    "imp_barracks": {builds[rs]['barracks']},
    "imp_factory": {builds[rs]['factory']},
    "imp_hangars": {builds[rs]['airforcebase']},
    "imp_drydock": {builds[rs]['drydock']}
}}"""

        class webbuild(MethodView):
            def get(arg):
                with open('./data/templates/buildspage.txt', 'r', encoding='UTF-8') as file:
                    template = file.read()
                result = Template(template).render(builds=builds, rss=rss, land=land, unique_builds=unique_builds, datetime=datetime)
                return str(result)
        #@app.route(f"/raids/{atck_ntn['id']}")
        endpoint = datetime.utcnow().strftime('%d%H%M%S')
        app.add_url_rule(f"/builds/{datetime.utcnow().strftime('%d%H%M%S')}", view_func=webbuild.as_view(str(datetime.utcnow())), methods=["GET", "POST"]) # this solution of adding a new page instead of updating an existing for the same nation is kinda dependent on the bot resetting every once in a while, bringing down all the endpoints
        if str(arg_infra).lower() in "any":
            infra = "any amount of"
        if str(mmr).lower() in "any":
            mmr = "no military requirement"
        else:
            mmr = "a military requirement of " + '/'.join(mmr[i:i+1] for i in range(0, len(mmr), 1))
        await message.edit(content=f"{len(cities):,} valid cities and {len(unique_builds):,} unique builds fulfilled your criteria of {infra} infra and {mmr}.\n\nSee the best builds here (assuming you have {land} land): https://fuquiem.karemcbob.repl.co/builds/{endpoint}")
        return

    
def setup(bot):
    bot.add_cog(General(bot))