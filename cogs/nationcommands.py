import os
from discord.ext import commands
import discord
import requests
import asyncio
from datetime import datetime, timedelta
from main import mongo
from cryptography.fernet import Fernet
import pathlib
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
        Database = self.bot.get_cog('Database')
        if api_nation['allianceposition'] > '2':
            await message.edit(content="I cannot let you change the perms of a person of such high ranking!")
            return {}
        if api_nation['allianceid'] == '4729':
            admin_id = 465463547200012298
        elif api_nation['allianceid'] == '7531':
            admin_id = 154886766275461120
        else:
            await message.edit(content='They are not affiliated with the Church nor the Convent!')
            return {}
        admin = await Database.find_user(admin_id)
        if admin['email'] == '' or admin['pwd'] == '':
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
                await message.edit(content='Their status was successfully changed.')
                await asyncio.sleep(2)
            else:
                await message.edit(content=f"I might have failed at changing their status, check their nation page to be sure: https://politicsandwar.com/nation/id={api_nation['nationid']}")
                return {}

    @commands.command(aliases=['message'], brief="Send a premade message to someone")
    @commands.has_any_role('Internal Affairs')
    async def msg(self, ctx, arg):
        message = await ctx.send("Working on it..")
        Database = self.bot.get_cog('Database')

        nation = await Database.find_nation(arg)
        if nation == None:
            nation = await Database.find_user(arg)
            if nation == {}:
                await message.edit(content='I could not find that nation!')
                return
            else:
                nation = await Database.find_nation(nation['nationid'])
                if nation == None:
                    await message.edit(content='I could not find that nation!')
                    return

        msg_hist = mongo.message_history.find_one({"nationid": nation['nationid']})

        api_nation = requests.get(f"http://politicsandwar.com/api/nation/id={nation['nationid']}&key=e5171d527795e8").json()

        invoker = await Database.find_user(ctx.author.id)
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
        Database = self.bot.get_cog('Database')
        nation = await Database.find_nation(arg)
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
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(person)
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

    @commands.command(brief='Admits an applicant, accepts 1 argument')
    @commands.has_any_role('Deacon', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def admit(self, ctx, arg):
        message = await ctx.send("<:thonk:787399051582504980>")
        Database = self.bot.get_cog('Database')
        nation = await Database.find_nation_plus(arg)
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
        
    def buildspage(self, builds, rss, land, unique_builds):
        with open('./data/templates/buildspage.txt', 'r', encoding='UTF-8') as file:
            template = file.read()
        result = Template(template).render(builds=builds, rss=rss, land=land, unique_builds=unique_builds, datetime=datetime)
        return str(result)

    @commands.command(aliases=['builds'], brief="Shows you the best city builds", help="After calling the command, you have to tell Fuquiem 3 things. 1) How much infra you want. 2) How much land you want. 3) What MMR you want. When you're done with this, Fuquiem will link to a webpage showing the best builds for producing every resource. Note that these are the best builds for YOU and YOU only! I takes your projects and continent into consideration when calculating the revenue of each build. When calling the command, you can therefore supply a person for whom you want the builds to be calculated for. IMPORTANT! - This tool only shows builds that are currently being used somewhere in Orbis. This means that you may very well be able to improve upon these builds. It's worth mentioning that even though this shows the best builds for producing every type of resource (except for the ones you can't produce due to continent restrictions), the \"best build for net income\" is in reality best for every resource. This is because the higher monetary income lets you buy more of a resource than you could get by producing it. Another important thing to mention, is that the monetary net income is dependent on market prices. This means that in times of war, manufactured resources will increase in price, increasing the profitability of builds producing these resources. The \"best\" build for net income may therefore not always be the same.")
    @commands.has_any_role('Pupil', 'Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def build(self, ctx, person=None):
        now = datetime.now()
        yesterday = now + timedelta(days=-1)
        date = yesterday.strftime("%Y-%m-%d")
        if os.path.isfile(pathlib.Path.cwd() / 'data' / 'dumps' / 'cities' / f'cities-{date}.csv'):
            print('That file already exists')
        else:
            dload.save_unzip(f"https://politicsandwar.com/data/cities/cities-{date}.csv.zip", str(
                pathlib.Path.cwd() / 'data' / 'dumps' / 'cities'), True)

        with open(pathlib.Path.cwd() / 'data' / 'dumps' / 'cities' / f'cities-{date}.csv', encoding='cp437') as f1:
            csv_dict_reader = DictReader(f1)

            message = await ctx.send('Stay with me...')
            if person == None:
                person = ctx.author.id
            Database = self.bot.get_cog('Database')
            db_nation = await Database.find_user(person)

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
            
            nation = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{nations(first:1 id:{db_nation['nationid']}){{data{{id continent date color dompolicy ironw bauxitew armss egr massirr itc recycling_initiative telecom_satellite green_tech clinical_research_center specialized_police_training uap}}}}}}"}).json()['data']['nations']['data']
            if len(nation) == 0:
                await message.edit(content="That person was not in the API!")
                return
            else:
                nation = nation[0]

            embed = discord.Embed(title=f"Infrastructure", description="How much infrastructure do you want the build to be for?\n\nex. \"1500\"\nex. \"2.5k\"\nex. \"any\"", color=0x00ff00)
            await message.edit(content="", embed=embed)

            while True:
                try:
                    command = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=600)
                    infra = command.content
                    try:
                        if "." in infra:
                            num_inf = re.sub("[A-z]", "", infra)
                            infra = int(num_inf.replace(".", "")) / 10**(len(num_inf) - num_inf.rfind(".") - 1)
                    except:
                        await message.edit(content="**I did not understand that, please try again!**")
                        continue

                    if "k" in command.content:
                        infra = int(float(re.sub("[A-z]", "", str(infra))) * 1000)
                    else:
                        try:
                            infra = int(infra)
                        except:
                            await message.edit(content="**I did not understand that, please try again!**")
                            continue

                    if not isinstance(infra, int) and str(infra).lower() not in "any":
                        await message.edit(content="**I did not understand that, please try again!**")
                        continue

                    print(infra)
                    await command.delete()
                    break

                except asyncio.TimeoutError:
                    await message.edit(content="**Command timed out!**")
                    print('message break')
                    break

            embed = discord.Embed(title=f"Land", description="How much land should I assume the cities to have when calculating their revenue?\n\nex. \"1500\"\nex. \"2.5k\"", color=0x00ff00)
            await message.edit(content="", embed=embed)

            while True:
                try:
                    command = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=600)
                    land = command.content
                    try:
                        if "." in land:
                            num_land = re.sub("[A-z]", "", land)
                            land = int(num_land.replace(".", "")) / 10**(len(num_land) - num_land.find(".") + num_land.rfind(".") - 2)
                    except:
                        await message.edit(content="**I did not understand that, please try again!**")
                        continue

                    if "k" in command.content:
                        land = int(float(re.sub("[A-z]", "", str(land))) * 1000)
                    else:
                        try:
                            land = int(land)
                        except:
                            await message.edit(content="**I did not understand that, please try again!**")
                            continue

                    print(land)
                    await command.delete()
                    break

                except asyncio.TimeoutError:
                    await message.edit(content="**Command timed out!**")
                    print('message break')
                    break

            embed = discord.Embed(title=f"MMR", description="What should the minimum military requirement be?\n\nex. \"1/2/5/1\"\nex. \"0351\"\nex. \"any\"", color=0x00ff00)
            await message.edit(content="", embed=embed)

            while True:
                try:
                    command = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=600)
                    mmr = command.content
                    await command.delete()
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
                city.pop('land')

                to_scan.append(city)
            
            await message.edit(content="Doing API calls...")
            res_colors = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{colors{{color turn_bonus}}}}"}).json()['data']['colors']
            colors = {}
            for color in res_colors:
                colors[color['color']] = color['turn_bonus'] * 12

            prices = requests.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{tradeprices(limit:1){{coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}}}"}).json()['data']['tradeprices'][0]
            prices['money'] = 1

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

            await message.edit(content="Calculating revenue...")
            max_commerce = 100
            max_hosp = 5
            max_recy = 3
            max_poli = 5
            base_com = 0
            hos_dis_red = 2.5
            alu_mod = 1
            mun_mod = 1
            gas_mod = 1
            manu_poll_mod = 1
            farm_poll_mod = 0.5
            subw_poll_red = 45
            rss_upkeep_mod = 1
            ste_mod = 1
            rec_poll = 70
            pol_cri_red = 2.5
            food_land_mod = 500
            uranium_mod = 1
            policy_bonus = 1
            mil_cost = 1
            new_player_bonus = 1
            city_age = (datetime.utcnow() - datetime.strptime(nation['date'], "%Y-%m-%d %H:%M:%S")).days / 2
            if city_age <= 0:
                city_age = 1

            if nation['ironw'] == True:
                ste_mod = 1.36
            if nation['bauxitew'] == True:
                alu_mod = 1.36
            if nation['armss'] == True:
                mun_mod = 1.34
            if nation['egr'] == True:
                gas_mod = 2
            if nation['massirr'] == True:
                food_land_mod = 400
            if nation['itc'] == True:
                max_commerce = 115
            if nation['telecom_satellite'] == True:
                max_commerce = 125
                base_com = 2
            if nation['recycling_initiative'] == True:
                rec_poll = 75
                max_recy = 4
            if nation['green_tech'] == True:
                manu_poll_mod = 0.75
                farm_poll_mod = 0.5
                subw_poll_red = 70
                rss_upkeep_mod = 0.9
            if nation['clinical_research_center'] == True:
                hos_dis_red = 3.5
                max_hosp = 6
            if nation['specialized_police_training'] == True:
                hos_dis_red = 3.5
                max_poli = 6
            if nation['uap'] == True:
                uranium_mod = 2
            if nation['dompolicy'] == "Imperialism":
                mil_cost = 0.95
            if nation['dompolicy'] == "Open Markets":
                policy_bonus = 1.01

            cities = []
            for city in to_scan:
                if int(city['hospitals']) > max_hosp or int(city['recycling_centers']) > max_recy or int(city['police_stations']) > max_poli:
                    continue
                city['coal'] = 0
                city['oil'] = 0
                city['uranium'] = 0
                city['lead'] = 0
                city['iron'] = 0
                city['bauxite'] = 0
                city['gasoline'] = 0
                city['munitions'] = 0
                city['steel'] = 0
                city['aluminum'] = 0
                city['food'] = 0
                city['money'] = 0
                rss_upkeep = 0
                civil_upkeep = 0
                power_upkeep = 0
                mil_upkeep = 0

                base_pop = float(city['infrastructure']) * 100
                pollution = 0
                unpowered_infra = float(city['infrastructure'])
                for wind_plant in range(int(city['wind_power_plants'])): #can add something about wasted slots
                    if unpowered_infra > 0:
                        unpowered_infra -= 250
                        power_upkeep += 42
                for nucl_plant in range(int(city['nuclear_power_plants'])): 
                    power_upkeep += 10500
                    for level in range(2):
                        if unpowered_infra > 0:
                            unpowered_infra -= 1000
                            city['uranium'] -= 1.2
                for oil_plant in range(int(city['oil_power_plants'])): 
                    power_upkeep += 1800 
                    pollution += 6
                    for level in range(5):
                        if unpowered_infra > 0:
                            unpowered_infra -= 100
                            city['oil'] -= 1.2
                for coal_plant in range(int(city['coal_power_plants'])): 
                    power_upkeep += 1200  
                    pollution += 8
                    for level in range(5):
                        if unpowered_infra > 0:
                            unpowered_infra -= 100
                            city['coal'] -= 1.2

                rss_upkeep += 400 * int(city['coal_mines']) * rss_upkeep_mod
                pollution += 12 * int(city['coal_mines'])
                city['coal'] += 3 * int(city['coal_mines']) * (1 + ((0.5 * (int(city['coal_mines']) - 1)) / (10 - 1)))

                rss_upkeep += 600 * int(city['oil_wells']) * rss_upkeep_mod
                pollution += 12 * int(city['oil_wells'])
                city['oil'] += 3 * int(city['oil_wells']) * (1 + ((0.5 * (int(city['oil_wells']) - 1)) / (10 - 1)))

                rss_upkeep += 5000 * int(city['uranium_mines']) * rss_upkeep_mod
                pollution += 20 * int(city['uranium_mines'])
                city['uranium'] += 3 * int(city['uranium_mines']) * (1 + ((0.5 * (int(city['uranium_mines']) - 1)) / (5 - 1))) * uranium_mod

                rss_upkeep += 1500 * int(city['lead_mines']) * rss_upkeep_mod
                pollution += 12 * int(city['lead_mines'])
                city['lead'] += 3 * int(city['lead_mines']) * (1 + ((0.5 * (int(city['lead_mines']) - 1)) / (10 - 1)))

                rss_upkeep += 1600 * int(city['iron_mines']) * rss_upkeep_mod
                pollution += 12 * int(city['iron_mines'])
                city['iron'] += 3 * int(city['iron_mines']) * (1 + ((0.5 * (int(city['iron_mines']) - 1)) / (10 - 1)))

                rss_upkeep += 1600 * int(city['bauxite_mines']) * rss_upkeep_mod
                pollution += 12 * int(city['bauxite_mines'])
                city['bauxite'] += 3 * int(city['bauxite_mines']) * (1 + ((0.5 * (int(city['bauxite_mines']) - 1)) / (10 - 1)))

                rss_upkeep += 300 * int(city['farms']) * rss_upkeep_mod ## seasonal modifiers and radiation
                pollution += 2 * int(city['farms']) * farm_poll_mod
                food_prod = float(land)/food_land_mod * int(city['farms']) * (1 + ((0.5 * (int(city['farms']) - 1)) / (20 - 1))) * seasonal_mod[nation['continent']] * radiation[nation['continent']]
                if food_prod < 0:
                    city['food'] += 0
                else:
                    city['food'] += food_prod
                
                commerce = base_com
                if unpowered_infra <= 0:
                    rss_upkeep += 4000 * int(city['oil_refineries']) * rss_upkeep_mod
                    pollution += 32 * int(city['oil_refineries']) * manu_poll_mod
                    city['oil'] -= 3 * int(city['oil_refineries']) * (1 + ((0.5 * (int(city['oil_refineries']) - 1)) / (5 - 1))) * gas_mod
                    city['gasoline'] += 6 * int(city['oil_refineries']) * (1 + ((0.5 * (int(city['oil_refineries']) - 1)) / (5 - 1))) * gas_mod

                    rss_upkeep += 4000 * int(city['steel_mills']) * rss_upkeep_mod
                    pollution += 40 * int(city['steel_mills']) * manu_poll_mod
                    city['iron'] -= 3 * int(city['steel_mills']) * (1 + ((0.5 * (int(city['steel_mills']) - 1)) / (5 - 1))) * ste_mod
                    city['coal'] -= 3 * int(city['steel_mills']) * (1 + ((0.5 * (int(city['steel_mills']) - 1)) / (5 - 1))) * ste_mod
                    city['steel'] += 9 * int(city['steel_mills']) * (1 + ((0.5 * (int(city['steel_mills']) - 1)) / (5 - 1))) * ste_mod

                    rss_upkeep += 2500 * int(city['aluminum_refineries']) * rss_upkeep_mod
                    pollution += 40 * int(city['aluminum_refineries']) * manu_poll_mod
                    city['bauxite'] -= 3 * int(city['aluminum_refineries']) * (1 + ((0.5 * (int(city['aluminum_refineries']) - 1)) / (5 - 1))) * alu_mod
                    city['aluminum'] += 9 * int(city['aluminum_refineries']) * (1 + ((0.5 * (int(city['aluminum_refineries']) - 1)) / (5 - 1))) * alu_mod

                    rss_upkeep += 3500 * int(city['munitions_factories']) * rss_upkeep_mod
                    pollution += 32 * int(city['munitions_factories']) * manu_poll_mod
                    city['lead'] -= 6 * int(city['munitions_factories']) * (1 + ((0.5 * (int(city['munitions_factories']) - 1)) / (5 - 1))) * mun_mod
                    city['munitions'] += 18 * int(city['munitions_factories']) * (1 + ((0.5 * (int(city['munitions_factories']) - 1)) / (5 - 1))) * mun_mod
                    
                    civil_upkeep += int(city['police_stations']) * 750 
                    civil_upkeep += int(city['hospitals']) * 1000 
                    civil_upkeep += int(city['recycling_centers']) * 2500 
                    civil_upkeep += int(city['subway']) * 3250 
                    civil_upkeep += int(city['supermarkets']) * 600 
                    civil_upkeep += int(city['banks']) * 1800 
                    civil_upkeep += int(city['shopping_malls']) * 5400
                    civil_upkeep += int(city['stadiums']) * 12150 

                    pollution += int(city['police_stations'])
                    pollution += int(city['hospitals']) * 4
                    pollution -= int(city['recycling_centers']) * rec_poll
                    pollution -= int(city['subway']) * subw_poll_red
                    pollution += int(city['shopping_malls']) * 2
                    pollution += int(city['stadiums']) * 5
                    
                    commerce += int(city['subway']) * 8
                    commerce += int(city['supermarkets']) * 3 
                    commerce += int(city['banks']) * 5 
                    commerce += int(city['shopping_malls']) * 9
                    commerce += int(city['stadiums']) * 12 

                    mil_upkeep += int(city['barracks']) * 3000 * 1.25
                    mil_upkeep += int(city['factories']) * 250 * 50
                    mil_upkeep += int(city['hangars']) * 15 * 500
                    mil_upkeep += int(city['drydocks']) * 5 * 3750

                city['real_commerce'] = commerce
                if commerce > max_commerce:
                    commerce = max_commerce
                city['commerce'] = commerce
                
                city['real_pollution'] = pollution
                if pollution < 0:
                    pollution = 0
                city['pollution'] = pollution

                city['real_crime_rate'] = ((103 - commerce)**2 + (float(city['infrastructure']) * 100))/(111111) - int(city['police_stations']) * pol_cri_red
                if city['real_crime_rate'] < 0:
                    city['crime_rate'] = 0
                else:
                    city['crime_rate'] = city['real_crime_rate']
                crime_deaths = ((city['crime_rate']) / 10) * (100 * float(city['infrastructure'])) - 25
                city['real_disease_rate'] = (((((base_pop / float(land))**2) * 0.01) - 25)/100) + (base_pop/100000) + pollution * 0.05 - int(city['hospitals']) * hos_dis_red
                if city['real_disease_rate'] < 0:
                    city['disease_rate'] = 0
                else:
                    city['disease_rate'] = city['real_disease_rate']
                disease_deaths = base_pop * (city['disease_rate']/100)
                population = ((base_pop - disease_deaths - crime_deaths) * (1 + math.log(city_age)/15))
                #print(city['id'], disease_rate, disease_deaths, crime_rate, crime_deaths, population, base_pop, city_age)
                city['money'] = (((commerce / 50) * 0.725) + 0.725) * population
                city['net income'] = round(city['money'] * policy_bonus * new_player_bonus - power_upkeep - rss_upkeep - civil_upkeep - mil_upkeep * mil_cost + city['coal'] * prices['coal'] + city['oil'] * prices['oil'] + city['uranium'] * prices['uranium'] + city['lead'] * prices['lead'] + city['iron'] * prices['iron'] + city['bauxite'] * prices['bauxite'] + city['gasoline'] * prices['gasoline'] + city['munitions'] * prices['munitions'] + city['steel'] * prices['steel'] + city['aluminum'] * prices['aluminum'] + city['food'] * prices['food'])
                cities.append(city)

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
    "imp_coalpower": {builds[rs]['coal_power_plants']},
    "imp_oilpower": {builds[rs]['oil_power_plants']},
    "imp_windpower": {builds[rs]['wind_power_plants']},
    "imp_nuclearpower": {builds[rs]['nuclear_power_plants']},
    "imp_coalmine": {builds[rs]['coal_mines']},
    "imp_oilwell": {builds[rs]['oil_wells']},
    "imp_uramine": {builds[rs]['uranium_mines']},
    "imp_leadmine": {builds[rs]['lead_mines']},
    "imp_ironmine": {builds[rs]['iron_mines']},
    "imp_bauxitemine": {builds[rs]['bauxite_mines']},
    "imp_farm": {builds[rs]['farms']},
    "imp_gasrefinery": {builds[rs]['oil_refineries']},
    "imp_aluminumrefinery": {builds[rs]['aluminum_refineries']},
    "imp_munitionsfactory": {builds[rs]['munitions_factories']},
    "imp_steelmill": {builds[rs]['steel_mills']},
    "imp_policestation": {builds[rs]['police_stations']},
    "imp_hospital": {builds[rs]['hospitals']},
    "imp_recyclingcenter": {builds[rs]['recycling_centers']},
    "imp_subway": {builds[rs]['subway']},
    "imp_supermarket": {builds[rs]['supermarkets']},
    "imp_bank": {builds[rs]['banks']},
    "imp_mall": {builds[rs]['shopping_malls']},
    "imp_stadium": {builds[rs]['stadiums']},
    "imp_barracks": {builds[rs]['barracks']},
    "imp_factory": {builds[rs]['factories']},
    "imp_hangars": {builds[rs]['hangars']},
    "imp_drydock": {builds[rs]['drydocks']}
}}"""

            class webbuild(MethodView):
                def get(arg):
                    return self.buildspage(builds, rss, land, unique_builds)
            #@app.route(f"/raids/{atck_ntn['id']}")
            endpoint = datetime.utcnow().strftime('%d%H%M%S')
            app.add_url_rule(f"/builds/{datetime.utcnow().strftime('%d%H%M%S')}", view_func=webbuild.as_view(str(datetime.utcnow())), methods=["GET", "POST"]) # this solution of adding a new page instead of updating an existing for the same nation is kinda dependent on the bot resetting every once in a while, bringing down all the endpoints
            if str(infra).lower() in "any":
                infra = "any amount of"
            if str(mmr).lower() in "any":
                mmr = "no military requirement"
            else:
                mmr = "a military requirement of " + '/'.join(mmr[i:i+1] for i in range(0, len(mmr), 1))
            await message.edit(content=f"{len(cities):,} valid cities and {len(unique_builds):,} unique builds fulfilled your criteria of {infra} infra and {mmr}.\n\nSee the best builds here (assuming you have {land} land): https://fuquiem.karemcbob.repl.co/builds/{endpoint}")
            return

    
def setup(bot):
    bot.add_cog(General(bot))