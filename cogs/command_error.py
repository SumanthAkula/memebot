from discord.ext import commands

from main import cf_util
from util.config_options import ConfigOption


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


class CommandErrorChecker(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRole):
            await ctx.send(f"You need the '{ctx.guild.get_role(error.missing_role).name}' role to run that command!")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send(f"That's not a valid command.  Run the `help` command for a list of valid commands")
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(error.original)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"You did not run this command with the correct number of arguments! Run `help` to see which "
                f"arguments this command requires")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(f"You do not have the right permissions to run the `{ctx.command.name}` command")
        else:
            await ctx.send(str(error))
            raise error


def setup(client):
    client.add_cog(CommandErrorChecker(client))
