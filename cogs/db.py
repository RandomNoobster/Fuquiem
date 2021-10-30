from cryptography import fernet
import discord
from discord.ext import commands
import requests
from cryptography.fernet import Fernet
import re
from main import mongo
import os
api_key = os.getenv("api_key")
convent_key = os.getenv("convent_api_key")
key = os.getenv("encryption_key")


class Database(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def find_user(self, arg):
        #print(arg)
        found = False
        current = current = list(mongo['users'].find({}))
        members = self.bot.get_all_members()
        guild = self.bot.get_guild(434071714893398016)
        heathen_role = guild.get_role(434248817005690880)
        try:
            await self.bot.fetch_user(int(arg))
            #print('just tried a user')
            for x in current:
                if x['user'] == int(arg):
                    found = True
                    return x
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
                        return x
            except:
                try:
                    int(arg)
                    #print('nation id?')
                    for x in current:
                        if x['nationid'] == arg:
                            found = True
                            return x
                except:
                    try:
                        #print('discord name?')
                        for member in members:
                            if arg.lower() in member.name.lower() and heathen_role not in member.roles:
                                x = mongo.users.find_one({"user": member.id})
                                found = True
                                return x
                            elif arg.lower() in member.display_name.lower() and heathen_role not in member.roles:
                                x = mongo.users.find_one({"user": member.id})
                                found = True
                                return x
                            elif str(member).lower() == arg.lower() and heathen_role not in member.roles:
                                x = mongo.users.find_one({"user": member.id})
                                found = True
                                return x
                            #print('name, leader?')
                            for x in current:
                                if arg.lower() in x['name'].lower():
                                    found = True
                                    return x
                                elif arg.lower() in x['leader'].lower():
                                    found = True
                                    return x
                        1/0
                    except:
                        try:
                            #print('link?')
                            for x in current:
                                if x['nationid'] == arg[(arg.index('=')+1):]:
                                    found = True
                                    return x
                        finally:
                            pass
                    finally:
                        pass
                finally:
                    pass
            finally:
                pass
        finally:
            if not found:
                return {}

    async def find_nation(self, arg):
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
        return result
    
    async def find_nation_plus(self, arg):
        nation = await self.find_nation(arg)
        if nation == None:
            nation = await self.find_user(arg)
            if nation == {}:
                return None
            else:
                nation = await self.find_nation(nation['nationid'])
                if nation == None:
                    return None
        return nation


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

        current = list(mongo['users'].find({}))
        for x in current:
            x['vm'] = False
            mongo.users.find_one_and_delete({"user": x['user']})
            mongo.users.insert_one(x)


    @commands.command(brief='Add someone to the db', help='First argument should be a ping, and the second argument should be a nation link.', aliases=['dab'])
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def dba(self, ctx, disc: discord.User, nation):
        print(disc)
        current = list(mongo['users'].find({}))
        for x in current:
            if x['user'] == disc.id:
                await ctx.send(f'They are already in the db!')
                return

        if "=" in nation:
            nid = nation[(nation.index('=')+1):]
        else:
            try:
                int(nation)
                nid = nation
            except:
                await ctx.send("Something's wrong with your arguments")
        response = requests.get(
            f"http://politicsandwar.com/api/nation/id={nid}&key={api_key}").json()
        mongo.users.insert_one({"user": disc.id, "nationid": nid, "name": response['name'], "leader": response['leadername'], "signups": 0, "wins": 0, "raids": [
        ], "email": '', 'pwd': '', 'signedup': False, "audited": False, "beige_alerts": []})
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
        person = await self.find_user(self, ctx.author.id)
        try:
            email = str(cipher_suite.decrypt(person['email'].encode()))[2:-1]
            pwd = str(cipher_suite.decrypt(person['pwd'].encode()))[2:-1]
        except fernet.InvalidToken:
            await ctx.send("It seems like you haven't registered any credentials.")
            return
        await ctx.send(f"I have registered your PnW credentials as:\nEmail: {email}\nPassword: {pwd}")

    @commands.command(brief="Get an overview of people in need of linkage or unlikage", aliases=['ul', 'unlink', 'registered', 'registration'], help="Shows a list of people that can be removed from the db. The reasons are also listed. It also shows people that are in the alliance, but not in the db.")
    async def unlinked(self, ctx):
        current = list(mongo['users'].find({}))
        heathen_role = ctx.guild.get_role(434248817005690880)
        embed = discord.Embed(
            title='Registration:', description='', color=0x00ff00)
        members = []
        member_ids = []

        for user in ctx.guild.members:
            if heathen_role not in user.roles and not user.bot:
                members.append(user)

        for x in current:
            member_ids.append(x['user'])

        for member in members:
            if member.id not in member_ids:
                embed.add_field(
                    name=member, value='... is not registered.', inline=False)

        church = requests.get(
            f'http://politicsandwar.com/api/alliance-members/?allianceid=4729&key={api_key}').json()['nations']
        convent = requests.get(
            f'http://politicsandwar.com/api/alliance-members/?allianceid=7531&key={convent_key}').json()['nations']
        nations = church + convent
        nation_ids = [str(nation['nationid']) for nation in nations]

        for member in current:
            discord_member = ctx.guild.get_member(member['user'])
            heathen_role = ctx.guild.get_role(434248817005690880)
            if discord_member == None:
                discord_user = await self.bot.fetch_user(member['user'])
                embed.add_field(
                    name=f'{discord_user} ({discord_user.id})', value='... can be un-registered, they are no longer in the server.', inline=False)
            if discord_member not in ctx.guild.members or heathen_role in discord_member.roles:
                discord_user = await self.bot.fetch_user(member['user'])
                embed.add_field(
                    name=f'{discord_user} ({discord_user.id})', value='... can be un-registered, they are a heathen.', inline=False)
            if member['nationid'] not in nation_ids:
                discord_user = await self.bot.fetch_user(member['user'])
                embed.add_field(
                    name=f'{discord_user} ({discord_user.id})', value='... can be un-registered, they are no longer in the in-game aa.', inline=False)
        if len(embed.fields) == 0:
            await ctx.send('All the right people are registered!')
            return
        else: 
            await ctx.send(embed=embed)

    @commands.command(brief='Remove someone from the db')
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def dbd(self, ctx, *, arg):
        person = await self.find_user(arg)
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
        n = 0
        embed = discord.Embed(title="Database", description="", color=0x00ff00)
        for x in current:
            if n == 25:
                await ctx.send(embed=embed)
                embed.clear_fields()
                n = 0
            embed.add_field(
                name="\u200b", value=f"<@!{x['user']}> - [{x['name']}](https://politicsandwar.com/nation/id={x['nationid']})", inline=False)
            n += 1
        await ctx.send(embed=embed)

    @commands.command(brief='Display the secondary database with all deleted users', aliases=['removeddb', 'rdb'])
    @commands.has_any_role('Acolyte', 'Cardinal', 'Pontifex Atomicus', 'Primus Inter Pares')
    async def removed_db(self, ctx):
        current = list(mongo['leaved_users'].find({}))
        n = 0
        embed = discord.Embed(title="Database", description="", color=0x00ff00)
        for x in current:
            if n == 25:
                await ctx.send(embed=embed)
                embed.clear_fields()
                n = 0
            embed.add_field(
                name="\u200b", value=f"```{x}```", inline=False)
            n += 1
        await ctx.send(embed=embed)

    @commands.command(brief='Anyways, who is that guy?', aliases=['whois'])
    async def who(self, ctx, *, arg):
        person = await self.find_user(self, arg)
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
