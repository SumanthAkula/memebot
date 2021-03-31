from discord.ext import commands


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
        raise error


def setup(client):
    client.add_cog(CommandErrorChecker(client))
