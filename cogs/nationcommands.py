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
        text = ""
        embed = discord.Embed(title='Links:', description="", color=0x00ff00)
        embed.add_field(name="Internal Affairs", value=ia)
        embed.add_field(name="Military Affairs", value=milcom)
        embed.add_field(name="Foreign Affairs", value=fa)
        embed.add_field(name="Other", value=other)
        await ctx.send(embed=embed)

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
        print(person)
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
            reminders += (f"\n{datetime.strftime(x['time'], '%d %B, %H:%M')} UTC ({round((x['time'] - datetime.utcnow()).total_seconds() // 3600)}h {round(((x['time'] - datetime.utcnow()).total_seconds() % 3600 // 60))}m) - <https://politicsandwar.com/nation/id={x['id']}>")
        await message.edit(content=f"Here are your reminders:\n{reminders}")
    
    @commands.command(brief='Delete a beige reminder', help='', aliases=['delalert', 'delrem'])
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

    @commands.command(brief='Add a beige reminder', help='', aliases=['ar', 'remindme', 'addreminder'])
    async def remind(self, ctx, arg):
        message = await ctx.send('Fuck requiem...')
        Database = self.bot.get_cog('Database')
        nation = await Database.find_nation(arg)
        if nation == None:
            await message.edit(content='I could not find that nation!')
            return
        print(nation)
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
    async def admit(self, ctx, applicant):
        Database = self.bot.get_cog('Database')
        person = await Database.find_user(applicant)
        response = requests.get(
            f"http://politicsandwar.com/api/nation/id={person['nationid']}&key=e5171d527795e8").json()
        if response['allianceposition'] > '1':
            await ctx.send('They are already a member!')
            return
        elif response['allianceposition'] < '1':
            await ctx.send('They are not an applicant!')
            return

        if response['allianceid'] == '4729':
            admin_id = 465463547200012298
        elif response['allianceid'] == '7531':
            admin_id = 154886766275461120
        else:
            await ctx.send('They are not applying to the correct alliance!')
            return

        admin = await Database.find_user(admin_id)
        print(admin)
        if admin['email'] == '' or admin['pwd'] == '':
            await ctx.send('Someone has not registered their PnW credentials with Fuquiem.')
            return

        cipher_suite = Fernet(key)

        with requests.Session() as s:
            login_url = "https://politicsandwar.com/login/"
            login_data = {
                "email": str(cipher_suite.decrypt(admin['email'].encode()))[2:-1],
                "password": str(cipher_suite.decrypt(admin['pwd'].encode()))[2:-1],
                "loginform": "Login"
            }
            s.post(login_url, data=login_data)

            withdraw_url = f"https://politicsandwar.com/alliance/id={response['allianceid']}"
            withdraw_data = {
                "nationperm": person['leader'],
                "level": '2',
                "permsubmit": 'Go',
            }

            try:
                await ctx.send(f"Are you sure you want to admit https://politicsandwar.com/nation/id={person['nationid']} ?")
                msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=40)

                if msg.content.lower() in ['yes', 'y']:
                    p = s.post(withdraw_url, data=withdraw_data)
                    await ctx.send(f'Response: {p}')
                elif msg.content.lower() in ['no', 'n']:
                    await ctx.send('Admission was canceled')
                    return
            except asyncio.TimeoutError:
                await ctx.send('Command timed out, you were too slow to respond.')

            if requests.get(f"http://politicsandwar.com/api/nation/id={person['nationid']}&key=e5171d527795e8").json()['allianceposition'] == '2':
                await ctx.send('They were successfully admitted')
            else:
                await ctx.send(f"The admission might have failed, check their nation page to be sure: https://politicsandwar.com/nation/id={person['nationid']}")
    
    def buildspage(self, builds, rss, land, unique_builds):
        template = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="https://i.ibb.co/2dX2WYW/atomism-ICONSSS.png">
    <title>City builds</title>
    <style>
        .template {
            display: inline-block;
            width: 320px;
            height: auto;
            margin: 20px;
            background-color: gainsboro;
        }

        .stat {
            display: inline-block;
            width: 100%;
        }

        .inline_block {
            display: inline-block;
            width: 30%;
            text-align:center;
        }

        .alert {
        padding: 20px;
        border-radius: 20px;
        background-color: orangered;
        color: white;
        font-size: small;
        }

        .closebtn {
        margin-left: 15px;
        color: white;
        font-weight: bold;
        float: right;
        font-size: 22px;
        line-height: 20px;
        cursor: pointer;
        transition: 0.3s;
        }

        .closebtn:hover {
        color: black;
        }
        
    </style>
    <script>
        function copyFunc(rs) {
            var str = document.getElementById(rs).innerHTML;
            const el = document.createElement('textarea');
            el.value = str;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
        }
    </script>
