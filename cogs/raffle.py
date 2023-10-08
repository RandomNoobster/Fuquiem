import random
import discord
import requests
import utils
from main import mongo
from datetime import datetime, timedelta
from discord.ext import commands
import os
import pathlib
import aiohttp
from cryptography.fernet import Fernet
api_key = os.getenv("api_key")
key = os.getenv("encryption_key")


class Raffle(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Signs you up for the raffle!')
    @commands.has_any_role('Pupil')
    async def login(self, ctx):
        x = mongo.users.find_one({"user": ctx.author.id})
        if x == None:
            await ctx.send("You are not in the database! <@465463547200012298> will have to add you!")
            return
        api_nation = requests.get(
            f"http://politicsandwar.com/api/nation/id={x['nationid']}&key=e5171d527795e8").json()
        if api_nation['allianceid'] != "8819":
            await ctx.send("You are not in the Convent!")
            return
        elif api_nation['cities'] >= 15:
            await ctx.send(f"You have {api_nation['cities']} cities. You should be reaching towards the Church!")
        else:
            if x['signedup']:
                await ctx.send('You have already signed up!')
                return
            else:
                mongo.users.find_one_and_update(
                    {"user": x['user']}, {'$set': {"signedup": True, "signups": x['signups'] + 1}})
                await ctx.send(content=f"{ctx.author.mention} has signed up!", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @commands.command(alias=['statistics', 'statsget'], brief='Shows stats, accepts 1 argument', help='By default it sorts by the winrate. Optional argument can be "su" for sorting by signups, "wins" for sorting by wins or if you would for some reason like to do something completely unnecessary, you can do "wr".')
    async def stats(self, ctx, sort='wr'):
        message = await ctx.send("Scanning social security numbers...")
        users = list(mongo.users.find({"signups": {'$gt': 0}}))
        fields = []
        if sort.lower() == 'su':
            users = sorted(users, key=lambda k: k['signups'])
            users.reverse()
        elif sort.lower() == 'wins':
            users = sorted(users, key=lambda k: k['wins'])
            users.reverse()
        elif sort.lower() == 'wr':
            users = sorted(users, key=lambda k: k['wins'] / k['signups'])
            users.reverse()
        for x in users:
            user = ctx.guild.get_member(x['user'])
            if user == None:
                print('for stats, skipped', x['leader'])
                continue

            if x['signups'] == 0:
                winrate = 0
            else:
                winrate = round(x['wins'] / x['signups'] * 100)

            if x['wins'] == 1:
                wins_plural = 'win'
            else:
                wins_plural = 'wins'
            if x['signups'] == 1:
                su_plural = 'signup'
            else:
                su_plural = 'signups'

            fields.append(
                {"name": user, "value": f"↳ has {x['wins']} {wins_plural}, {x['signups']} {su_plural}, and a {winrate}% winrate"})
        embeds = utils.embed_pager("Raffle stats", fields)
        await message.edit(content="", embed=embeds[0])
        await utils.reaction_checker(self, message, embeds)

    @commands.command(brief='Shows a list of everyone that has signed up for the daily raffle')
    async def get(self, ctx):
        current = list(mongo.users.find({"signedup": True}))
        mention_string = ''
        n = 0
        for x in current:
            user = ctx.guild.get_member(x['user'])
            mention_string += f"**{user}**"
            n += 1
            if n < len(current) - 1:
                mention_string += ', '
            if n == len(current) - 1:
                mention_string += ' & '
        plural = 'people) have'
        if len(current) == 1:
            plural = 'person) has'
        mention_string += f" ({len(current)} {plural} signed up."
        await ctx.send(content=mention_string, allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @commands.command(brief='Debugging cmd, requires admin perms')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def draw(self, ctx):
        await self.draw_func()
        # merely a debugging command

    async def draw_func(self):
        async with aiohttp.ClientSession() as session:
            channel = self.bot.get_channel(850302301838114826)
            debug_channel = self.bot.get_channel(
                677883771810349067)  # ooooooopppspoaspaospaos

            current = list(mongo.users.find({"signedup": True}))
            if len(current) == 0:
                await channel.send('Nobody has signed up yet!')
                return

            amount = "5000000"
            if len(current) < 5:
                amount = "2500000"

            winners = []

            weights = [round((2 - (x['wins'] / x['signups'])) ** 10, 3)
                       for x in current]
            winner1 = random.choices(current, weights=weights, k=1)[0]
            winners.append(winner1)
            current.remove(winner1)

            if len(current) > 19:
                weights = [round((2 - (x['wins'] / x['signups'])) ** 10, 3)
                           for x in current]
                winner2 = random.choices(current, weights=weights, k=1)[0]
                winners.append(winner2)

            with open(pathlib.Path.cwd() / 'data' / 'attachments' / 'money.gif', 'rb') as gif:
                gif = discord.File(gif)
                if len(winners) == 2:
                    msg = await channel.send(content=f"<@{winner1['user']}> and <@{winner2['user']}> have won today's raffle. Your prizes should have been sent automatically. <@&747179040720289842>, you can now sign up again!", file=gif)
                elif len(winners) == 1:
                    msg = await channel.send(content=f"<@{winner1['user']}> has won today's raffle. Your prize should have been sent automatically. <@&747179040720289842>, you can now sign up again!", file=gif)
                await msg.add_reaction('<:atomism_church:704914811175043192>')

            for winner in winners:

                mongo.users.find_one_and_update(
                    {"user": winner['user']}, {'$inc': {"wins": 1}})
                mongo.users.update_many({}, {'$set': {"signedup": False}})

                randy = utils.find_user(self, 465463547200012298)
                if len(randy['email']) <= 1 or len(randy['pwd']) <= 1:
                    await debug_channel.send("<@465463547200012298>'s credentials are wrong?")

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
                        "withmoney": amount,
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
                        "withrecipient": winner['name'],
                        "withnote": 'Automated raffle prize',
                        "withsubmit": 'Withdraw'
                    }

                    start_time = (datetime.utcnow() - timedelta(seconds=5))
                    p = s.post(withdraw_url, data=withdraw_data)
                    end_time = (datetime.utcnow() + timedelta(seconds=5))
                    print(f'Response: {p}')
                    await debug_channel.send(f'Response: {p}')
                    success = False

                    async with session.get(f"http://politicsandwar.com/api/v2/nation-bank-recs/{api_key}/&nation_id={winner['nationid']}&min_tx_date={datetime.today().strftime('%Y-%m-%d')}r_only=true") as txids:
                        txids = await txids.json()
                    for x in txids['data']:
                        if x['note'] == 'Automated raffle prize' and start_time <= datetime.strptime(x['tx_datetime'], '%Y-%m-%d %H:%M:%S') <= end_time:
                            success = True

                    if success:
                        await debug_channel.send(f"I can confirm that the transaction to {winner['name']} ({winner['leader']}) has successfully commenced.")
                    else:
                        await debug_channel.send(f"<@465463547200012298> the transaction to {winner['name']} ({winner['leader']}) might have failed. Check this page to be sure:\nhttps://politicsandwar.com/nation/id={winner['nationid']}&display=bank")


def setup(bot):
    bot.add_cog(Raffle(bot))
