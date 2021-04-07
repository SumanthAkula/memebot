import time

import discord
from discord.ext import commands

from main import cf_util, bot_ctrl, db_util
from util.config_options import ConfigOption


class Reviewer(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    # -------------------------------------- LISTENERS TO ADD/REMOVE MEME REVIEWS --------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message):
        if cf_util.get_param(ConfigOption.meme_review_channel) == message.channel.id:
            if message.guild.get_role(cf_util.get_param(ConfigOption.meme_reviewer_role)) in message.author.roles:
                await bot_ctrl.get_rating(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.__reaction_rating(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.__reaction_rating(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_clear(self, payload: discord.RawReactionClearEvent):
        print(payload)

    async def __reaction_rating(self, payload):
        channel: discord.TextChannel = self.client.get_channel(payload.channel_id)
        if channel.id != cf_util.get_param(ConfigOption.meme_review_channel):
            return
        valid_emoji = ["abdurkek", "abdurcringe", "cursed"]
        if payload.emoji.name not in valid_emoji:
            return
        message: discord.Message = await channel.fetch_message(payload.message_id)
        if payload.event_type == "REACTION_ADD":
            await bot_ctrl.modify_rating(message.author, "add", 1, payload.emoji.name.replace("abdur", ""))
            await message.reply(payload.emoji)
        elif payload.event_type == "REACTION_REMOVE":
            await bot_ctrl.modify_rating(message.author, "subtract", 1, payload.emoji.name.replace("abdur", ""))

    # ----------------------------------------- COMMANDS TO MODIFY USER STATS ------------------------------------------
    @commands.group(invoke_without_command=True)
    @commands.has_role(cf_util.get_param(ConfigOption.meme_reviewer_role))
    async def rating(self, ctx):
        await ctx.send("Example usage for this command: \n"
                       "`rating add 1 kek @user`\n"
                       "`rating remove 3 cringe @user`")

    @rating.command(name="add")
    async def add_rating(self, ctx, amount: int, rating_type: str, user: discord.Member):
        await self.__modify_rating(ctx, "add", amount, rating_type, user)

    @rating.command(name="subtract", aliases=["remove", "rm", "sub"])
    async def remove_rating(self, ctx, amount: int, rating_type: str, user: discord.Member):
        await self.__modify_rating(ctx, "subtract", amount, rating_type, user)

    @staticmethod
    async def __modify_rating(ctx, operation: str, amount: int, rating_type: str, user: discord.Member):
        possible_ratings = ['kek', 'cringe', 'cursed']
        if rating_type is None or (rating_type in possible_ratings) is not True:
            await ctx.send(
                "You gotta specify which rating you want to modify (either `kek`, `cringe`, or `cursed`)")
            return
        await bot_ctrl.modify_rating(user, operation, amount, rating_type)
        await ctx.send(f"successfully updated the {rating_type} stat for {user.display_name}")

    # ---------------------------------------- COMMAND TO GET MEME REVIEW STATS ----------------------------------------
    @commands.command(aliases=["gs"])
    async def getstats(self, ctx: discord.ext.commands.Context, user: discord.Member = None):
        if user is not None:
            await ctx.send(embed=bot_ctrl.get_user_stats(user))
        else:
            await ctx.send(embed=bot_ctrl.get_user_stats(ctx.author))

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx, sort: str = 'r'):
        await ctx.send(await bot_ctrl.get_leaderboard(ctx, sort))

    # --------------------------------------- PRELOAD CODE DON'T MESS WITH THIS! ---------------------------------------
    @commands.command()
    @commands.check(bot_ctrl.is_dev)
    async def preload(self, ctx: discord.ext.commands.Context):
        mr_channel_id = cf_util.get_param(ConfigOption.meme_review_channel)
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
