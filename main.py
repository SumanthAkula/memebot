import discord
from discord.ext import commands
import secret
from util.config_util import CFUtil
from util.config_options import ConfigOption
from util.db_util import DBUtil
from util import Constants
from controller.bot_controller import BotController
import time
import sqlite3

db_util = DBUtil('main.sqlite',
                 Constants.RATINGS_TABLE_NAME,
                 Constants.RATED_MEME_IDS_NAME,
                 Constants.CONFIG_OPTIONS_TABLE_NAME,
                 Constants.INSULTS_TABLE_NAME,
                 Constants.BANNED_DOMAINS_TABLE_NAME)
cf_util = CFUtil(db_util)
db_util.create_tables()


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


print("starting now")


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game("with chronos' scrotum"))
    print("bot's ready")


# command permission checking functions
async def is_dev(ctx) -> bool:
    return ctx.author.id == 177812127363497984


async def is_admin_or_higher(ctx) -> bool:
    if await is_dev(ctx):
        return True
    admin_role = ctx.guild.get_role(
        cf_util.get_param(ConfigOption.admin_role.name))
    for role in ctx.author.roles:
        if role.position >= admin_role.position:
            return True
    return False


@client.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    print(f"User {ctx.message.author.display_name} tried to run command `{ctx.command.name}`")
    if isinstance(error, commands.MissingRole):
        await ctx.send(f"You need the '{ctx.guild.get_role(error.missing_role).name}' role to run that command!")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"That's not a valid command.  Run the `help` command for a list of valid commands")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(error.original)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"You did not run this command with the correct number of arguments! Run `help` to see which "
                       f"arguments this command requires")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(f"You do not have the right permissions to run the `{ctx.command.name}` command")
    else:
        await ctx.send(str(error))
        raise error


@client.command()
@commands.check(is_dev)
async def preload(ctx: discord.ext.commands.Context):
    mr_channel_id = cf_util.get_param(ConfigOption.meme_review_channel.name)
    if ctx.message.channel.id != mr_channel_id:
        await ctx.send(f"This command can only be run in the {ctx.guild.get_channel(mr_channel_id).mention} channel")
        return
    start_t = time.time()
    messages = await ctx.channel.history(limit=100).flatten()
    ratings_added = 0
    for m in messages:
        if m.reference is not None:
            orig_message: discord.Message = await m.channel.fetch_message(m.reference.message_id)
            orig_id = orig_message.id
            if db_util.meme_already_reviewed(orig_id):
                continue
            await bot_ctrl.get_rating(m)
            ratings_added += 1
    await ctx.send(f"preload completed: preloaded {ratings_added} new meme ratings\n"
                   f"Preload took {time.time() - start_t} seconds.")


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


@client.command(aliases=["gs"])
async def getstats(ctx):
    if len(ctx.message.mentions) != 0:
        await ctx.send(embed=bot_ctrl.get_user_stats(ctx.message.mentions[0]))
    else:
        await ctx.send(embed=bot_ctrl.get_user_stats(ctx.author))


@client.command(aliases=["lb"])
async def leaderboard(ctx, sort: str = 'r'):
    await ctx.send(await bot_ctrl.get_leaderboard(ctx, sort))


@client.command()
@commands.has_role(cf_util.get_param(ConfigOption.meme_reviewer_role.name))
async def rating(ctx, operation=None, arg2="1", arg3=None):
    if operation is None and arg3 is None:
        await ctx.send("Example usage:\n"
                       "`rating add 2 kek @username` will add 2 kek ratings to whoever was tagged\n"
                       "`rating subtract cringe @username` will subtract 1 cringe rating from whoever was tagged")
        return
    operation = operation.lower()
    if operation is None or not (operation == "add" or operation == "subtract"):
        await ctx.send("You gotta specify an operation (either `add` or `subtract`) first")
        return
    try:  # in this case arg2 is "amount" and arg3 is "category"
        amt = int(arg2)
    except (ValueError, TypeError):  # in this case arg2 is "category" and arg3 was None
        amt = 1
        arg3 = arg2.lower()  # category is transfered to arg3
    possible_ratings = ['kek', 'cringe', 'cursed']
    if arg3 is None or (arg3 in possible_ratings) is not True:
        await ctx.send("You gotta specify which rating you want to modify (either `kek`, `cringe`, or `cursed`) second")
        return
    if len(ctx.message.mentions) == 0:
        await ctx.send("You gotta tag the user you want to change the stats for last")
        return
    await bot_ctrl.set_rating(ctx.message.mentions[0], operation, amt, arg3)
    await ctx.send(f"successfully updated the {arg3} stat for {ctx.message.mentions[0].display_name}")


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
    if cf_util.get_param('meme_review_channel') == message.channel.id:
        await bot_ctrl.delete_blocked_domains(message)
        if message.guild.get_role(cf_util.get_param('meme_reviewer_role')) in message.author.roles:
            await bot_ctrl.get_rating(message)
    await client.process_commands(message)


client.run(secret.TOKEN)