</head>
<body style="background-color: darkgray;font-family: Arial, Helvetica, sans-serif;font-size: 15px;">

<div>
    <div class="alert">
        <span class="closebtn" onclick="this.parentElement.style.display='none';">&times;</span> 
        <strong>IMPORTANT!</strong> - This tool only shows builds that are currently being used somewhere in Orbis. This means that you may very well be able to improve upon these builds. It's worth mentioning that even though this shows the best builds for producing every type of resource (except for the ones you can't produce due to continent restrictions), the "best build for net income" is in reality best for every resource. This is because the higher monetary income lets you buy more of a resource than you could get by producing it. Another important thing to mention, is that the monetary net income is dependent on market prices. This means that in times of war, manufactured resources will increase in price, increasing the profitability of builds producing these resources. The "best" build for net income may therefore not always be the same.
      </div>
    % for rs in rss:
    <div class="template" id="template ${rs}" style="border:4px solid whitesmoke; padding: 0px 5px 5px 5px;">
    <h3 style="text-align:center;">The best build for ${rs}</h3>
    <pre id="${rs}" style="font-size: small;">${builds[rs]['template']}</pre>
        <div style="display: flex;justify-content: space-between;">
            <button onclick="copyFunc('${rs}')">
                Copy build
            </button>
            <form action="https://politicsandwar.com/cities/" target="_blank" style="display: inline-block;">
                <input type="submit" value="Your city page" />
            </form>
            <form action="https://politicsandwar.com/city/improvements/bulk-import/" target="_blank" style="display: inline-block;">
                <input type="submit" value="Bulk import page" />
            </form>
        </div>
        <div class="stat">
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: left; width: 45%;">
                🤢 = ${round(builds[rs]['disease_rate'], 1)}% (${round(builds[rs]['real_disease_rate'], 1)}%)
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: right; width:45%">
                🏭 = ${round(builds[rs]['pollution'])}pts (${round(builds[rs]['real_pollution'])}pts)
            </div>
            <br>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: left; width: 45%">
                👮 = ${round(builds[rs]['crime_rate'], 1)}% (${round(builds[rs]['real_crime_rate'], 1)}%)
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: right; width: 45%">
                🛒 = ${round(builds[rs]['commerce'])}% (${round(builds[rs]['real_commerce'])}%)
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: left; width: 45%">
                MMR = ${f"{builds[rs]['barracks']}/{builds[rs]['factories']}/{builds[rs]['hangars']}/{builds[rs]['drydocks']}"}
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: right; width: 45%">
                Land = ${land}
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; display: inline-block; width: 306px">
                Net income = $${f"{round(builds[rs]['net income']):,}"}
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px;padding:5px;max-width:fit-content">
                <div class="inline_block"><img src="https://i.ibb.co/Jvc721Q/aluminum.png" alt="aluminum"></a> = ${round(builds[rs]['aluminum'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/MCX24BV/bauxite.png" alt="bauxite"></a> = ${round(builds[rs]['bauxite'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/0Q49PQW/coal.png" alt="coal"></a> = ${round(builds[rs]['coal'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/WyGLcnL/gasoline.png" alt="gasoline"></a> = ${round(builds[rs]['gasoline'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/27cjVPf/iron.png" alt="iron"></a> = ${round(builds[rs]['iron'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/r5KB1rS/lead.png" alt="lead"></a> = ${round(builds[rs]['lead'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/cgd2D7s/money.png" alt="money"></a> = ${round(builds[rs]['money']/1000, 1)}k</div>
                <div class="inline_block"><img src="https://i.ibb.co/LJLjL7g/munitions.png" alt="munitions"></a> = ${round(builds[rs]['munitions'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/861z21m/oil.png" alt="oil"></a> = ${round(builds[rs]['oil'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/PcbqzMS/steak-meat.png" alt="steak-meat"></a> = ${round(builds[rs]['food'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/JHVBnW7/steel.png" alt="steel"></a> = ${round(builds[rs]['steel'], 1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/JB3dhNQ/uranium.png" alt="uranium"></a> = ${round(builds[rs]['uranium'], 1)}</div>
            </div>
        </div>
        <div class="left_btn" style="float: left;">
            <button onclick="leftFunc('${rs}')" style="width: 100px;">
                <span class="tooltiptext" id="myTooltip">Previous</span>
            </button>
        </div>
        <div class="count" id="count ${rs}" style="text-align: center;width: 120px;display: inline-block;">
            #1
        </div>
        <div class="right_btn" style="float: right;">
            <button onclick="rightFunc('${rs}')" style="width: 100px;">
                <span class="tooltiptext" id="myTooltip">Next</span>
            </button>
        </div>
    </div>
    % endfor
</div>
</body>
<script>
        
    var builds = ${unique_builds}
    var land = ${land}

    function formatNumber(num) {
        return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
    }

    function rightFunc(rs) {
        console.log(rs)
        builds.sort((firstItem, secondItem) => secondItem[rs] - firstItem[rs]);
        var index = parseInt(document.getElementById("count " + rs).textContent.replace(/\D/g,'')) + 1
        var build = builds[index-1]
        templateMaker(build, rs, index)
    }

    function leftFunc(rs) {
        console.log(rs)
        builds.sort((firstItem, secondItem) => secondItem[rs] - firstItem[rs]);
        var index = parseInt(document.getElementById("count " + rs).textContent.replace(/\D/g,'')) - 1
        var build = builds[index-1]
        templateMaker(build, rs, index)
    }

    function templateMaker(build, rs, index) {
        var str = `
        <div class="template" id="template <%text>$</%text>{rs}" style="border:4px solid whitesmoke; padding: 0px 5px 5px 5px;">
        <h3 style="text-align:center;">The best build for <%text>$</%text>{rs}</h3>
    <pre id="<%text>$</%text>{rs}" style="font-size: small;">
{
    "infra_needed": <%text>$</%text>{build['infrastructure']},
    "imp_total": <%text>$</%text>{Math.floor(parseFloat(build['infrastructure'])/50)},
    "imp_coalpower": <%text>$</%text>{build['coal_power_plants']},
    "imp_oilpower": <%text>$</%text>{build['oil_power_plants']},
    "imp_windpower": <%text>$</%text>{build['wind_power_plants']},
    "imp_nuclearpower": <%text>$</%text>{build['nuclear_power_plants']},
    "imp_coalmine": <%text>$</%text>{build['coal_mines']},
    "imp_oilwell": <%text>$</%text>{build['oil_wells']},
    "imp_uramine": <%text>$</%text>{build['uranium_mines']},
    "imp_leadmine": <%text>$</%text>{build['lead_mines']},
    "imp_ironmine": <%text>$</%text>{build['iron_mines']},
    "imp_bauxitemine": <%text>$</%text>{build['bauxite_mines']},
    "imp_farm": <%text>$</%text>{build['farms']},
    "imp_gasrefinery": <%text>$</%text>{build['oil_refineries']},
    "imp_aluminumrefinery": <%text>$</%text>{build['aluminum_refineries']},
    "imp_munitionsfactory": <%text>$</%text>{build['munitions_factories']},
    "imp_steelmill": <%text>$</%text>{build['steel_mills']},
    "imp_policestation": <%text>$</%text>{build['police_stations']},
    "imp_hospital": <%text>$</%text>{build['hospitals']},
    "imp_recyclingcenter": <%text>$</%text>{build['recycling_centers']},
    "imp_subway": <%text>$</%text>{build['subway']},
    "imp_supermarket": <%text>$</%text>{build['supermarkets']},
    "imp_bank": <%text>$</%text>{build['banks']},
    "imp_mall": <%text>$</%text>{build['shopping_malls']},
    "imp_stadium": <%text>$</%text>{build['stadiums']},
    "imp_barracks": <%text>$</%text>{build['barracks']},
    "imp_factory": <%text>$</%text>{build['factories']},
    "imp_hangars": <%text>$</%text>{build['hangars']},
    "imp_drydock": <%text>$</%text>{build['drydocks']}
}</pre>
        <div style="display: flex;justify-content: space-between;">
            <button onclick="copyFunc('${rs}')">
                Copy build
            </button>
            <form action="https://politicsandwar.com/cities/" target="_blank" style="display: inline-block;">
                <input type="submit" value="Your city page" />
            </form>
            <form action="https://politicsandwar.com/city/improvements/bulk-import/" target="_blank" style="display: inline-block;">
                <input type="submit" value="Bulk import page" />
            </form>
        </div>
        <div class="stat">
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: left; width: 45%;">
                🤢 = <%text>$</%text>{Math.round(build['disease_rate'] * 10) / 10}% (<%text>$</%text>{Math.round(build['real_disease_rate'] * 10) / 10}%)
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: right; width:45%">
                🏭 = <%text>$</%text>{build['pollution']}pts (<%text>$</%text>{build['real_pollution']}pts)
            </div>
            <br>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: left; width: 45%">
                👮 = <%text>$</%text>{Math.round(build['crime_rate'] * 10) / 10}% (<%text>$</%text>{Math.round(build['real_crime_rate'] * 10) / 10}%)
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: right; width: 45%">
                🛒 = <%text>$</%text>{build['commerce']}% (<%text>$</%text>{build['real_commerce']}%)
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: left; width: 45%">
                MMR = <%text>$</%text>{build['barracks']}/<%text>$</%text>{build['factories']}/<%text>$</%text>{build['hangars']}/<%text>$</%text>{build['drydocks']}
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; float: right; width: 45%">
                Land = <%text>$</%text>{land}
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px; padding: 3px 5px 3px 5px; display: inline-block; width: 306px">
                Net income = <%text>$</%text><%text>$</%text>{formatNumber(build['net income'])}
            </div>
            <div style="border:2px groove whitesmoke; border-radius: 5px;padding:5px;max-width:fit-content">
                <div class="inline_block"><img src="https://i.ibb.co/Jvc721Q/aluminum.png" alt="aluminum"></a> = <%text>$</%text>{parseFloat(build['aluminum']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/MCX24BV/bauxite.png" alt="bauxite"></a> = <%text>$</%text>{parseFloat(build['bauxite']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/0Q49PQW/coal.png" alt="coal"></a> = <%text>$</%text>{parseFloat(build['coal']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/WyGLcnL/gasoline.png" alt="gasoline"></a> = <%text>$</%text>{parseFloat(build['gasoline']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/27cjVPf/iron.png" alt="iron"></a> = <%text>$</%text>{parseFloat(build['iron']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/r5KB1rS/lead.png" alt="lead"></a> = <%text>$</%text>{parseFloat(build['lead']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/cgd2D7s/money.png" alt="money"></a> = <%text>$</%text>{parseFloat(build['money']/1000).toFixed(1)}k</div>
                <div class="inline_block"><img src="https://i.ibb.co/LJLjL7g/munitions.png" alt="munitions"></a> = <%text>$</%text>{parseFloat(build['munitions']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/861z21m/oil.png" alt="oil"></a> = <%text>$</%text>{parseFloat(build['oil']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/PcbqzMS/steak-meat.png" alt="steak-meat"></a> = <%text>$</%text>{parseFloat(build['food']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/JHVBnW7/steel.png" alt="steel"></a> = <%text>$</%text>{parseFloat(build['steel']).toFixed(1)}</div>
                <div class="inline_block"><img src="https://i.ibb.co/JB3dhNQ/uranium.png" alt="uranium"></a> = <%text>$</%text>{parseFloat(build['uranium']).toFixed(1)}</div>
            </div>
        </div>
        <div class="left_btn" style="float: left;">
            <button onclick="leftFunc('<%text>$</%text>{rs}')" style="width: 100px;">
                <span class="tooltiptext" id="myTooltip">Previous</span>
            </button>
        </div>
        <div class="count" id="count <%text>$</%text>{rs}" style="text-align: center;width: 120px;display: inline-block;">
            #<%text>$</%text>{index}
        </div>
        <div class="right_btn" style="float: right;">
            <button onclick="rightFunc('<%text>$</%text>{rs}')" style="width: 100px;">
                <span class="tooltiptext" id="myTooltip">Next</span>
            </button>
        </div>
</div>`
        console.log()
        var Obj = document.getElementById(`template <%text>$</%text>{rs}`); //any element to be fully replaced
        if(Obj.outerHTML) { //if outerHTML is supported
            Obj.outerHTML=str; ///it's simple replacement of whole element with contents of str var
        }
        else { //if outerHTML is not supported, there is a weird but crossbrowsered trick
            var tmpObj=document.createElement("div");
            tmpObj.innerHTML='<!--THIS DATA SHOULD BE REPLACED-->';
            ObjParent=Obj.parentNode; //Okey, element should be parented
            ObjParent.replaceChild(tmpObj,Obj); //here we placing our temporary data instead of our target, so we can find it then and replace it into whatever we want to replace to
            ObjParent.innerHTML=ObjParent.innerHTML.replace('<div><!--THIS DATA SHOULD BE REPLACED--></div>',str);
        }

    }
</script>
</html>"""

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
            mmr = '/'.join(mmr[i:i+1] for i in range(0, len(mmr), 1))
            await message.edit(content=f"{len(cities):,} valid cities and {len(unique_builds):,} unique builds fulfilled your criteria of {infra} infra and a minimum military requirement of {mmr}.\n\nSee the best builds here (assuming you have {land} land): https://fuquiem.karemcbob.repl.co/builds/{endpoint}")
            return

    
def setup(bot):
    bot.add_cog(General(bot))