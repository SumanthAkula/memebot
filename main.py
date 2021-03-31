import secret
import discord
from discord.ext import commands

from cogs.command_error import is_admin_or_higher
from util.config_util import CFUtil
from util.db_util import DBUtil
from util import Constants
from controller.bot_controller import BotController

import os
import sqlite3

db_util = DBUtil('main.sqlite',
                 Constants.RATINGS_TABLE_NAME,
                 Constants.RATED_MEME_IDS_NAME,
                 Constants.CONFIG_OPTIONS_TABLE_NAME,
                 Constants.INSULTS_TABLE_NAME,
                 Constants.BANNED_DOMAINS_TABLE_NAME)
db_util.create_tables()
cf_util = CFUtil(db_util)


def determine_prefix(_client, _message):
    try:
        return chr(cf_util.get_param('prefix'))
    except sqlite3.OperationalError:
        return '>'


intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=determine_prefix, intents=intents)
client.remove_command('help')
bot_ctrl = BotController(client, db_util, cf_util)

for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        client.load_extension(f"cogs.{file[:-3]}")

print("starting now")


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game("with chronos' scrotum"))
    print("Bot is ready")


@client.command()
async def help(ctx, arg=""):
    if ctx.author == client.user:
        return
    if arg == "setconfig":
        await ctx.send(embed=bot_ctrl.show_setconfig_help())
    else:
        await ctx.send(embed=bot_ctrl.show_help_message())


@client.command(aliases=["sc"])
@commands.check(is_admin_or_higher)
async def setconfig(ctx: discord.ext.commands.Context, param="none", value=None):
    param = param.lower()
    await bot_ctrl.setconfig(ctx, param, value)


@client.command(aliases=["lb"])
async def leaderboard(ctx, sort: str = 'r'):
    await ctx.send(await bot_ctrl.get_leaderboard(ctx, sort))


@client.command(aliases=["lsins"])
@commands.check(is_admin_or_higher)
async def listinsults(ctx):
    await ctx.send(embed=await bot_ctrl.list_insults_embed())


@client.command(aliases=["addins"])
@commands.check(is_admin_or_higher)
async def addinsult(ctx, *, insult: str = ""):
    if insult == "":
        await ctx.send("You gotta specify the insult you want to add, fool")
        return
    await bot_ctrl.add_insult_to_db(insult)
    await ctx.send(f"successfully added \"{insult}\" to the list of insults to bully Abdur with")


@client.command(aliases=["rmins"])
@commands.check(is_admin_or_higher)
async def removeinsult(ctx, insult_id: str = None):
    if insult_id is None:
        await ctx.send("You gotta pass in the ID of the insult! Run the `listinsults` command to get a list of IDs")
        return
    try:
        id_num: int = int(insult_id)
    except ValueError:
        await ctx.send("You gotta type a number for for the insult ID")
        return
    await bot_ctrl.remove_insult_from_db(id_num)


@client.command(aliases=["lsbd"])
@commands.check(is_admin_or_higher)
async def blockeddomains(ctx):
    await ctx.send(embed=await bot_ctrl.list_banned_domains())


@client.command(aliases=["bd"])
@commands.check(is_admin_or_higher)
async def blockdomain(ctx, domain: str = None):
    if domain == "":
        await ctx.send("You gotta specify the domain you want to block, fool")
        return
    await bot_ctrl.add_domain_to_blacklist(domain)
    await ctx.send(f"successfully added \"{domain}\" to the list of domains that can't be sent")


@client.command(aliases=["ubd"])
@commands.check(is_admin_or_higher)
async def unblockdomain(ctx, domain_id: str = None):
    if domain_id is None:
        await ctx.send("You gotta pass in the ID of the domain! Run the `blocked` command to get a list of IDs")
        return
    try:
        id_num: int = int(domain_id)
    except ValueError:
        await ctx.send("You gotta type a number for for the domain ID")
        return
    await bot_ctrl.remove_domain_from_blacklist(ctx, id_num)


@client.event
async def on_message(message: discord.Message):
    if client.user in message.mentions:
        prefix = determine_prefix(client, message)
        await message.channel.send(
            f"The command prefix for this bot is '{prefix}'\nRun `{prefix}help` to see all of the commands available.")
    if message.author == client.user:
        return
    await bot_ctrl.send_canned_responses(message)
    await client.process_commands(message)


client.run(secret.TOKEN)
