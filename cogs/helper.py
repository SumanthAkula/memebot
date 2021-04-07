from discord import Embed
from discord.ext import commands

from main import cf_util, bot_ctrl
from util.config_options import ConfigOption


class Helper(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def help(self, ctx, arg=""):
        if ctx.author == self.client.user:
            return
        if arg == "setconfig":
            await ctx.send(embed=await self.show_setconfig_help(ctx))
        else:
            await ctx.send(embed=await self.show_help_message(ctx))

    @staticmethod
    async def show_setconfig_help(ctx) -> Embed:
        admin = await bot_ctrl.is_admin_or_higher(ctx)
        if admin:
            color = 0xFA64CA
        else:
            color = 0xDC1414
        if not admin:
            embed = Embed(title="You must be an admin to view these commands!", color=color)
            embed.set_author(name="Kek Cringe Tracker")
            return embed
        embed = Embed(title="setconfig options", color=color)
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
                        value="set to `true` to have the bot respond 'pong' to any message that is the word 'ping'",
                        inline=False)
        embed.add_field(name="send_noot_noot",
                        value="set to `true` to have the bot respond 'noot' to any message that is the word 'noot'")
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
    async def show_help_message(ctx) -> Embed:
        embed = Embed(title="Commands", color=0xFA64CA)
        embed.set_author(name="Kek Cringe Tracker")
        embed.add_field(name="`help`", value="shows this message", inline=True)
        embed.add_field(name="`getstats [@user (optional)]` (alias: `gs`)",
                        value="gets the number of kek, cringe, and cursed memes sent by whoever ran the command or "
                              "whoever was tagged in the command",
                        inline=False)
        embed.add_field(name="`leaderboard [sort (optional)]` (alias: `lb`)",
                        value="Shows the leaderboard for everyone's Meme Review stats.  By default the stats will be "
                              "sorted by the kek/cringe ratio of each person.  The possible sorts are `kek`, "
                              "`cringe`, `cursed`, `total`, or `ratio`.  If no valid sort is specified, the leaderboard"
                              " will be sorted by `ratio`.",
                        inline=False)
        if await bot_ctrl.is_dev(ctx):
            # DEVELOPER COMMANDS
            embed.add_field(name="`preload`",
                            value="looks through the past 100 messages and adds any new meme reviews to the database\n"
                                  "**Note: this command takes a while to run, and spamming it could break the bot!**",
                            inline=False)
        if await bot_ctrl.is_admin_or_higher(ctx):
            # ADMIN COMMANDS
            embed.add_field(name="`setconfig [parameter]` (alias: `sc`)",
                            value="run the `help setconfig` command for more info. its "
                                  "too much info to put here lol",
                            inline=False)
            embed.add_field(name="`listinsults` (alias: `lsins`)",
                            value="Lists all of the possible insults that could be sent when someone sends a message "
                                  "containing the phrase 'is abdur gay?'",
                            inline=False)
            embed.add_field(name="`addinsult` [insult] (alias: `addins`)",
                            value="Adds the specified insult to the list of insults that could be sent when someone "
                                  "sends "
                                  "a message containing the phrase 'is abdur gay?'",
                            inline=False)
            embed.add_field(name="`removeinsult [insult ID]` (alias: `rmins`)",
                            value="Removes the specified insult from the list of insults that could be sent when "
                                  "someone "
                                  "sends a message containing the phrase 'is abdur gay?'  It's a good idea to run the "
                                  "`listinsults` command first to see what each insult's ID number is",
                            inline=False)
            embed.add_field(name="`blockeddomains` (alias: `lsbd`)",
                            value="Displays the list of domains that can't be sent in the meme review channel",
                            inline=False)
            embed.add_field(name="`blockdomain [domain]` (alias: `bd`)",
                            value="Adds the specified domain to the list of list of domains that can't be sent in the "
                                  "meme review channel",
                            inline=False)
            embed.add_field(name="`unblockdomain [domain ID]` (alias: `ubd`)",
                            value="Removes the specified domain from the list of domains that can't be sent in the "
                                  "meme review channel.  It's a good idea to run the `blockeddomains` command first to "
                                  "see what each domain's ID number is",
                            inline=False)
        if ctx.guild.get_role(cf_util.get_param(ConfigOption.meme_reviewer_role)) in ctx.author.roles:
            # MEME REVIEWER COMMANDS
            embed.add_field(name="`rating [add/subtract] [amount (optional)] [kek/cringe/cursed] [@user]`",
                            value="modifies the stats of the user mentioned.  Run the command without any arguments "
                                  "to see an example of how to user it. ",
                            inline=False)
        return embed


def setup(client):
    client.add_cog(Helper(client))
