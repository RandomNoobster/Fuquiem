from collections import defaultdict
import discord
from matplotlib.style import use
import requests
import dateutil.parser
import aiohttp
from lxml import html
import math
import pytz
import re
import utils
import copy
import asyncio
from datetime import datetime, timedelta
from main import mongo
from discord.ext import commands
import os
from cryptography.fernet import Fernet

api_key = os.getenv("api_key")
key = os.getenv("encryption_key")
convent_key = os.getenv("convent_api_key")
cipher_suite = Fernet(key)

class Economic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases=['prices', 'p'],
        brief='A chart showing price history',
        help='You can use the command without supplying any arguments, then it would default to all resources and the average price. If you only wish to see one resource, the first argument will be the name of that resource (although the bot only uses the first two letters, meaning that even though it works just fine to write "aluminum", it works just as well to write "al"). The second argument is the offer-type, if left blank it will default to average price, but you can specify "buy offer" ("bo") or "sell offer" ("so").'
        )
    async def price(self, ctx, input_resource='all', *, type='avg'):
        message = await ctx.send('Doing API calls...')
        f1 = list(mongo.price_history.find({}))
        new = await self.get_prices()
        f1.append(new)
        f_cop = f1.copy()
        while len(f1) >= 200:
            for n in range(math.floor(len(f1)/2)):
                if n % 2 == 0:
                    del f1[n]
        dates = []
        data = []
        input_resource.lower()
        type.lower()

        rss = ['Aluminum', 'Bauxite', 'Coal', 'Credits', 'Food', 'Gasoline', 'Iron', 'Lead', 'Munitions', 'Oil', 'Steel', 'Uranium']
        found = False

        if input_resource == 'all':
            index = ''
            label = ''
            found = True
        else:
            for rs in rss:
                if input_resource in rs.lower():
                    index = rs.lower()[:2]
                    label = rs
                    found = True
                    break

        if found == False:
            await message.edit('That was not a valid resource, please try again!')
            return

        if type in 'average' or type in 'avg':
            index += '_avg'
            label += ' - Average price'
        elif type in 'highest buy' or type in ['hb', 'buy_offer', 'buy offer', 'buyoffer', 'highest_buy', 'bo']:
            index += '_hb'
            label += ' - Highest buy-offer'
        elif type in 'lowest sell' or type in ['lowest_buy', 'highest_sell', 'lb', 'hs', 'sell_offer', 'sell offer', 'selloffer', 'so']:
            index += '_lb'
            label += ' - Lowest sell-offer'
        else:
            await message.edit('That was not a valid offer-type, please try again!')
            return
        
        if input_resource != 'all':
            field = f"{label}: **{int(new['prices'][f'{index}']):,}**ppu"
            for x in f1:
                t1 = dateutil.parser.parse(x['time'])
                t2 = t1.replace(tzinfo=pytz.UTC)
                t3 = t2.strftime("%Y/%m/%d")
                dates.append(t3)
                data.append(x['prices'][index])
            post_data = {'chart': {'type': 'line', 'data': {
                'labels': dates, 'datasets': [{'label': label, 'data': data}]}}}

        else:
            field = ""
            for rs in rss:
                field += f"{rs}{label}: **{int(new['prices'][f'{rs.lower()[:2]}{index}']):,}**ppu\n"

            datasets = [{'label': 'Aluminum', 'data': []}, {'label': 'Bauxite', 'data': []}, {'label': 'Coal', 'data': []}, {'label': 'Food', 'data': []}, {'label': 'Gasoline', 'data': []}, {
                'label': 'Iron', 'data': []}, {'label': 'Lead', 'data': []}, {'label': 'Munitions', 'data': []}, {'label': 'Steel', 'data': []}, {'label': 'Uranium', 'data': []}]
            for x in f1:
                t1 = dateutil.parser.parse(x['time'])
                t2 = t1.replace(tzinfo=pytz.UTC)
                t3 = t2.strftime("%Y/%m/%d")
                dates.append(t3)
                for y in datasets:
                    temp_index = y['label'][:2].lower() + index
                    y['data'].append(x['prices'][temp_index])
            post_data = {'chart': {'type': 'line', 'data': {
                'labels': dates, 'datasets': datasets}}}

        response = requests.post(
            'https://quickchart.io/chart/create', json=post_data)
        chart_response = response.json()

        embed = discord.Embed(
            title='Market prices:', description="Here is the price history of the resorces and offer-type you specified:", color=0x00ff00)
        embed.set_image(url=chart_response['url'])
        embed.add_field(inline=True, name="Current prices", value=field)
        embed.add_field(inline=False, name="Price history", value="\u200b")
        await message.edit(content='',embed=embed)

    @commands.command(
        brief='Archive current resource prices'
        )
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def getprices(self, ctx):
        file = await self.get_prices()
        mongo.price_history.insert_one(file)
        await ctx.send(f'Prices have been gathered!')
        # merely a debugging command
    
    @commands.command(
        brief='Print average prices for resources',
        help='Sends a message on discord and prints average prices to the console. This is the average of all recorded prices.'
        )
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def avgprices(self, ctx):
        rss = ['Aluminum', 'Bauxite', 'Coal', 'Credits', 'Food', 'Gasoline', 'Iron', 'Lead', 'Munitions', 'Oil', 'Steel', 'Uranium']
        resp = list(mongo.price_history.find({}))
        avg = {}
        for rs in rss:
            avg[rs] = 0
            for price in resp:
                avg[rs] += int(price['prices'][f"{rs[:2].lower()}_avg"])
            avg[rs] = round(avg[rs]/len(resp))
        print(avg)
        await ctx.send(avg)
        # merely a debugging command

    async def get_prices(self):
        async with aiohttp.ClientSession() as session:
            rss = ['aluminum', 'bauxite', 'coal', 'credits', 'food', 'gasoline', 'iron', 'lead', 'munitions', 'oil', 'steel', 'uranium']
            prices = {}
            for rs in rss:
                async with session.get(f'http://politicsandwar.com/api/tradeprice/?resource={rs}&key={api_key}') as resp:
                    resp = await resp.json()
                prices.update({f"{rs[:2]}_avg": resp['avgprice']})
                prices.update({f"{rs[:2]}_hb": resp['highestbuy']['price']})
                prices.update({f"{rs[:2]}_lb": resp['lowestbuy']['price']})
        
        return {"time": pytz.utc.localize(datetime.utcnow()).isoformat(), "prices": prices}
        # should look into removing pytz

    @commands.command(
        brief='Withdraw resources from the alliance bank',
        help='This command may only be used by Cardinals. Usage: "$withdraw <recipient> <type of resource> - <amount of resource>, <type of resource> - <amount of resource>... " Recipient can be nation name, nation id, nation link, leader name, discord id, discord name, or discord mention. Please note that spaces are ignored, so it does not matter if you type "-" and "," or " - " and ", "',
        aliases=['with', 'w']
        )
    @commands.has_any_role('Pam', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def withdraw(self, ctx, recipient, *, rss):
        async with aiohttp.ClientSession() as session:
            randy = utils.find_user(self, 465463547200012298)
            if randy['email'] == '' or randy['pwd'] == '':
                await ctx.send('Randy has not registered his PnW credentials with Fuquiem.')

            cipher_suite = Fernet(key)

            with requests.Session() as s:
                login_url = "https://politicsandwar.com/login/"
                login_data = {
                    "email": str(cipher_suite.decrypt(randy['email'].encode()))[2:-1],
                    "password": str(cipher_suite.decrypt(randy['pwd'].encode()))[2:-1],
                    "loginform": "Login"
                }
                s.post(login_url, data=login_data)

                person = utils.find_user(self, recipient)

                res = []
                for sub in rss.split(','):
                    if '-' in sub:
                        res.append(map(str.strip, sub.split('-', 1)))
                res = dict(res)

                for k, v in res.items():
                    amount = v
                    try:
                        if "." in amount:
                            num_inf = re.sub("[A-z]", "", amount)
                            amount = int(num_inf.replace(".", "")) / 10**(len(num_inf) - num_inf.rfind(".") - 1)
                            #print(amount)
                    except:
                        pass

                    if "k" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000)
                    if "m" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000000)
                    if "b" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000000000)
                    else:
                        try:
                            amount = int(amount)
                        except:
                            pass

                    if not isinstance(amount, int) and str(amount).lower() not in "any":
                        await ctx.send('Something\'s wrong with your arguments!')
                        return

                    res[k] = amount

                withdraw_url = f'https://politicsandwar.com/alliance/id=4729&display=bank'
                withdraw_data = {
                    "withmoney": '0',
                    "withfood": '0',
                    "withcoal": '0',
                    "withoil": '0',
                    "withuranium": '0',
                    "withlead": '0',
                    "withiron": '0',
                    "withbauxite": '0',
                    "withgasoline": '0',
                    "withmunitions": '0',
                    "withsteel": '0',
                    "withaluminum": '0',
                    "withtype": 'Nation',
                    "withrecipient": person['name'],
                    "withnote": 'Sent through discord.',
                    "withsubmit": 'Withdraw'
                }

                for x in withdraw_data:
                    for y in res:
                        if y in x:
                            withdraw_data[x] = res[y]

                pretty_data = withdraw_data.copy()
                for k in pretty_data.copy():
                    try:
                        int(pretty_data[k])
                        pretty_data[k.replace('with', '')] = f"{pretty_data[k]:_}".replace("_", " ")
                        pretty_data.pop(k)
                    except:
                        pretty_data[k.replace('with', '')] = f'{pretty_data.pop(k)}'

                if ctx.author.id != 891875198704431155:
                    try:
                        await ctx.send(f'Are you sure you want to continue with this transaction? (yes/no)\n```json\n{pretty_data}```')
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=40)

                        if msg.content.lower() in ['yes', 'y']:
                            start_time = (datetime.utcnow() - timedelta(seconds=5))
                            end_time = (datetime.utcnow() + timedelta(seconds=5))
                            p = s.post(withdraw_url, data=withdraw_data)
                            print(f'Response: {p}')
                        elif msg.content.lower() in ['no', 'n']:
                            await ctx.send('Transaction was canceled')
                            return
                    except asyncio.TimeoutError:
                        await ctx.send('Command timed out, you were too slow to respond.')
                        return

                success = False
                await asyncio.sleep(1)
                async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={person['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                    txids = await txids.json()
                for x in txids['data']:
                    if x['note'] == 'Sent through discord.' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                        success = True
                if success:
                    await ctx.send('I can confirm that the transaction has successfully commenced.')
                else:
                    await ctx.send(f"This transaction might have failed. Check this page to be sure:\nhttps://politicsandwar.com/nation/id={person['nationid']}&display=bank")

    @commands.command(
        brief='Deposit your resources to the alliance bank',
        help='Type "$deposit <type of resource> - <amount of resource>, <type of resource> - <amount of resource>..." Please note that spaces are ignored, so it does not matter if you type "-" and "," or " - " and ", "',
        aliases=['dep', 'dp']
        )
    async def deposit(self, ctx, *, rss):
        async with aiohttp.ClientSession() as session:
            person = utils.find_user(self, ctx.author.id)
            if person == None:
                await ctx.send("I can't find you in the database!")
                return
            elif person['email'] == '' or person['pwd'] == '':
                use_link = True
            else:
                use_link = False

            cipher_suite = Fernet(key)

            with requests.Session() as s:
                if not use_link:
                    login_url = "https://politicsandwar.com/login/"
                    login_data = {
                        "email": str(cipher_suite.decrypt(person['email'].encode()))[2:-1],
                        "password": str(cipher_suite.decrypt(person['pwd'].encode()))[2:-1],
                        "loginform": "Login"
                    }
                    s.post(login_url, data=login_data)

                res = []
                for sub in rss.split(','):
                    if '-' in sub:
                        res.append(map(str.strip, sub.split('-', 1)))
                res = dict(res)

                for k, v in res.items():
                    amount = v
                    try:
                        if "." in amount:
                            num_inf = re.sub("[A-z]", "", amount)
                            amount = int(num_inf.replace(".", "")) / 10**(len(num_inf) - num_inf.rfind(".") - 1)
                            #print(amount)
                    except:
                        pass

                    if "k" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000)
                    if "m" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000000)
                    if "b" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000000000)
                    else:
                        try:
                            amount = int(amount)
                        except:
                            pass

                    if not isinstance(amount, int) and str(amount).lower() not in "any":
                        await ctx.send('Something\'s wrong with your arguments!')
                        return

                    res[k] = amount

                req = requests.get(
                    f"http://politicsandwar.com/api/nation/id={person['nationid']}&key={api_key}").json()
                
                rss = ['aluminum', 'bauxite', 'coal', 'food', 'gasoline', 'iron', 'lead', 'money', 'munitions', 'oil', 'steel', 'uranium']
                excess = ""
                if use_link:
                    for k, v in res.items():
                        for rs in rss:
                            if k in rs:
                                excess += f"&d_{rs}={v}"
                                break
                    await ctx.send(f"Use this pre-filed link to deposit the resources: <https://politicsandwar.com/alliance/id={req['allianceid']}&display=bank{excess}>")
                    return
                else:
                    deposit_url = f'https://politicsandwar.com/alliance/id={req["allianceid"]}&display=bank'
                    deposit_data = {
                        "depmoney": '0',
                        "depfood": '0',
                        "depcoal": '0',
                        "depoil": '0',
                        "depuranium": '0',
                        "deplead": '0',
                        "depiron": '0',
                        "depbauxite": '0',
                        "depgasoline": '0',
                        "depmunitions": '0',
                        "depsteel": '0',
                        "depaluminum": '0',
                        "depnote": 'Sent through discord.',
                        "depsubmit": 'Deposit'
                    }

                    for x in deposit_data:
                        for y in res:
                            if y in x:
                                deposit_data[x] = res[y]

                    pretty_data = deposit_data.copy()
                    for k in pretty_data.copy():
                        try:
                            int(pretty_data[k])
                            pretty_data[k.replace('dep', '')] = f"{pretty_data[k]:_}".replace("_", " ")
                            pretty_data.pop(k)
                        except:
                            pretty_data[k.replace('dep', '')] = f'{pretty_data.pop(k)}'

                    try:
                        await ctx.send(f'Are you sure you want to continue with this transaction? (yes/no)\n```json\n{pretty_data}```')
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=40)

                        if msg.content.lower() in ['yes', 'y']:
                            start_time = (datetime.utcnow() - timedelta(seconds=5))
                            end_time = (datetime.utcnow() + timedelta(seconds=5))
                            p = s.post(deposit_url, data=deposit_data)
                            print(f'Response: {p}')
                        elif msg.content.lower() in ['no', 'n']:
                            await ctx.send('Transaction was canceled')
                            return
                    except asyncio.TimeoutError:
                        await ctx.send('Command timed out, you were too slow to respond.')
                        return

                    success = False
                    await asyncio.sleep(1)
                    async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={person['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                        txids = await txids.json()
                    for x in txids['data']:
                        if x['note'] == 'Sent through discord.' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                            success = True
                    if success:
                        await ctx.send('I can confirm that the transaction has successfully commenced.')
                    else:
                        await ctx.send(f"This transaction might have failed. Check this page to be sure:\nhttps://politicsandwar.com/nation/id={person['nationid']}&display=bank")

    @commands.command(
        brief='Gives you food',
        help="Sends 100k food to your nation. The command can only be used by Zealots and has a 48 hour cooldown.",
        aliases=['fd']
        )
    @commands.cooldown(1, 172800, commands.BucketType.user)
    @commands.has_any_role('Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def food(self, ctx):
        async with aiohttp.ClientSession() as session:
            randy = utils.find_user(self, 465463547200012298)
            if randy['email'] == '' or randy['pwd'] == '':
                await ctx.send('Randy has not registered his PnW credentials with Fuquiem.')

            cipher_suite = Fernet(key)

            with requests.Session() as s:
                login_url = "https://politicsandwar.com/login/"
                login_data = {
                    "email": str(cipher_suite.decrypt(randy['email'].encode()))[2:-1],
                    "password": str(cipher_suite.decrypt(randy['pwd'].encode()))[2:-1],
                    "loginform": "Login"
                }
                s.post(login_url, data=login_data)

                person = utils.find_user(self, ctx.author.id)
                
                withdraw_url = f'https://politicsandwar.com/alliance/id=4729&display=bank'
                withdraw_data = {
                    "withmoney": '0',
                    "withfood": '100000',
                    "withcoal": '0',
                    "withoil": '0',
                    "withuranium": '0',
                    "withlead": '0',
                    "withiron": '0',
                    "withbauxite": '0',
                    "withgasoline": '0',
                    "withmunitions": '0',
                    "withsteel": '0',
                    "withaluminum": '0',
                    "withtype": 'Nation',
                    "withrecipient": person['name'],
                    "withnote": 'Hunger Prevention!',
                    "withsubmit": 'Withdraw'
                }

                start_time = (datetime.utcnow() - timedelta(seconds=5))
                p = s.post(withdraw_url, data=withdraw_data)
                end_time = (datetime.utcnow() + timedelta(seconds=5))
                print(f'Response: {p}')

                success = False
                await asyncio.sleep(1)
                async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={person['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                    txids = await txids.json()
                for x in txids['data']:
                    if x['note'] == 'Hunger Prevention!' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                        success = True
                if success:
                    await ctx.send('Once upon a time there was 100k food. Now it resides in your nation.')
                else:
                    await ctx.send(f"Bugger me sideways with a hamburger! Things didn't go as planned! Please check this page to see if you got your food:\nhttps://politicsandwar.com/nation/id={person['nationid']}&display=bank")

    @commands.command(
        brief='Gives you uranium',
        aliases=['ur', 'uran'],
        help="Sends you 3k uranium. The command has a 48 hour cooldown, and may only be used by Zealots."
        )
    @commands.cooldown(1, 172800, commands.BucketType.user)
    @commands.has_any_role('Zealot', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def uranium(self, ctx):
        async with aiohttp.ClientSession() as session:
            randy = utils.find_user(self, 465463547200012298)
            if randy['email'] == '' or randy['pwd'] == '':
                await ctx.send('Randy has not registered his PnW credentials with Fuquiem.')

            cipher_suite = Fernet(key)

            with requests.Session() as s:
                login_url = "https://politicsandwar.com/login/"
                login_data = {
                    "email": str(cipher_suite.decrypt(randy['email'].encode()))[2:-1],
                    "password": str(cipher_suite.decrypt(randy['pwd'].encode()))[2:-1],
                    "loginform": "Login"
                }
                s.post(login_url, data=login_data)

                person = utils.find_user(self, ctx.author.id)

                withdraw_url = f'https://politicsandwar.com/alliance/id=4729&display=bank'
                withdraw_data = {
                    "withmoney": '0',
                    "withfood": '0',
                    "withcoal": '0',
                    "withoil": '0',
                    "withuranium": '3000',
                    "withlead": '0',
                    "withiron": '0',
                    "withbauxite": '0',
                    "withgasoline": '0',
                    "withmunitions": '0',
                    "withsteel": '0',
                    "withaluminum": '0',
                    "withtype": 'Nation',
                    "withrecipient": person['name'],
                    "withnote": 'Power outage prevention!',
                    "withsubmit": 'Withdraw'
                }

                start_time = (datetime.utcnow() - timedelta(seconds=5))
                p = s.post(withdraw_url, data=withdraw_data)
                end_time = (datetime.utcnow() + timedelta(seconds=5))
                print(f'Response: {p}')

                success = False
                await asyncio.sleep(1)
                async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={person['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                    txids = await txids.json()
                for x in txids['data']:
                    if x['note'] == 'Power outage prevention!' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                        success = True
                if success:
                    await ctx.send('Roses are red. Uranium is green. You now have 3k more uranium.')
                else:
                    await ctx.send(f"Beat me up with an eyebrow! Things didn't go as planned! Please check this page to see if you got your uranium:\nhttps://politicsandwar.com/nation/id={person['nationid']}&display=bank")

    @commands.has_any_role('Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    @commands.command(
        aliases=['ba', 'balincrement', 'bi'],
        brief="Adds value to person's balance",
        help="Create an artifical transaction record of a set amount of money"
        )
    async def baladd(self, ctx, person, diff):
        user = utils.find_user(self, person)
        message = await ctx.send("Fuck Requiem...")
        await self.balmod(diff, message, 1, user)

    @commands.has_any_role('Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    @commands.command(
        aliases=['balremove', 'br'],
        brief="Subtracts value to person's balance",
        help="Create an artifical transaction record of a set amount of money"
        )
    async def balsubtract(self, ctx, person, diff):
        user = utils.find_user(self, person)
        message = await ctx.send("Fuck Requiem...")
        await self.balmod(diff, message, -1, user)

    async def balmod(self, diff, message, prefix, user):
        change = diff
        try:
            if "." in diff:
                num_inf = re.sub("[A-z]", "", diff)
                diff = int(num_inf.replace(".", "")) / 10**(len(num_inf) - num_inf.rfind("."))
                #print(diff)
        except:
            pass

        if "k" in change.lower():
            diff = int(float(re.sub("[A-z]", "", str(diff))) * 1000)
        if "m" in change.lower():
            diff = int(float(re.sub("[A-z]", "", str(diff))) * 1000000)
        if "b" in change.lower():
            diff = int(float(re.sub("[A-z]", "", str(diff))) * 1000000000)
        else:
            try:
                diff = int(diff)
            except:
                await message.edit("I couldn't do that!")
                return

        if not isinstance(diff, int):
            await message.edit('Something\'s wrong with your arguments!')
            return

        balance = mongo.total_balance.find_one_and_update({'nationid': user['nationid']}, {"$inc": {"mo": (diff * prefix)}})
        mongo.bank_records.insert_one({"time": datetime.utcnow(), "note": "Manual adjuster", "bnkr": "0", "s_id": "0", "s_tp": 1, "r_tid": user['nationid'], "r_tp": 1, "mo": prefix * diff, "co": 0, "oi": 0, "ur": 0, "ir": 0, "ba": 0, "le": 0, "ga": 0, "mu": 0, "st": 0, "al": 0, "fo": 0 })
        if balance == None:
            await message.edit("I could not find their balance!")
            return

        await message.edit(content=f"I modified <@{user['user']}>'s balance by {(diff*prefix):,}", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @commands.command(
        aliases=['bal'],
        brief="Shows you the person's balance with the alliance bank",
        help="Accepts 0 to 1 argument. If no arguments are provided, it will display your balance with the bank. If you use leader name, nation name, nation link, nation id, discord id, discord username, discord nickname or a discord mention, you can see the balance of the person you specified. Other arguments include 'top', 'max' and 'min'. These will display the 10 people with the highest or lowest balances."
        )
    async def balance(self, ctx, *, person=''):
        message = await ctx.send('Gathering data...')
        bal_embed, user_obj = await self.balance2(ctx, message, person, None)
        if bal_embed == None:
            return
        now_time = datetime.utcnow()
        if not (4 < now_time.minute < 7):
            #jetzt=datetime.utcnow()
            await asyncio.gather(self.balance1(user_obj))
            #print((datetime.utcnow()-jetzt).seconds) 
        bal_embed, user_ob = await self.balance2(ctx, message, person, bal_embed)
        await message.edit(content="Using fresh numbers <:pepoohappy:787399051724980274>", embed=bal_embed)
    
    async def balance1(self, user_obj):
        async with aiohttp.ClientSession() as session:
            for aa in [{"id": 4729, "key": api_key, "banker": 465463547200012298}, {"id": 7531, "key": convent_key, "banker": 716986772944322635}]: # IMPORTANT, MUST HAVE UTC +0 AS DISPLAY TIME!!!
                for type in ['tax', 'bank']:
                    api_query = f"{{alliances(id:{aa['id']} first:1){{data{{{type}recs{{date sid stype rid rtype pid note money coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}}}}}}}"

                    async with session.post(f"https://api.politicsandwar.com/graphql?api_key={aa['key']}", json={'query': api_query}) as res:
                        res = (await res.json())['data']['alliances']['data'][0][f'{type}recs']
                    #print(len(res))
                    tx_list = []
                    tx_obj = {}

                    for txid in res:
                        if user_obj['nationid'] == txid['rid'] or user_obj['nationid'] == txid['sid']:
                            tx_obj['time'] = datetime.strptime(txid['date'], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                            if tx_obj['time'] < datetime(2021, 7, 4, 15):
                                #print('skipped due to recency')
                                continue
                            tx_obj['note'] = txid['note']
                            tx_obj['bnkr'] = str(txid['pid'])
                            tx_obj['s_id'] = str(txid['sid'])
                            if txid['stype'] == 3:
                                tx_obj['s_tp'] = 1  
                            else:
                                tx_obj['s_tp'] = txid['stype']
                            tx_obj['r_id'] = str(txid['rid'])
                            tx_obj['r_tp'] = txid['rtype']
                            tx_obj['mo'] = float(txid['money'])
                            tx_obj['co'] = float(txid['coal'])
                            tx_obj['oi'] = float(txid['oil'])
                            tx_obj['ur'] = float(txid['uranium'])
                            tx_obj['ir'] = float(txid['iron'])
                            tx_obj['ba'] = float(txid['bauxite'])
                            tx_obj['le'] = float(txid['lead'])
                            tx_obj['ga'] = float(txid['gasoline'])
                            tx_obj['mu'] = float(txid['munitions'])
                            tx_obj['st'] = float(txid['steel'])
                            tx_obj['al'] = float(txid['aluminum'])
                            tx_obj['fo'] = float(txid['food'])
                            tx_list.append(tx_obj)
                            tx_obj = {}

                    for tx in tx_list:
                        keys = list(tx)
                        values = list(tx.values())
                        query = []
                        for n in range(len(keys)):
                            query.append({keys[n]: values[n]})
                        res = mongo.bank_records.find_one({'$and': query})
                        if res != None:
                            #print('continue')
                            continue
                        else:
                            mongo.bank_records.insert_one(tx)
                            if tx['s_tp'] == 2 and tx['r_tp'] == 2:
                                continue
                            if tx['s_tp'] == 1 and tx['r_id'] in ['4729', '7531']:
                                mongo.total_balance.find_one_and_update({"nationid": tx['s_id']}, {"$inc": { "mo": tx['mo'], "fo": tx['fo'], "co": tx['co'], "oi": tx['oi'], "ur": tx['ur'], "le": tx['le'], "ir": tx['ir'], "ba": tx['ba'], "ga": tx['ga'], "mu": tx['mu'], "st": tx['st'], "al": tx['al']}}, upsert=True)
                            elif tx['r_tp'] == 1 and tx['note'] not in ['Automated raffle prize', 'Automated monthly raid prize', 'Free war aid for countering raiders'] and 'of the alliance bank inventory.' not in tx['note'] and tx['s_id'] in ['4729', '7531']:
                                mongo.total_balance.find_one_and_update({"nationid": tx['r_id']}, {"$inc": { "mo": -tx['mo'], "fo": -tx['fo'], "co": -tx['co'], "oi": -tx['oi'], "ur": -tx['ur'], "le": -tx['le'], "ir": -tx['ir'], "ba": -tx['ba'], "ga": -tx['ga'], "mu": -tx['mu'], "st": -tx['st'], "al": -tx['al']}}, upsert=True)
                            elif 'of the alliance bank inventory.' in tx['note'] and tx['s_id'] in ['4729', '7531']:
                                mongo.total_balance.find_one_and_update({"nationid": tx['bnkr']}, {"$inc": { "mo": -tx['mo'], "fo": -tx['fo'], "co": -tx['co'], "oi": -tx['oi'], "ur": -tx['ur'], "le": -tx['le'], "ir": -tx['ir'], "ba": -tx['ba'], "ga": -tx['ga'], "mu": -tx['mu'], "st": -tx['st'], "al": -tx['al']}}, upsert=True)
                            #print('inserted')

    async def balance2(self, ctx, message, person, bal_embed):
        async with aiohttp.ClientSession() as session:
            rss = ['aluminum', 'bauxite', 'coal', 'food', 'gasoline', 'iron', 'lead', 'money', 'munitions', 'oil', 'steel', 'uranium']
            prices = defaultdict(lambda: 0)
            async with session.post(f"https://api.politicsandwar.com/graphql?api_key={api_key}", json={'query': f"{{tradeprices(page:1){{data{{coal oil uranium iron bauxite lead gasoline munitions steel aluminum food}}}}}}"}) as temp:
                price_history = (await temp.json())['data']['tradeprices']['data']
                for entry in price_history:
                    for rs in rss:
                        if rs != 'money':
                            prices[rs] += entry[rs]
                for rs in rss:
                    prices[rs] = prices[rs]/len(price_history)
                prices['money'] = 1
            people = list(mongo.total_balance.find({}))

            def total_bal(k):
                nonlocal prices
                x = 0
                for rs in rss:
                    x += k[rs[:2]] * prices[rs]
                return x
            try:
                if person.lower() in ['top', 'max', 'min', 'low', 'high']:
                    reverse = True
                    name = 'highest'
                    if person in ['min', 'low']:
                        reverse = False
                        name = 'lowest'

                    people = sorted(people, key=lambda k: total_bal(k), reverse=reverse)
                    embed = discord.Embed(title=f"The {name} balances:",
                                        description="", color=0x00ff00)
                    n = 0
                    for ind in people:
                        if n == 10:
                            break
                        user = mongo.users.find_one({"nationid": ind['nationid']})
                        if user == None:
                            #print('balance skipped', ind['nationid'])
                            continue
                        embed.add_field(name=user['leader'],inline=False,value=f"Cumulative balance: ${round(total_bal(ind)):,}")
                        n += 1
                    await message.edit(embed=embed,content='')
                    return None, None
            except:
                pass

            if person == '':
                person = utils.find_user(self, ctx.author.id)
            else:
                person = utils.find_user(self, person)
            if person == {}:
                await message.edit(content='I could not find that person, please try again.', embed=bal_embed)
                return None, None
            bal = (mongo.total_balance.find_one({"nationid": person['nationid']}))
            if bal == None:
                await message.edit(content='I was not able to find their balance.', embed=bal_embed)
                return None, None
            bal_embed = discord.Embed(title=f"{person['leader']}'s balance",
                                    description="", color=0x00ff00)
            for rs in rss:
                amount = bal[rs[:2]]
                bal_embed.add_field(name=rs.capitalize(), value=f"{round(amount):,}")
            bal_embed.add_field(name="Converted total", value=f"{round(total_bal(bal)):,}",inline=False)
            #print(bal_embed)
            await message.edit(content="Using 1 hour old numbers <:peeposad:787399051796283392> updating to newer ones in the background...", embed=bal_embed)
            return bal_embed, person

    @commands.command(
        aliases=['val'],
        brief="Calculates the value of the resources you specify",
        help='usage: "$value <type of resource> - <amount of resource>, <type of resource> - <amount of resource>..." Please note that spaces are ignored, so it does not matter if you type "-" and "," or " - " and ", " It works by calculating the worth of the resources you specify by looking at the price of the cheapest sell offer available.'
        )
    async def value(self,ctx,*,rss=''):
        async with aiohttp.ClientSession() as session:
            message = await ctx.send('Doing API calls...')
            total = 0
            pretty_res = {}
            res = []
            for sub in rss.split(','):
                if '-' in sub:
                    res.append(map(str.strip, sub.split('-', 1)))
            res = dict(res)

            rss_list = ['food', 'coal', 'oil', 'uranium', 'bauxite',
                        'iron', 'lead', 'gasoline', 'munitions', 'aluminum', 'steel']

            for k, v in res.items():
                amount = v
                try:
                    if "." in amount:
                        num_inf = re.sub("[A-z]", "", amount)
                        amount = int(num_inf.replace(".", "")) / 10**(len(num_inf) - num_inf.rfind(".") - 1)
                        #print(amount)
                except:
                    pass

                if "k" in v.lower():
                    amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000)
                if "m" in v.lower():
                    amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000000)
                if "b" in v.lower():
                    amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000000000)
                else:
                    try:
                        amount = int(amount)
                    except:
                        pass

                if not isinstance(amount, int) and str(amount).lower() not in "any":
                    await ctx.send('Something\'s wrong with your arguments!')
                    return

                res[k] = amount
            
                for resource in rss_list:
                    if k.lower() in resource:
                        val = res[k]
                        pretty_res.update({resource: val})
                        async with session.get(f'http://politicsandwar.com/api/tradeprice/?resource={resource}&key={api_key}') as temp:
                            cost = int((await temp.json())['avgprice'])
                        total += int(res[k]) * cost
                        break
                    elif k.lower() in 'money':
                        total += int(res[k])
                        pretty_res.update({'money': res[k]})
                        break

            embed = discord.Embed(title="Value:",
                                    description=f"The current market value of...\n```{pretty_res}```\n...is ${round(total):,}", color=0x00ff00)
            await message.edit(content='', embed=embed)
    
    @commands.command(
        brief='Send people grants',
        help='This command may only be used by Cardinals. Usage: "$grant <type of resource> - <amount of resource>, <type of resource> - <amount of resource>... <recipient>" Recipient can be nation name, nation id, nation link, leader name, discord id, discord name, or discord mention. Please note that spaces are ignored, so it does not matter if you type "-" and "," or " - " and ", "'
        )
    @commands.has_any_role('Pam', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def grant(self, ctx, recipient, *, rss):
        async with aiohttp.ClientSession() as session:
            randy = utils.find_user(self, 465463547200012298)
            if randy['email'] == '' or randy['pwd'] == '':
                await ctx.send('Randy has not registered his PnW credentials with Fuquiem.')

            cipher_suite = Fernet(key)

            with requests.Session() as s:
                login_url = "https://politicsandwar.com/login/"
                login_data = {
                    "email": str(cipher_suite.decrypt(randy['email'].encode()))[2:-1],
                    "password": str(cipher_suite.decrypt(randy['pwd'].encode()))[2:-1],
                    "loginform": "Login"
                }
                s.post(login_url, data=login_data)

                person = utils.find_user(self, recipient)

                res = []
                for sub in rss.split(','):
                    if '-' in sub:
                        res.append(map(str.strip, sub.split('-', 1)))
                res = dict(res)

                for k, v in res.items():
                    amount = v
                    try:
                        if "." in amount:
                            num_inf = re.sub("[A-z]", "", amount)
                            amount = int(num_inf.replace(".", "")) / 10**(len(num_inf) - num_inf.rfind(".") - 1)
                            #print(amount)
                    except:
                        pass

                    if "k" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000)
                    if "m" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000000)
                    if "b" in v.lower():
                        amount = int(float(re.sub("[A-z]", "", str(amount))) * 1000000000)
                    else:
                        try:
                            amount = int(amount)
                        except:
                            pass

                    if not isinstance(amount, int) and str(amount).lower() not in "any":
                        await ctx.send('Something\'s wrong with your arguments!')
                        return

                    res[k] = amount

                withdraw_url = f'https://politicsandwar.com/alliance/id=4729&display=bank'
                withdraw_data = {
                    "withmoney": '0',
                    "withfood": '0',
                    "withcoal": '0',
                    "withoil": '0',
                    "withuranium": '0',
                    "withlead": '0',
                    "withiron": '0',
                    "withbauxite": '0',
                    "withgasoline": '0',
                    "withmunitions": '0',
                    "withsteel": '0',
                    "withaluminum": '0',
                    "withtype": 'Nation',
                    "withrecipient": person['name'],
                    "withnote": 'Free war aid for countering raiders',
                    "withsubmit": 'Withdraw'
                }

                for x in withdraw_data:
                    for y in res:
                        if y in x:
                            withdraw_data[x] = res[y]

                pretty_data = withdraw_data.copy()
                for k in pretty_data.copy():
                    try:
                        int(pretty_data[k])
                        pretty_data[k.replace('with', '')] = f"{pretty_data[k]:_}".replace("_", " ")
                        pretty_data.pop(k)
                    except:
                        pretty_data[k.replace('with', '')] = f'{pretty_data.pop(k)}'

                if ctx.author.id != 891875198704431155:
                    try:
                        await ctx.send(f'Are you sure you want to continue with this grant? (yes/no)\n```json\n{pretty_data}```')
                        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=40)

                        if msg.content.lower() in ['yes', 'y']:
                            start_time = (datetime.utcnow() - timedelta(seconds=5))
                            end_time = (datetime.utcnow() + timedelta(seconds=5))
                            p = s.post(withdraw_url, data=withdraw_data)
                            print(f'Response: {p}')
                        elif msg.content.lower() in ['no', 'n']:
                            await ctx.send('Grant was canceled')
                            return
                    except asyncio.TimeoutError:
                        await ctx.send('Command timed out, you were too slow to respond.')
                        return

                success = False
                await asyncio.sleep(1)
                async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={person['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                    txids = await txids.json()
                for x in txids['data']:
                    if x['note'] == 'Free war aid for countering raiders' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                        success = True
                if success:
                    await ctx.send('I can confirm that the grant has been successfully sent.')
                else:
                    await ctx.send(f"The sending of this grant might have failed. Check this page to be sure:\nhttps://politicsandwar.com/nation/id={person['nationid']}&display=bank")

    @commands.command(
        aliases=['rev'],
        brief='Revenue breakdown of a nation',
        help="The command takes one argument; a nation. If no argument is provided, it will default to the nation of the person that invoked the command. You can react with ⚔️ to get an overivew of the nation's war incomes."
        )
    @commands.has_any_role('Pupil', 'Zealot', 'Deacon', 'Advisor', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def revenue(self, ctx, person: str = None, *, build: str = None):
        message = await ctx.send('Stay with me...')
        if person == None:
            person = ctx.author.id
        db_nation = utils.find_user(self, person)

        if db_nation == {}:
            db_nation = utils.find_nation(person)
            if not db_nation:
                await message.edit(content='I could not find that person!')
                return
            db_nation['nationid'] = db_nation['id']

        nation, colors, prices, treasures, radiation, seasonal_mod = await utils.pre_revenue_calc(api_key, message, query_for_nation=True, nationid=db_nation['nationid'])

        if build != None:
            build_txt = "daily city revenue with this build"
            single_city = True
        else:
            build_txt = "daily revenue"
            single_city = False

        rev_obj = await utils.revenue_calc(message, nation, radiation, treasures, prices, colors, seasonal_mod, build, single_city, True)

        embed = discord.Embed(
            title=f"{db_nation['leader']}'s {build_txt}:", url=f"https://politicsandwar.com/nation/id={db_nation['nationid']}", description="", color=0x00ff00)
        
        if build != None:
            build = str(build).replace(', ', ',\n   ').replace("{", "{\n    ").replace("}", "\n}")
            embed.add_field(name="Build", value=f"```json\n{build}```", inline=False)

        embed.add_field(name="Incomes", value=rev_obj['income_txt'])
        embed.add_field(name="Expenses", value=rev_obj['expenses_txt'])
        embed.add_field(name="Net Revenue", value=rev_obj['net_rev_txt'])
        embed.add_field(name="Monetary Net Income", inline=False, value=rev_obj['mon_net_txt'])
        embed.set_footer(text=rev_obj['footer'])

        await message.edit(content="", embed=embed)

        if build == None:
            await message.add_reaction("⚔️")

            await asyncio.gather(
                    self.reaction_remove_checker(ctx, message, copy.deepcopy(embed)),
                    self.reaction_add_checker(ctx, message, rev_obj['nation'], prices, copy.deepcopy(embed)),
                )
    
    async def wars_revenue(self, message, nation, prices, wars_embed):
        days_since_first_war = 14
        raid_earnings = {"aluminum_used": 0, "gasoline_used": 0, "munitions_used": 0, "steel_used": 0, "money_gained": 0, "money_lost": 0, "infra_lost": 0, "gained_beige_loot": 0, "lost_beige_loot": 0, "total": 0, "aluminum": 0, "bauxite": 0, "coal": 0, "food": 0, "gasoline": 0, "iron": 0, "lead": 0, "money": 0, "munitions": 0, "oil": 0, "steel": 0, "uranium": 0}
        wars_list = nation['wars']
        if wars_list != []:
            for war in wars_list:
                if war['date'] == '-0001-11-30 00:00:00':
                    wars_list.remove(war)
            wars_list = sorted(wars_list, key=lambda k: k['date'], reverse=False)
            days_since_first_war = (datetime.utcnow() - datetime.strptime(wars_list[0]['date'], "%Y-%m-%dT%H:%M:%S%z")).days

        for war in wars_list:
            if war['attid'] == nation['id']:
                raid_earnings['gasoline_used'] += war['att_gas_used']
                raid_earnings['gasoline'] -= war['att_gas_used']
                raid_earnings['total'] -= war['att_gas_used'] * prices['gasoline']
                raid_earnings['munitions_used'] += war['att_mun_used']
                raid_earnings['munitions'] -= war['att_mun_used']
                raid_earnings['total'] -= war['att_mun_used'] * prices['munitions']
                raid_earnings['steel_used'] += war['att_steel_used']
                raid_earnings['steel'] -= war['att_steel_used']
                raid_earnings['total'] -= war['att_steel_used'] * prices['steel']
                raid_earnings['aluminum_used'] += war['att_alum_used']
                raid_earnings['aluminum'] -= war['att_alum_used']
                raid_earnings['total'] -= war['att_alum_used'] * prices['aluminum']
                raid_earnings['infra_lost'] += war['def_infra_destroyed_value']
                raid_earnings['total'] -= war['def_infra_destroyed_value']
            else:
                raid_earnings['gasoline_used'] += war['def_gas_used']
                raid_earnings['gasoline'] -= war['def_gas_used']
                raid_earnings['total'] -= war['def_gas_used'] * prices['gasoline']
                raid_earnings['munitions_used'] += war['def_mun_used']
                raid_earnings['munitions'] -= war['def_mun_used']
                raid_earnings['total'] -= war['def_mun_used'] * prices['munitions']
                raid_earnings['steel_used'] += war['def_steel_used']
                raid_earnings['steel'] -= war['def_steel_used']
                raid_earnings['total'] -= war['def_steel_used'] * prices['steel']
                raid_earnings['aluminum_used'] += war['def_alum_used']
                raid_earnings['aluminum'] -= war['def_alum_used']
                raid_earnings['total'] -= war['def_alum_used'] * prices['aluminum']
                raid_earnings['infra_lost'] += war['att_infra_destroyed_value']
                raid_earnings['total'] -= war['att_infra_destroyed_value']

            for attack in war['attacks']:
                if attack['victor'] != nation['id']:
                    if attack['moneystolen']:
                        raid_earnings['money_lost'] += attack['moneystolen']
                        raid_earnings['money'] -= attack['moneystolen']
                        raid_earnings['total'] -= attack['moneystolen']
                else:
                    if attack['moneystolen']:
                        raid_earnings['money_gained'] += attack['moneystolen']
                        raid_earnings['money'] += attack['moneystolen']
                        raid_earnings['total'] += attack['moneystolen']
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
                            if war['winner'] == nation['id']:
                                raid_earnings[rs] += amount
                                raid_earnings['total'] += amount * price
                                raid_earnings['gained_beige_loot'] += amount * price
                            else:
                                raid_earnings[rs] -= amount
                                raid_earnings['total'] -= amount * price
                                raid_earnings['lost_beige_loot'] += amount * price
                    elif "alliance bank, taking:" in text:
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
                            if war['winner'] == nation['id']:
                                raid_earnings[rs] += amount
                                raid_earnings['total'] += amount * price ## is possible to add a "leading to # of lost alliance loot" attribute
                                raid_earnings['gained_beige_loot'] += amount * price
                    else:
                        continue
        wars_embed.add_field(name="\u200b", inline=False, value="\u200b")
        wars_embed.add_field(name="War incomes (avg.)", value=f"Ground loot: ${round(raid_earnings['money_gained'] / days_since_first_war):,}\nBeige loot: ${round(raid_earnings['gained_beige_loot'] / days_since_first_war):,}")
        wars_embed.add_field(name="War expenditures (avg.)", value=f"Ground loot: ${round(raid_earnings['money_lost'] / days_since_first_war):,}\nBeige loot: ${round(raid_earnings['lost_beige_loot'] / days_since_first_war):,}\nInfra lost: ${round(raid_earnings['infra_lost'] / days_since_first_war):,}\nResources used: ${round((raid_earnings['aluminum_used'] * prices['aluminum'] + raid_earnings['gasoline_used'] * prices['gasoline'] + raid_earnings['munitions_used'] * prices['munitions'] + raid_earnings['steel_used'] * prices['steel']) / days_since_first_war):,}")
        wars_embed.add_field(name="War revenues (avg.)", value=f"Aluminum: {round(raid_earnings['aluminum'] / days_since_first_war):,}\nBauxite: {round(raid_earnings['bauxite'] / days_since_first_war):,}\nCoal: {round(raid_earnings['coal'] / days_since_first_war):,}\nFood: {round(raid_earnings['food'] / days_since_first_war):,}\nGasoline: {round(raid_earnings['gasoline'] / days_since_first_war):,}\nIron: {round(raid_earnings['iron'] / days_since_first_war):,}\nLead: {round(raid_earnings['lead'] / days_since_first_war):,}\nMunitions: {round(raid_earnings['munitions'] / days_since_first_war):,}\nOil: {round(raid_earnings['oil'] / days_since_first_war):,}\nSteel: {round(raid_earnings['steel'] / days_since_first_war):,}\nUranium: {round(raid_earnings['uranium'] / days_since_first_war):,}\nMoney: ${round((raid_earnings['money'] - raid_earnings['infra_lost']) / days_since_first_war):,}")
        wars_embed.add_field(name="War Net Income (avg.)", value=f"${round(raid_earnings['total'] / days_since_first_war):,}")
        await message.edit(content="", embed=wars_embed)
    
    async def reaction_add_checker(self, ctx, message, nation, prices, rac_embed):
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=300)
                if user.id != ctx.author.id:
                    continue
                if str(reaction.emoji) == "⚔️":
                    await self.wars_revenue(message, nation, prices, copy.deepcopy(rac_embed))

            except asyncio.TimeoutError:
                await message.edit(content="**Command timed out!**")
                break
    
    async def reaction_remove_checker(self, ctx, message, rrc_embed):
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_remove", timeout=300)
                if user.id != ctx.author.id:
                    continue
                if str(reaction.emoji) == "⚔️":
                    await message.edit(content="", embed=rrc_embed)

            except asyncio.TimeoutError:
                await message.edit(content="**Command timed out!**")
                break
        

def setup(bot):
    bot.add_cog(Economic(bot))