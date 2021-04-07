from discord.ext import commands

from main import bot_ctrl, cf_util
from util.config_options import ConfigOption


class DomainBlocker(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if cf_util.get_param(ConfigOption.meme_review_channel) == message.channel.id:
            await bot_ctrl.delete_blocked_domains(message)

    @commands.command(aliases=["lsbd"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def blockeddomains(self, ctx):
        await ctx.send(embed=await bot_ctrl.list_banned_domains())

    @commands.command(aliases=["bd"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def blockdomain(self, ctx, domain: str = None):
        if domain == "":
            await ctx.send("You gotta specify the domain you want to block, fool")
            return
        await bot_ctrl.add_domain_to_blacklist(domain)
        await ctx.send(f"successfully added \"{domain}\" to the list of domains that can't be sent")

    @commands.command(aliases=["ubd"])
    @commands.check(bot_ctrl.is_admin_or_higher)
    async def unblockdomain(self, ctx, domain_id: str = None):
        if domain_id is None:
            await ctx.send("You gotta pass in the ID of the domain! Run the `blocked` command to get a list of IDs")
            return
        try:
            id_num: int = int(domain_id)
        except ValueError:
            await ctx.send("You gotta type a number for for the domain ID")
            return
        await bot_ctrl.remove_domain_from_blacklist(ctx, id_num)


def setup(client):
    client.add_cog(DomainBlocker(client))
