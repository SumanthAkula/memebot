import random
from operator import itemgetter

import discord

from util.config_options import ConfigOption
from util.config_util import CFUtil
from util.db_util import DBUtil


class BotController:
    def __init__(self, client: discord.Client, db_util: DBUtil, config_util: CFUtil):
        self.db_util = db_util
        self.cf_util = config_util
        self.client = client

    async def setconfig(self, ctx, param=None, value: str = None):
        option = None
        if param == "none":
            await ctx.send("You gotta pass in a parameter!")
            return
        for opt in ConfigOption:
            if param == opt.name:
                option = opt
        if option is None:
            raise ValueError("That is not a valid configuration option!")
        if value is None:
            val = self.cf_util.get_param(option)
            if option == ConfigOption.prefix:
                val = chr(val)
            elif option == ConfigOption.meme_reviewer_role or param == ConfigOption.admin_role:
                role = ctx.guild.get_role(val)
                if role is None:
                    val = "NULL"
                else:
                    val = role.mention
            elif option == ConfigOption.meme_review_channel:
                channel = ctx.guild.get_channel(val)
                if channel is None:
                    val = "NULL"
                else:
                    val = channel.mention
            await ctx.send(f"The value of {option.name} is {val}")
            return
        elif option == ConfigOption.meme_reviewer_role or option == ConfigOption.admin_role:
            if len(ctx.message.role_mentions) == 0:
                await ctx.send(f"You gotta tag the role you want to set as the {option.name}")
                return
            value = ctx.message.role_mentions[0]
            self.cf_util.set_param(option, value)
            await ctx.send(f"Set {option.name} to {value.mention}")
            return
        elif option == ConfigOption.meme_review_channel:
            if len(ctx.message.channel_mentions) == 0:
                await ctx.send("You gotta tag the channel you want to set as the meme review channel")
                return
            value = ctx.message.channel_mentions[0]
            self.cf_util.set_param(option, value)
            await ctx.send(f"Set {option.name} to {value.mention}")
        else:
            self.cf_util.set_param(option, value)
            await ctx.send(f"Set {option.name} to {value}")

    async def get_rating(self, message: discord.Message):
        if message.reference is not None:
            orig: discord.Message = await message.channel.fetch_message(message.reference.message_id)
            if message.content.find(":abdurkek:") != -1:
                category = "kek"
            elif message.content.find(":abdurcringe:") != -1:
                category = "cringe"
            elif message.content.find(":cursed:") != -1:
                category = "cursed"
            else:
                return
            await self.modify_rating(orig.author, "add", 1, category)
            self.db_util.add_meme_to_reviewed(orig.id)

    async def modify_rating(self, target: discord.Member, operation: str, amount: int, category: str,
                            message_id: int = None):
        operation = operation.lower()
        if operation == "add" or operation == "subtract":
            self.db_util.set_stat(target.id, operation, abs(amount), category)
        if message_id is not None:
            self.db_util.add_meme_to_reviewed(message_id)

    async def send_canned_responses(self, message: discord.Message):
        if self.cf_util.get_param(ConfigOption.send_ayy_lmao) == 1:
            if message.content.lower().find("ayy") != -1:
                await message.channel.send("lmao")
        if self.cf_util.get_param(ConfigOption.send_ping_pong) == 1:
            if message.content.lower() == "ping":
                await message.channel.send("pong")
        if self.cf_util.get_param(ConfigOption.send_noot_noot) == 1:
            if message.content.lower() == "noot":
                await message.channel.send("noot")
        if self.cf_util.get_param(ConfigOption.bully_abdur) == 1:
            if message.content.lower().find("is abdur gay") != -1:
                insults = self.db_util.get_insults()
                if len(insults) == 0:
                    await message.channel.send("The list of responses is empty! "
                                               "Add a response before running this again")
                else:
                    await message.channel.send(random.choice(insults)[1])

    async def delete_blocked_domains(self, message: discord.Message):
        if self.cf_util.get_param(ConfigOption.enforce_domain_blacklist):
            for _rowid, domain in self.db_util.get_banned_domains():
                if message.content.find(domain) != -1:
                    await message.channel.send(f"{message.author.mention}, That message links to a domain that "
                                               f"is blocked ({domain}), so your message has been removed")
                    await message.delete()

    # code to process insults
    async def list_insults_embed(self) -> discord.Embed:
        row = self.db_util.get_insults()
        description = "The number is the ID of the insult\n" \
                      "Run the `deleteinsult [ID]` command to delete an insult from this list\n" \
                      "Run the `addinsult [insult]` command to add an insult to this list"
        embed = discord.Embed(
            title="Possible replies to \"is abdur gay?\"", description=description)
        for obj in row:
            embed.add_field(name=f"{obj[0]}.", value=str(obj[1]), inline=False)
        return embed

    async def add_insult_to_db(self, insult: str):
        self.db_util.add_insult(insult)

    async def remove_insult_from_db(self, insult_id: int):
        self.db_util.remove_insult(insult_id)

    # code to process domain blacklist
    async def list_banned_domains(self) -> discord.Embed:
        row = self.db_util.get_banned_domains()
        description = "The number is the ID of the domain\n" \
                      "Run the `unblockdomain [ID]` command to delete a domain from this list\n" \
                      "Run the `blockdomain [domain]` command to add a domain to this list"
        embed = discord.Embed(title="Blocked domains", description=description)
        for obj in row:
            embed.add_field(name=f"{obj[0]}.", value=str(obj[1]), inline=False)
        return embed

    async def add_domain_to_blacklist(self, domain: str):
        self.db_util.add_domain_to_blacklist(domain)

    async def remove_domain_from_blacklist(self, ctx, domain_id: int):
        for rowid, domain in self.db_util.get_banned_domains():
            if rowid == domain_id:
                self.db_util.remove_domain_from_blacklist(domain_id)
                await ctx.send(f"{domain} unblocked successfully")
                return
        await ctx.send("There is no domain with that ID")

    def get_user_stats(self, user: discord.Member) -> discord.Embed:
        data = self.db_util.get_user_data(user.id)
        if data is None:
            ndembed = discord.Embed(
                title=f"No data found for {user.display_name}!", color=0xDC1414)
            return ndembed
        total_memes = data[1] + data[2] + data[3]
        ratio: str = f"{data[1] / (1 if data[2] == 0 else data[2]):.2f}"
        embed = discord.Embed(title="Meme Review Stats", color=0x73FF00)
        embed.add_field(name="Kek memes", value=str(data[1]), inline=True)
        embed.add_field(name="Cringe memes", value=str(data[2]), inline=True)
        embed.add_field(name="Cursed memes", value=str(data[3]), inline=True)
        embed.add_field(name="Total memes", value=total_memes, inline=True)
        embed.add_field(name="Kek/Cringe Ratio",
                        value=ratio, inline=True)
        embed.add_field(name="User", value=user.display_name, inline=True)
        return embed

    async def get_leaderboard(self, ctx, sort: str = None):
        all_data = self.db_util.get_all_user_data()
        if len(all_data) == 0:
            value = "There is no meme review data, so a leaderboard cannot be created!"
            return value
        all_data = [list(data)+[data[1] / (1 if data[2] == 0 else data[2])]
                    for data in all_data]
        all_data = [list(data)+[data[1] + data[2] + data[3]]
                    for data in all_data]
        sort = sort.lower()
        if sort == 'kek':
            sort_index = 1
        elif sort == 'cringe':
            sort_index = 2
        elif sort == 'cursed':
            sort_index = 3
        elif sort == 'total':
            sort_index = 5
        else:
            sort = 'ratio'
            sort_index = 4  # if no valid sort type is passed in, default to sort by ratio
        all_data = sorted(all_data, key=itemgetter(sort_index), reverse=True)
        value = f"**Meme Review Leaderboard (sorted by {sort})**\n"
        value += "```python\n"
        for uid, kek, cringe, cursed, ratio, total in all_data:
            user = await ctx.guild.fetch_member(uid)
            value += f"{user.display_name: <32} Kek: {kek: <4} Cringe: {cringe: <4} Cursed: {cursed: <4}" \
                     f" Ratio: {ratio: <7.2f} Total: {total}\n"
        value += "```"
        return value

    @staticmethod
    async def is_dev(ctx) -> bool:
        return ctx.author.id == 177812127363497984

    async def is_admin_or_higher(self, ctx) -> bool:
        if await self.is_dev(ctx):
            return True
        admin_role = ctx.guild.get_role(
            self.cf_util.get_param(ConfigOption.admin_role))
        for role in ctx.author.roles:
            if role.position >= admin_role.position:
                return True
        return False
