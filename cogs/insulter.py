from discord.ext import commands

from main import bot_ctrl


class Insulter(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["lsins"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def listinsults(self, ctx):
        await ctx.send(embed=await bot_ctrl.list_insults_embed())

    @commands.command(aliases=["addins"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def addinsult(self, ctx, *, insult: str = ""):
        if insult == "":
            await ctx.send("You gotta specify the insult you want to add, fool")
            return
        await bot_ctrl.add_insult_to_db(insult)
        await ctx.send(f"successfully added \"{insult}\" to the list of insults to bully Abdur with")

    @commands.command(aliases=["rmins"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def removeinsult(self, ctx, insult_id: str = None):
        if insult_id is None:
            await ctx.send("You gotta pass in the ID of the insult! Run the `listinsults` command to get a list of IDs")
            return
        try:
            id_num: int = int(insult_id)
        except ValueError:
            await ctx.send("You gotta type a number for for the insult ID")
            return
        await bot_ctrl.remove_insult_from_db(id_num)


def setup(client):
    client.add_cog(Insulter(client))
