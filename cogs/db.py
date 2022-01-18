from cryptography import fernet
import discord
from discord.ext import commands
import requests
from cryptography.fernet import Fernet
import re
from main import mongo
import aiohttp
import utils
import os
from datetime import datetime, timedelta
import asyncio
api_key = os.getenv("api_key")
convent_key = os.getenv("convent_api_key")
key = os.getenv("encryption_key")


class Database(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
 
    @commands.command(brief='Meant for debugging purposes')
    @commands.has_any_role('Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def debug(self, ctx):
        """print('debugging')
        current = list(mongo['users'].find({}))
        church = requests.get(
            f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}').json()['nations']
        convent = requests.get(
            f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}').json()['nations']
        convent_ids = [str(nation['nationid']) for nation in convent]
        church_ids = [str(nation['nationid']) for nation in church]
        n = 0
        m = 0
        for x in current:
            for nation in convent_ids:
                if x['nationid'] == nation:
                    try:
                        print(x['nationid'], 'in the convent')
                        x.pop('tax_bracket')
                        n += 1
                        mongo.users.find_one_and_delete({"user": x['user']})
                        mongo.users.insert_one(x)
                    except KeyError:
                        print('no tax_bracket', x['nationid'])
            for nation in church_ids:
                if x['nationid'] == nation:
                    try:
                        print(x['nationid'], 'in the church')
                        x.pop('tax_bracket')
                        m += 1
                        mongo.users.find_one_and_delete({"user": x['user']})
                        mongo.users.insert_one(x)
                    except KeyError:
                        print('no tax_bracket', x['nationid'])
        #merely a debugging command
        print(n,'n')
        print(m,'m')"""

        """current = list(mongo['users'].find({}))
        for x in current:
            #x['nationid'] = str(x['id'])
            x['name'] = x['nation']
            #x['leader'] = x['leader_name']
            #del x['id']
            del x['nation']
            #del x['leader_name']
            mongo.users.find_one_and_delete({"user": x['user']})
            mongo.users.insert_one(x)"""


    @commands.command(brief='Add someone to the db', help='First argument should be a ping, and the second argument should be a nation link.', aliases=['dab'])
    @commands.has_any_role('Internal Affairs', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def dba(self, ctx, disc: discord.User, nation):
        async with aiohttp.ClientSession() as session:
            nid = str(re.sub("[^0-9]", "", nation))
            current = list(mongo['users'].find({}))
            for x in current:
                if x['user'] == disc.id:
                    await ctx.send(f'They are already in the db!')
                    return
            async with session.get(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': f"{{nations(first:1 id:{nid}){{data{{id leader_name nation_name alliance{{name id}}}}}}}}"}) as temp:
                try:
                    nation = (await temp.json())['data']['nations']['data'][0]
                except:
                    print((await temp.json())['errors'])
                    return
            mongo.users.insert_one({"user": disc.id, "nationid": nid, "name": nation['nation_name'], "leader": nation['leader_name'], "signups": 0, "wins": 0, "raids": [], "email": '', 'pwd': '', 'signedup': False, "audited": False, "beige_alerts": []})
            await ctx.send(content=f"I added <@{disc.id}> with the nation {nid}.", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @commands.command(breif='Can only be used in DMs with the bot, accepts two arguments', help='This command can only be used in direct messages (DMs) with Fuquiem. It accepts two arguments, the first being your email and the second being your password. You can update the credentials anytime, and they can be reset by not including any arguments (simply saying "$setcredentials").', aliases=['setcred', 'sc'])
    @commands.dm_only()
    async def setcredentials(self, ctx, email='', *, pwd=''):
        if pwd == '' and len(email) > 1:
            await ctx.send("You can't supply 1 argument, for this command I only accept 0 or 2.")
            return

        person = mongo.users.find_one({"user": ctx.author.id})
        cipher_suite = Fernet(key)
        person['email'] = str(cipher_suite.encrypt(email.encode()))[2:-1]
        person['pwd'] = str(cipher_suite.encrypt(pwd.encode()))[2:-1]
        mongo.users.find_one_and_update({"user": ctx.author.id}, {
                                        '$set': {"email": person['email'], "pwd": person['pwd']}})

        await ctx.send(f'Your credentials were updated.\nEmail: {email}\nPassword: {pwd}')

    @commands.command(breif='Shows you the credentials you have set to your account.', aliases=['mc', 'myc', 'mycreds'])
    @commands.dm_only()
    async def mycredentials(self, ctx):
        cipher_suite = Fernet(key)
        person = await utils.find_user(self, ctx.author.id)
        try:
            email = str(cipher_suite.decrypt(person['email'].encode()))[2:-1]
            pwd = str(cipher_suite.decrypt(person['pwd'].encode()))[2:-1]
        except fernet.InvalidToken:
            await ctx.send("It seems like you haven't registered any credentials.")
            return
        await ctx.send(f"I have registered your PnW credentials as:\nEmail: {email}\nPassword: {pwd}")

    @commands.command(brief="Get an overview of people in need of linkage or unlikage", aliases=['ul', 'unlink', 'registered', 'registration'], help="Shows a list of people that can be removed from the db. The reasons are also listed. It also shows people that are in the alliance, but not in the db.")
    async def unlinked(self, ctx):
        message = await ctx.send("Working on it...")
        current = list(mongo['users'].find({}))
        heathen_role = ctx.guild.get_role(434248817005690880)
        members = []
        member_ids = []
        fields = []
        
        for user in ctx.guild.members:
            if heathen_role not in user.roles and not user.bot:
                members.append(user)
        
        for x in current:
            member_ids.append(x['user'])
        
        for member in members:
            if member.id not in member_ids:
                fields.append({"name": member, "value": "**in the discord, but not not registered**"})
        
        church = requests.get(
            f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}').json()['nations']
        convent = requests.get(
            f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}').json()['nations']
        nations = church + convent
        nation_ids = [str(nation['nationid']) for nation in nations]
        
        heathen_role = ctx.guild.get_role(434248817005690880)
        for member in current:
            un_register = False
            text = ""
            discord_member = ctx.guild.get_member(member['user'])
            discord_user = None
            if member['nationid'] not in nation_ids:
                un_register = True
                if not discord_user:
                    discord_user = await self.bot.fetch_user(member['user'])
                text += "not in-game\n"
            if heathen_role in discord_member.roles:
                un_register = True
                if not discord_user:
                    discord_user = await self.bot.fetch_user(member['user'])
                text += "heathen\n"
            if discord_member == None:
                un_register = True
                discord_user = await self.bot.fetch_user(member['user'])
                text += "not in the server\n"
            if un_register:
                fields.append({"name": f'{discord_user} ({discord_user.id})', "value": text})
        
        if len(fields) == 0:
            await message.edit(content='All the right people are registered!')
            return
        else:
            embeds = utils.embed_pager("Registration", fields)
            await message.edit(content="", embed=embeds[0])
            await utils.reaction_checker(self, message, embeds)

    @commands.command(brief='Remove someone from the db')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def dbd(self, ctx, *, arg):
        person = await utils.find_user(self, arg)
        if person == {}:
            await ctx.send('I do not know who that is.')
            return
        to_delete = mongo.users.find_one({"user": person['user']})
        if to_delete == None:
            await ctx.send('I do not know who that is.')
            return
        mongo.leaved_users.insert_one(to_delete)
        await ctx.send(f'I am deleting this from the db:\n{to_delete}')
        mongo.users.delete_one({"user": person['user']})
        await ctx.send('It was sucessfully deleted')

    @commands.command(brief='Move someone back from the secondary db', help='')
    @commands.has_any_role('Internal Affairs', 'Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def restore(self, ctx, *, arg):
        message = await ctx.send("Asking James for selfies...")
        result = None
        async with aiohttp.ClientSession() as session:
            try:
                int(arg)
                x = mongo.leaved_users.find_one({"nationid": str(arg)})
                if x:
                    result = x        
            except:
                pass
            if not result:
                try:
                    x = mongo.leaved_users.find_one({"user": int(arg)})
                    if x:
                        result = x        
                except:
                    pass
            current = list(mongo.leaved_users.find({}))
            if not result:
                try:
                    for x in current:
                        if arg.lower() in x['name'].lower():
                            result = x
                        elif arg.lower() in x['leader'].lower():
                            result = x
                except:
                    pass
            if not result:
                try:
                    members = self.bot.get_all_members()
                    for member in members:
                        if arg.lower() in member.name.lower():
                            x = mongo.leaved_users.find_one({"user": member.id})
                            result = x
                        elif arg.lower() in member.display_name.lower():
                            x = mongo.leaved_users.find_one({"user": member.id})
                            result = x
                        elif str(member).lower() == arg.lower():
                            x = mongo.leaved_users.find_one({"user": member.id})
                            result = x
                except:
                    pass
            if not result:
                try:
                    for x in current:
                        if int(x['nationid']) == int(re.sub("[^0-9]", "", arg)):
                            result = x
                        elif int(x['user']) == int(re.sub("[^0-9]", "", arg)):
                            result = x
                except:
                    pass
            if result:
                content = ""
                fatal = False
                for key in ["user", "nationid", "name", "leader", "signups", "wins", "raids", "email", "pwd", "signedup", "audited", "beige_alerts"]:
                    if key not in result:
                        if key in ["user", "nationid"]:
                            content += "**FATAL** "
                            fatal = True
                        content += f"there is no `{key}`\n"
                        result[key] = None
                    elif not result[key]:
                        if key in ["user", "nationid"]:
                            content += f"**FATAL** `{key}` is empty: `{result[key]}\u200b`\n"
                            fatal = True
                if content:
                    content = "I encountered the following issues:\n\n" + content + "\nI fixed any non-fatal issues. "
                if fatal:
                    await message.edit(content=content)
                    return
                
                async with session.get(f'https://api.politicsandwar.com/graphql?api_key={api_key}', json={'query': f"{{nations(first:1 id:{result['nationid']}){{data{{id leader_name nation_name alliance{{name id}}}}}}}}"}) as temp:
                    try:
                        nation = (await temp.json())['data']['nations']['data'][0]
                    except:
                        print((await temp.json())['errors'])
                        return
                new_obj = {"user": result['user'], "nationid": result['nationid'], "name": nation['nation_name'], "leader": nation['leader_name'], "signups": result['signups'] or 0, "wins": result['wins'] or 0, "raids": result['raids'] or [], "email": result['email'] or '', 'pwd': result['pwd'] or '', 'signedup': result['signedup'] or False, "audited": result['audited'] or False, "beige_alerts": result['beige_alerts'] or []}
                try:
                    await message.edit(content=f'I was able to find a match in the secondary database. {content}Do you want me to attempt to restore them to the primary database? (yes/no)\n```\n{new_obj}```')
                    msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.id == ctx.channel.id, timeout=40)
                    if msg.content.lower() in ['yes', 'y']:
                        pass
                    elif msg.content.lower() in ['no', 'n']:
                        await ctx.send('Transaction was canceled')
                        return
                except asyncio.TimeoutError:
                    await ctx.send('Command timed out, you were too slow to respond.')
                    return
            else:
                await ctx.send("I was not able to find any matches!")

            mongo.users.insert_one(new_obj)
            mongo.leaved_users.find_one_and_delete({"user": result['user']})
            await ctx.send(content=f"I added <@{result['user']}> with the nation {result['nationid']}.```{new_obj}```", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        to_delete = mongo.users.find_one({"user": member.id})
        if to_delete == None:
            return
        print('deleting user')
        mongo.leaved_users.insert_one(to_delete)
        mongo.users.delete_one({"user": member.id})

    @commands.command(brief='The ENTIRE db!')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def db(self, ctx):
        current = list(mongo['users'].find({}))
        fields = []        
        for x in current:
            fields.append({"name": "\u200b", "value": f"<@!{x['user']}> - [{x['name']}](https://politicsandwar.com/nation/id={x['nationid']})"})
        embeds = utils.embed_pager("Database", fields)
        message = await ctx.send(embed=embeds[0])
        await utils.reaction_checker(self, message, embeds)

    @commands.command(brief='Display the secondary database with all deleted users', aliases=['removeddb', 'rdb'])
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def removed_db(self, ctx):
        current = list(mongo['leaved_users'].find({}))
        fields = []        
        for x in current:
            fields.append({"name": x['leader'], "value": f"```{x}```"})
        embeds = utils.embed_pager("Database", fields, inline=False)
        message = await ctx.send(embed=embeds[0])
        await utils.reaction_checker(self, message, embeds)

    @commands.command(brief='Anyways, who is that guy?', aliases=['whois'])
    async def who(self, ctx, *, arg):
        person = await utils.find_user(self, arg)
        if person == {} or person == None:
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
                        result = None
            if not result:
                await ctx.send('I could not find that person!')
                return
            else:
                print(result)
                embed = discord.Embed(title=result['leader'], description=f"[{result['nation']}](https://politicsandwar.com/nation/id={result['nationid']})")
                await ctx.send(embed=embed)
                return
        embed = discord.Embed(title=str(await self.bot.fetch_user(person['user'])), description=f"[{person['name']}](https://politicsandwar.com/nation/id={person['nationid']})")
        await ctx.send(embed=embed)

    @commands.command(brief='Search for deleted user', aliases=['dw'], help="Search for a user in the secondary database with all deleted users. Usage is identical to that of $who")
    async def del_who(self, ctx, *, arg):
        #print(arg)
        found = False
        current = current = list(mongo['leaved_users'].find({}))
        members = self.bot.get_all_members()
        guild = self.bot.get_guild(434071714893398016)
        heathen_role = guild.get_role(434248817005690880)
        try:
            await self.bot.fetch_user(int(arg))
            #print('just tried a user')
            for x in current:
                if x['user'] == int(arg):
                    found = True
                    person = x
        except:
            try:
                arg.startswith('<@') and arg.endswith('>')
                if arg.startswith('<@!'):
                    user_id = arg[(arg.index('!')+1):arg.index('>')]
                else:
                    user_id = arg[(arg.index('@')+1):arg.index('>')]
                #print('mention string?')
                for x in current:
                    if x['user'] == int(user_id):
                        found = True
                        person = x
            except:
                try:
                    int(arg)
                    #print('nation id?')
                    for x in current:
                        if x['nationid'] == arg:
                            found = True
                            person = x
                except:
                    try:
                        #print('discord name?')
                        for member in members:
                            if member.name.lower() == arg.lower() and heathen_role not in member.roles:
                                x = mongo.leaved_users.find_one({"user": member.id})
                                found = True
                                person = x
                            elif member.display_name.lower() == arg.lower() and heathen_role not in member.roles:
                                x = mongo.leaved_users.find_one({"user": member.id})
                                found = True
                                person = x
                            elif str(member).lower() == arg.lower() and heathen_role not in member.roles:
                                x = mongo.leaved_users.find_one({"user": member.id})
                                found = True
                                person = x
                            #print('name, leader?')
                            for x in current:
                                if x['name'].lower() == arg.lower():
                                    found = True
                                    person = x
                                elif x['leader'].lower() == arg.lower():
                                    found = True
                                    person = x
                        1/0
                    except:
                        try:
                            #print('link?')
                            for x in current:
                                if x['nationid'] == arg[(arg.index('=')+1):]:
                                    found = True
                                    person = x
                        finally:
                            pass
                    finally:
                        pass
                finally:
                    pass
            finally:
                pass
        finally:
            if not found or person == None:
                await ctx.send('I could not find that person in the list of deleted users.')
                return
            else: 
                embed = discord.Embed(title=str(await self.bot.fetch_user(person['user'])), description=f"```{person}```")
                await ctx.send(embed=embed)
                return


def setup(bot):
    bot.add_cog(Database(bot))
