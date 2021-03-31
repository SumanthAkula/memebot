import time

import discord
from discord.ext import commands

from main import cf_util, bot_ctrl, db_util
from util.config_options import ConfigOption


class Reviewer(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if cf_util.get_param('meme_review_channel') == message.channel.id:
            if message.guild.get_role(cf_util.get_param('meme_reviewer_role')) in message.author.roles:
                await bot_ctrl.get_rating(message)

    @commands.command()
    @commands.has_role(cf_util.get_param(ConfigOption.meme_reviewer_role.name))
    async def rating(self, ctx: discord.ext.commands.Context,
                     operation: str,
                     amount: int,
                     rating_type: str,
                     user: discord.Member):
        operation = operation.lower()
        rating_type = rating_type.lower()
        if operation is None or not (operation == "add" or operation == "subtract"):
            await ctx.send("You gotta specify an operation (either `add` or `subtract`)")
            return
        possible_ratings = ['kek', 'cringe', 'cursed']
        if rating_type is None or (rating_type in possible_ratings) is not True:
            await ctx.send(
                "You gotta specify which rating you want to modify (either `kek`, `cringe`, or `cursed`)")
            return
        await bot_ctrl.set_rating(user, operation, amount, rating_type)
        await ctx.send(f"successfully updated the {rating_type} stat for {user.display_name}")

    @commands.command(aliases=["gs"])
    async def getstats(self, ctx: discord.ext.commands.Context, user: discord.Member = None):
        if user is not None:
            await ctx.send(embed=bot_ctrl.get_user_stats(user))
        else:
            await ctx.send(embed=bot_ctrl.get_user_stats(ctx.author))

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx, sort: str = 'r'):
        await ctx.send(await bot_ctrl.get_leaderboard(ctx, sort))

    @commands.command()
    @commands.check(bot_ctrl.is_dev)
    async def preload(self, ctx: discord.ext.commands.Context):
        mr_channel_id = cf_util.get_param(ConfigOption.meme_review_channel.name)
        if ctx.message.channel.id != mr_channel_id:
            await ctx.send(
                f"This command can only be run in the {ctx.guild.get_channel(mr_channel_id).mention} channel")
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


def setup(client):
    client.add_cog(Reviewer(client))
