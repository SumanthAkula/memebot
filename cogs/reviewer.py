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
        channel: discord.TextChannel = self.client.get_channel(payload.channel_id)
        if channel.id != cf_util.get_param(ConfigOption.meme_review_channel):
            return
        message: discord.Message = await channel.fetch_message(payload.message_id)
        # the event was a reaction clear event since RawReactionClearEvent has no event_type attribute
        if db_util.meme_already_reviewed(message.id):
            print("already reviewed!")
            await message.reply("Reactions cleared! The original rating still stands. **Clearing reactions from a "
                                "meme in this channel can prevent the this bot from tracking them properly!**")
        else:
            print("not reviewed, not doing anything")

    async def __reaction_rating(self, payload):
        channel: discord.TextChannel = self.client.get_channel(payload.channel_id)
        if channel.id != cf_util.get_param(ConfigOption.meme_review_channel):
            return
        reviewer_role = channel.guild.get_role(cf_util.get_param(ConfigOption.meme_reviewer_role))
        reactor_roles = channel.guild.get_member(payload.user_id).roles
        if reviewer_role not in reactor_roles:
            return
        message: discord.Message = await channel.fetch_message(payload.message_id)
        valid_emoji = ["abdurkek", "abdurcringe", "cursed"]
        if payload.emoji.name not in valid_emoji:
            return
        if payload.event_type == "REACTION_ADD":
            db_util.add_meme_to_reviewed(message.id)
            await bot_ctrl.modify_rating(message.author, "add", 1, payload.emoji.name.replace("abdur", ""))
            await message.reply(payload.emoji)
        elif payload.event_type == "REACTION_REMOVE":
            db_util.remove_meme_from_reviewed(message.id)
            await bot_ctrl.modify_rating(message.author, "subtract", 1, payload.emoji.name.replace("abdur", ""))
            """
            delete a message if and only if:
                * the message was sent by the bot
                * the message is a reply to a meme
                * the meme rating reaction was removed
            """
            async for msg in channel.history(limit=100):
                if msg.author == self.client.user and msg.reference is not None:
                    if message.id == msg.reference.message_id:
                        if msg.content == str(payload.emoji):
                            await msg.delete()

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
        start_t = time.time()
        tmp = await ctx.send("Hold on a few seconds it gotta load rq...")
        await ctx.send(await bot_ctrl.get_leaderboard(ctx, sort))
        await tmp.delete()
        print(time.time() - start_t)

    # ----------------------------------------- COMMAND TO GET LAST RATED MEME -----------------------------------------
    @commands.command(aliases=["lm"])
    async def lastmeme(self, ctx):
        meme: discord.Message = await ctx.channel.fetch_message(db_util.get_last_rated_meme())
        await meme.reply("Last reviewed meme is this one", mention_author=False)

    # ---------------------------------------------------- PRELOAD -----------------------------------------------------
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
