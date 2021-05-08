from discord.ext import commands

from main import bot_ctrl


class Responder(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["lsresp"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def listresponses(self, ctx):
        await ctx.send(embed=await bot_ctrl.list_responses_embed())

    @commands.command(aliases=["addresp"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def addresponse(self, ctx, *, insult: str = ""):
        if insult == "":
            await ctx.send("You gotta specify the response you want to add, fool")
            return
        await bot_ctrl.add_response_to_db(insult)
        await ctx.send(f"successfully added \"{insult}\" to the list of responses")

    @commands.command(aliases=["rmresp"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def removeresponse(self, ctx, resp_id: str = None):
        if resp_id is None:
            await ctx.send("You gotta pass in the ID of the insult! Run the `listresponses` "
                           "command to get a list of IDs")
            return
        try:
            id_num: int = int(resp_id)
        except ValueError:
            await ctx.send("You gotta type a number for for the response ID")
            return
        await bot_ctrl.remove_response_from_db(id_num)


def setup(client):
    client.add_cog(Responder(client))
