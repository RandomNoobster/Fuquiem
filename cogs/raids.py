import discord
import pytz
import aiohttp
import dateutil.parser
import requests
from main import mongo
from datetime import datetime, timedelta
from discord.ext import commands
import os
from cryptography.fernet import Fernet
api_key = os.getenv("api_key")
key = os.getenv("encryption_key")

moment = pytz.utc.localize(datetime.utcnow()).isoformat()

class Raids(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    """@commands.command(brief='A leaderboard showing the top 10 raiders of this month', aliases=['lb'])
    async def leaderboard(self, ctx):
        f1 = list(mongo.users.find({}))
        # currently disabled due to the extra time it requires. aftar all, any church members will be pushed out of the lb when enough pupils have declared wars
        #church_nations = list(mongo.church_nations.find({}))[0]['results']
        # for x in church_nations:
        #    for y in f1:
        #        if x['name'] == y['name']:
        #            f1.remove(y)
        embed = discord.Embed(
            title="Leaderboard", description="This month's top 10 raiders:", color=0x00ff00)
        embed.set_footer(text='Updated hourly')
        users = sorted(f1, key=lambda k: len(k['raids']))
        users.reverse()
        n = 1
        for x in users:
            if n < 11:  # what the hell is this mess?!?!?!?
                user = await self.bot.fetch_user(x['user'])
                embed.add_field(
                    name="\u200b", value=f"#{n} - {user} with {len(x['raids'])} wars\n\n", inline=False)
                n += 1
        await ctx.send(embed=embed)

    @commands.command(brief='Resets the monthly leaderboard and sends money to the participants')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def raids_draw(self, ctx):
        await self.draw()
        # merely a debugging command

    async def draw(self):
        async with aiohttp.ClientSession() as session:
            debug_channel = self.bot.get_channel(739155202640183377) ## ooooooopppspoaspaospaos
            f1 = list(mongo.users.find({}))
            users = sorted(f1, key=lambda k: len(k['raids']))
            users.reverse()
            users = users[0:10]
            channel = self.bot.get_channel(850302301838114826) ## convent channell
            await channel.send(f"#1 - {(await self.bot.fetch_user(users[0]['user'])).mention} has won this month's raiding competition with {len(users[0]['raids'])} wars! The runner-ups were:\n\n#2 - {(await self.bot.fetch_user(users[1]['user'])).mention} ({len(users[1]['raids'])} wars)\n\n#3 - {(await self.bot.fetch_user(users[2]['user'])).mention} ({len(users[2]['raids'])} wars)\n\nThe top 10 raiders of this month will recieve $500k multiplied by the number of wars they each declared. Enjoy!")
            Database = self.bot.get_cog('Database')
            randy = await Database.find_user(465463547200012298)
            if len(randy['email']) <= 1 or len(randy['pwd']) <= 1:
                await debug_channel.send("<@465463547200012298>'s credentials are wrong?")
            for user in users:
                if len(user['raids']) > 0:
                    cipher_suite = Fernet(key)

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
                            "withmoney": str(500000 * len(user['raids'])), ## should be 500k
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
                            "withrecipient": user['name'],
                            "withnote": 'Automated monthly raid prize',
                            "withsubmit": 'Withdraw'
                        }

                        start_time = (datetime.utcnow() - timedelta(seconds=5))
                        p = s.post(withdraw_url, data=withdraw_data)
                        end_time = (datetime.utcnow() + timedelta(seconds=5))
                        print(f'Response: {p}')
                        await debug_channel.send(f'Response: {p}')
                        success = False

                        async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={user['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                            txids = await txids.json()
                        for x in txids['data']:
                            if x['note'] == 'Automated monthly raid prize' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                                success = True
                        if success:
                            await debug_channel.send(f"I can confirm that the transaction to {user['name']} ({user['leader']}) has successfully commenced.")
                        else:
                            await debug_channel.send(f"<@465463547200012298> the transaction to {user['name']} ({user['leader']}) might have failed. Check this page to be sure:\nhttps://politicsandwar.com/nation/id={user['nationid']}&display=bank")
                        
        mongo.users.update_many({}, {"$set": {"raids": []}})

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def rcheck(self, ctx):
        await self.raids()
        # merely a debugging command

    async def raids(self):
        users = list(mongo.users.find({}))
        wars = requests.get(
            f'https://politicsandwar.com/api/wars/300&key={api_key}&alliance_id=7531').json()['wars']
        for x in wars:
            if x['attackerAA'] == "Convent of Atom":
                if ((dateutil.parser.parse(x['date'])).replace(tzinfo=pytz.UTC)).month == datetime.now().month:
                    for y in users:
                        if x['attackerID'] == int(y['nationid']):
                            if x['warID'] not in y['raids']:
                                print('war not registered')
                                y['raids'].append(x['warID'])
                                mongo.users.find_one_and_update({"user": y['user']}, {
                                                                '$set': {"raids": y['raids']}})"""

def setup(bot):
    bot.add_cog(Raids(bot))