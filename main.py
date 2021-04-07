import os
import sqlite3

import discord
from discord.ext import commands

import secret
from controller.bot_controller import BotController
from util import Constants
from util.config_options import ConfigOption
from util.config_util import CFUtil
from util.db_util import DBUtil

db_util = DBUtil(Constants.DB_FILE_NAME,
                 Constants.RATINGS_TABLE_NAME,
                 Constants.RATED_MEME_IDS_NAME,
                 Constants.CONFIG_OPTIONS_TABLE_NAME,
                 Constants.INSULTS_TABLE_NAME,
                 Constants.BANNED_DOMAINS_TABLE_NAME)
db_util.create_tables()
cf_util = CFUtil(db_util)


def determine_prefix(_client, _message):
    try:
        return chr(cf_util.get_param(ConfigOption.prefix))
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


@client.command(aliases=["sc"])
@commands.check(bot_ctrl.is_admin_or_higher)
async def setconfig(ctx: discord.ext.commands.Context, param="none", value=None):
    param = param.lower()
    await bot_ctrl.setconfig(ctx, param, value)


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
