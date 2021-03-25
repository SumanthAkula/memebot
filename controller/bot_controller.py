import random
import discord
from util.config_util import CFUtil
from util.config_options import ConfigOption
from util.db_util import DBUtil
from operator import itemgetter


class BotController:
    def __init__(self, client: discord.Client, db_util: DBUtil, cf_util: CFUtil):
        self.db_util = db_util
        self.cf_util = cf_util
        self.client = client

    async def setconfig(self, ctx, param, value: str = None):
        if param == "none":
            await ctx.send(embed=self.show_setconfig_help())
            return
        elif value is None:
            val = self.cf_util.get_param(param)
            if param == ConfigOption.prefix.name:
                val = chr(val)
            elif param == ConfigOption.meme_reviewer_role.name or param == ConfigOption.admin_role.name:
                role = ctx.guild.get_role(val)
                if role is None:
                    val = "NULL"
                else:
                    val = role.mention
            elif param == ConfigOption.meme_review_channel.name:
                channel = ctx.guild.get_channel(val)
                if channel is None:
                    val = "NULL"
                else:
                    val = channel.mention
            await ctx.send(f"The value of {param} is {val}")
            return
        elif param == ConfigOption.meme_reviewer_role.name or param == ConfigOption.admin_role.name:
            if len(ctx.message.role_mentions) == 0:
                await ctx.send(f"You gotta tag the role you want to set as the {param}")
                return
            value = ctx.message.role_mentions[0]
            self.cf_util.set_param(param, value)
            await ctx.send(f"Set {param} to {value.mention}")
            return
        elif param == ConfigOption.meme_review_channel.name:
            if len(ctx.message.channel_mentions) == 0:
                await ctx.send("You gotta tag the channel you want to set as the meme review channel")
                return
            value = ctx.message.channel_mentions[0]
            self.cf_util.set_param(param, value)
            await ctx.send(f"Set {param} to {value.mention}")
        else:
            self.cf_util.set_param(param, value)
            await ctx.send(f"Set {param} to {value}")

    async def get_rating(self, message: discord.Message):
        if message.reference is not None:
            orig: discord.Message = await message.channel.fetch_message(message.reference.message_id)
            self.db_util.add_meme_to_reviewed(orig.id)
            if message.content.find(":abdurkek:") != -1:
                self.db_util.add_rating(orig.author.id, 'kek')
            elif message.content.find(":abdurcringe:") != -1:
                self.db_util.add_rating(orig.author.id, 'cringe')
            elif message.content.find(":cursed:") != -1:
                self.db_util.add_rating(orig.author.id, 'cursed')

    async def set_rating(self, target: discord.User, operation: str, amount: int, category: str):
        if operation.lower() == "add" or operation.lower() == "subtract":
            self.db_util.set_stat(target.id, operation, amount, category)

    async def send_canned_responses(self, message: discord.Message):
        if self.cf_util.get_param("send_ayy_lmao") == 1:
            if message.content.lower().find("ayy") != -1:
                await message.channel.send("lmao")
        if self.cf_util.get_param("send_ping_pong") == 1:
            if message.content.lower() == "ping":
                await message.channel.send("pong")
        if self.cf_util.get_param("bully_abdur") == 1:
            if message.content.lower().find("is abdur gay") != -1:
                insults = self.db_util.get_insults()
                if len(insults) == 0:
                    await message.channel.send("The list of insults is empty! Add an insult before running this again")
                else:
                    await message.channel.send(random.choice(insults)[1])

    async def delete_blocked_domains(self, message: discord.Message):
        if self.cf_util.get_param("enforce_domain_blacklist"):
            for _rowid, domain in self.db_util.get_banned_domains():
                if message.content.find(domain) != -1:
                    await message.channel.send(f"That message links to a domain that is blocked ({domain}), "
                                               f"so your message has been")
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

    # ----------------------------------------------- Big embeds go here -----------------------------------------------
    @staticmethod
    def show_setconfig_help() -> discord.Embed:
        embed = discord.Embed(title="setconfig options", color=0xFA64CA)
        embed.set_author(name="Kek Cringe Tracker")
        embed.add_field(name="`prefix [new prefix]`",
                        value="sets the new prefix (AKA the little symbol you type before running commands) for this "
                              "bot.  If no new prefix is provided, the bot will tell you the current command prefix "
                              "and nothing will be changed",
                        inline=False)
        embed.add_field(name="`bully_abdur [true/false]`",
                        value="set to `true` to have the bot send messages telling abdur he's gay whenever someone "
                              "types 'is abdur gay?'  set to `false` if you don't want to hurt abdur's feelings",
                        inline=False)
        embed.add_field(name="`send_ayy_lmao [true/false]`",
                        value="set to `true` to have the bot respond 'lmao' to any message containing the word 'ayy'",
                        inline=False)
        embed.add_field(name="`send_ping_pong [true/false]`",
                        value="set to `true` to have the bot respond 'pong' to any message containing the word 'ping'",
                        inline=False)
        embed.add_field(name="`enforce_domain_blacklist [domain]`",
                        value="set to `true` to have the bot auto-delete messages containing a banned URL",
                        inline=False)
        embed.add_field(name="`meme_reviewer_role [@mention role]`",
                        value="@mention the role you want to designate as the meme reviewer's role.  Only people with"
                              "this role will be able to register meme ratings with this bot and modify users' meme "
                              "ratings",
                        inline=False)
        embed.add_field(name="`meme_review_channel [#mention channel]`",
                        value="#mention the channel you want to designate as the meme review channel.  Keks, Cringes, "
                              "and Curseds will only be tracked in this channel.  This is also the only channel that "
                              "the domain blocking feature will work in.  If no channel is set as the meme review "
                              "channel, the no meme reviews in any channel will be tracked, and the domain blocking "
                              "will be nonfunctional",
                        inline=False)
        return embed

    @staticmethod
    def show_help_message() -> discord.Embed:
        embed = discord.Embed(title="Commands", color=0xFA64CA)
        embed.set_author(name="Kek Cringe Tracker")
        embed.add_field(name="`help`", value="shows this message", inline=True)
        embed.add_field(name="`preload`",
                        value="looks through the past 100 messages and adds any new meme reviews to the database\n"
                              "**Note: this command takes a while to run, and spamming it could break the bot!**",
                        inline=False)
        embed.add_field(name="`getstats [@user (optional)]` (alias: `gs`)",
                        value="gets the number of kek, cringe, and cursed memes sent by whoever ran the command or "
                              "whoever was tagged in the command",
                        inline=False)
        embed.add_field(name="`setconfig [parameter]` (alias: `sc`)",
                        value="run the `help setconfig` command for more info. its "
                              "too much info to put here lol",
                        inline=False)
        embed.add_field(name="`rating [add/subtract] [amount (optional)] [kek/cringe/cursed] [@user]`",
                        value="modifies the stats of the user mentioned.  Run the command without any arguments to see"
                              "an example of how to user it.  If no `amount` value is passed in, it defaults to 1",
                        inline=False)
        embed.add_field(name="`leaderboard [sort (optional)]` (alias: `lb`)",
                        value="Shows the leaderboard for everyone's Meme Review stats.  By default the stats will be "
                              "sorted by the kek/cringe ratio of each person.  The possible sorts are `kek`, "
                              "`cringe`, `cursed`, or `ratio`.  If no valid sort is specified, the leaderboard will "
                              "be sorted by `ratio`.",
                        inline=False)
        embed.add_field(name="`listinsults` (alias: `lsins`)",
                        value="Lists all of the possible insults that could be sent when someone sends a message "
                              "containing the phrase 'is abdur gay?'",
                        inline=False)
        embed.add_field(name="`addinsult` [insult] (alias: `addins`)",
                        value="Adds the specified insult to the list of insults that could be sent when someone sends "
                              "a message containing the phrase 'is abdur gay?'",
                        inline=False)
        embed.add_field(name="`removeinsult [insult ID]` (alias: `rmins`)",
                        value="Removes the specified insult from the list of insults that could be sent when someone "
                              "sends a message containing the phrase 'is abdur gay?'  It's a good idea to run the "
                              "`listinsults` command first to see what each insult's ID number is",
                        inline=False)
        embed.add_field(name="`blockeddomains` (alias: `lsbd`)",
                        value="Displays the list of domains that can't be sent in the meme review channel",
                        inline=False)
        embed.add_field(name="`blockdomain [domain]` (alias: `bd`)",
                        value="Adds the specified tomain to the list of list of domains that can't be sent in the "
                              "meme review channel",
                        inline=False)
        embed.add_field(name="`unblockdomain [domain ID]` (alias: `ubd`)",
                        value="Removes the specidied domain from the list of domains that can't be sent in the "
                              "meme review channel.  It's a good idea to run the `blockeddomains` command first to "
                              "see what each domain's ID number is",
                        inline=False)
        return embed

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
        sort = sort.lower()
        if sort == 'kek':
            sort_index = 1
        elif sort == 'cringe':
            sort_index = 2
        elif sort == 'cursed':
            sort_index = 3
        else:
            sort = 'ratio'
            sort_index = 4  # if no valid sort type is passed in, default to sort by ratio
        all_data = sorted(all_data, key=itemgetter(sort_index), reverse=True)
        value = f"**Meme Review Leaderboard (sorted by {sort})**\n"
        value += "```python\n"
        for uid, kek, cringe, cursed, ratio in all_data:
            user = await ctx.guild.fetch_member(uid)
            value += f"{user.display_name: <32} Kek: {kek: <4} Cringe: {cringe: <4} Cursed: {cursed: <4}" \
                     f" Ratio: {ratio:.2f}\n"
        value += "```"
        return value
