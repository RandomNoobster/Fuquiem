from dotenv import load_dotenv
from datetime import datetime
import dateutil.parser
from pymongo.mongo_client import MongoClient
import keep_alive
import pymongo
import aiohttp
#from threading import Thread
#import asyncio
import pytz
#import traceback
import os
import ssl
import discord
from discord.ext import commands
intents = discord.Intents.default()
intents.members = True
load_dotenv()

client = pymongo.MongoClient(os.getenv("pymongolink"), ssl_cert_reqs=ssl.CERT_NONE)
version = os.getenv("version")
mongo = client[str(version)]

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print('Bot is ready')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game('$help'))
    print('We have logged in as {0.user}'.format(bot))

    sheet = bot.get_cog('Sheet')
    print('updating')
    await sheet.sheet_generator()

@bot.event
async def on_command_error(ctx, error):
    print(error)
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.CommandOnCooldown):
        em = discord.Embed(title=f"Slow it down bro!",description=f"Try again in {round(error.retry_after/60)} minutes.")
        await ctx.send(embed=em)
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the permission to use this command")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Something's wrong with your arguments")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You don't have the required arguments")
    elif isinstance(error, commands.PrivateMessageOnly):
        await ctx.send("This command can only be used in private messages.")
    elif isinstance(error, commands.MissingAnyRole):
        await ctx.send("You do not have the roles required to use this command.")
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send(f'{ctx.command} has been disabled.')
    elif isinstance(error, aiohttp.ClientOSError):
        await ctx.send("A really f***ing annoying error occurred, and there's no real way to fix it, so I'm pretty upset. You can just try again and it should work.\n-Randy")
    else:
        await ctx.send(f'An error occurred:\n```{error}```')


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')


@bot.command(brief='Imma pong yo ass')
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')


@bot.command(brief='Gives you the UTC-localized timestamp in the iso format.')
async def time(ctx):
    moment = pytz.utc.localize(datetime.utcnow()).isoformat()
    temp_time = dateutil.parser.parse(moment)
    embed_time = temp_time.replace(tzinfo=pytz.UTC)
    await ctx.send(embed_time)

keep_alive.keep_alive()

@keep_alive.app.route('/sheet')
def sheet():
    return mongo.sheet_code.find_one({})['code']


bot.run(os.getenv("bot_token"))