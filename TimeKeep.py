import discord
import asyncio
import math
import random
import time
import websockets
from discord.ext import commands
from DiscordTimeKeep import SecretFile
from DiscordTimeKeep import DataManager
from DiscordTimeKeep import GameStat

description = '''An bot designed to get time'''
bot = commands.Bot(command_prefix=SecretFile.get_command_prefix(), description=description)
bot.remove_command("help")

maintenance = False
latest_clear = 0

restart = False
notice_message = ""

reap_in_progress = 0
reap_name = ""
thief_id = 0


# notice_message = "** ------ Notice ------ **\n**UPDATE** new patch released, use t!pn for more information~"
# notice_message = "** ------ Notice ------ **\n**End of Season: ** 08/31 - 11:59 P.M. PST"


def get_latest_time():
    with open("./data/playerData.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
    if len(content) == 0:
        content.append('{}'.format(time.time()))
    return content[0]


def hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return int(h), int(m), int(s)


def seconds_format(seconds):
    if seconds < 0:
        return '-{} Hours {} Minutes {} Seconds'.format(*hms(-seconds))
    else:
        return '{} Hours {} Minutes {} Seconds'.format(*hms(seconds))


async def start_timer():
    try:
        # t_interval = 0
        while True:
            # if t_interval % 30 == 0:
            #     await update_time_status()
            # if reap_in_progress != 0:
            #     break
            # await asyncio.sleep(1)
            # t_interval += 1
            await update_time_status()
            await asyncio.sleep(300)
    except websockets.exceptions.ConnectionClosed:
        await asyncio.sleep(10)
        global restart
        restart = True


async def update_time_status():
    if reap_in_progress != 0:
        return
    flowed_time = int(time.time() - latest_clear)
    time_str = "{}H {}M {}S".format(*hms(flowed_time))
    await bot.change_presence(activity=discord.Game(name='t!: ' + time_str))


@bot.event
async def on_ready():  # when ready it prints the username, id, and starts the status update
    global latest_clear
    latest_clear = float(get_latest_time())
    if latest_clear == 0:
        latest_clear = time.time()
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    # latest_clear = time.time()
    await start_timer()


@bot.command(pass_context=True)
async def start(ctx):
    embed = discord.Embed(color=0x42d7f4)
    embed.title = "Welcome~ "
    embed.description = GameStat.start_str
    await ctx.message.channel.send(embed=embed)


@bot.command(pass_context=True)
async def choose(ctx):
    await class_selection(ctx)


@bot.command(pass_context=True)
async def change(ctx):
    await class_selection(ctx)


async def class_selection(ctx):
    if reap_in_progress != 0:
        await ctx.message.channel.send("Sorry Reap is Currently In Progress\nClass Selection is Temporarily Disabled")
        return

    try:
        player_class_id = (int(ctx.message.content[9:]))
        if player_class_id > GameStat.class_name.__len__():
            raise ValueError
        if player_class_id == 8:
            msg = await ctx.message.channel.send("<@!{}> **Abyssal Voyager Warning: **\n"
                                                 "One Look into the Abyss and There Will be no Turning Back\n"
                                                 "(Class Change Will be Disabled)\n"
                                                 "**Is {} Ready to Venture Into the Abyss**"
                                                 "".format(ctx.message.author.id, str(ctx.message.author)[:-5]))
            await msg.add_reaction("✅")
            await msg.add_reaction("❎")
            return
    except (ValueError, KeyError):
        msg = "Sorry I don't understand\nUse t!choose / t!change <Class #>\n" + GameStat.char_list
        await ctx.message.channel.send(msg)
        return
    if change_player_class(ctx.message.author.id, ctx.message.author, player_class_id):
        await ctx.message.channel.send(
            "<@!{}> is now a **{}**".format(ctx.message.author.id, GameStat.class_name[player_class_id]))
    else:
        await ctx.message.channel.send("<@!{}> Sorry Abyssal Voyage is Never Ending"
                                       "\nClass Change Cancelled".format(ctx.message.author.id))


def change_player_class(author_id, author_name, player_class_id):
    players = DataManager.read_players()
    try:
        # Find the current player
        player = next(player for player in players if player.id == author_id)
        if player.class_type == 8:
            return False
        player.name = str(author_name)[:-5]
        player.class_type = player_class_id
        if player.class_type == 2:
            player.next_reap = time.time() + GameStat.reap_cooldown * (1 - GameStat.mage_reduction_rate)
        else:
            player.next_reap = time.time() + GameStat.reap_cooldown
        DataManager.write_players(players, latest_clear)
        DataManager.update_logs_class(player.name, GameStat.class_name[player_class_id], True)
    except StopIteration:
        # Player doesn't exist in our logs
        player = GameStat.Player("{}|{}|{}|{}|{}|{}"
                                 .format(author_id, str(author_name)[:-5], 0, time.time(), 0, player_class_id))
        players.append(player)
        DataManager.write_players(players, latest_clear)
        DataManager.update_logs_class(player.name, GameStat.class_name[player_class_id])
    return True


@bot.command(pass_context=True)
async def reap(ctx):
    global reap_in_progress
    player_package = await check_player(ctx)
    if player_package is None:
        return
    player = player_package[0]
    players = player_package[1]
    if reap_in_progress != 0:
        await ctx.message.channel.send("Reap is Currently In Progress \nBandits are allowed to steal with *t!steal*")
        return

    global latest_clear
    current_time = time.time()
    added_time = current_time - latest_clear
    reap_message = ""

    if player.class_type == 10:
        reward = GameStat.striker_max_reward - (current_time - player.next_reap) / 60 * GameStat.striker_reward_drop
        if reward > 1:
            reap_message += '**MOMENTUM STABLE!**\n Reap Time Increased to {}%\n' \
                .format(round(reward * 100))
            added_time *= reward
        else:
            reap_message += '**Momentum Lost**\n Reap Time Not Affected\n'
    if player.class_type == 11:
        reward = (current_time - player.next_reap) / 86400 * GameStat.capacitor_boost + 1
        reap_message += '**CAPACITOR DISCHARGE!**\n Reap Time Increased to {}%\n' \
            .format(round(reward * 100))
        added_time *= reward

    author = ctx.message.author
    player.reap_count += 1
    player.next_reap = current_time + GameStat.reap_cooldown
    player.name = str(author)[:-5]
    reap_delay = 60

    # --------------------- Unique Class Passive ------------------
    if player.class_type == 1:
        added_time *= GameStat.warrior_buff
        reap_message += '**HEROIC STRIKE ACTIVATED!**\n Reap Time Increased to {}%\n' \
            .format(GameStat.warrior_buff * 100)

    elif player.class_type == 2:
        reap_message += '**TIME WARP ACTIVATED!**\n Reap Cooldown Reduced by {}%\n' \
            .format(GameStat.mage_reduction_rate * 100)
        player.next_reap = current_time + GameStat.reap_cooldown * (1 - GameStat.mage_reduction_rate)

    elif player.class_type == 3:
        if random.random() < GameStat.hunter_crit_rate:
            added_time *= 2
            reap_message += '**HUNTER\'S MARK ACTIVATED!**\n Reap Time Increased to {}%\n' \
                .format(GameStat.hunter_crit_dmg * 100)
        else:
            reap_message += '**HUNTER\'S MARK FAILED!**\n Reap Time Gains No Modifier\n'

    elif player.class_type == 4:
        added_time += GameStat.fairy_boost * 60
        reap_message += '**WILD GROWTH ACTIVATED!**\n Reap Time Increased by {}M\n'.format(GameStat.fairy_boost)

    elif player.class_type == 6:
        reap_delay = 0
        reap_message += '**BLINDING ASSAULT ACTIVATED!**\n Instant Reap Complete\n'

    elif player.class_type == 7:
        if random.random() < GameStat.gamble_chance:
            reap_delay = 0
            added_time *= GameStat.gamble_reward
            for win in range(3):
                reap_message += '**💰!!!LUCKY COIN ACTIVATED!!!💰**\n Reap Time Increased to {}%!!!\n' \
                    .format(GameStat.gamble_reward * 100)
            # DataManager.update_logs_win(True, "GAMBLE")
        else:
            msg = '**LUCKY COIN FAILED**\n{} Minutes has Been Lost\n'.format(GameStat.gamble_cost) \
                  + roll_shell(added_time, players, author)
            player.reaped_time -= GameStat.gamble_cost * 60
            await ctx.message.channel.send(msg)
            latest_clear = current_time
            DataManager.write_players(players, latest_clear)
            # DataManager.write_players(players, current_time)
            DataManager.update_logs_win(False, "GAMBLE", str(author)[:-5], seconds_format(added_time))
            await update_time_status()
            return

    elif player.class_type == 8:
        if random.random() < GameStat.voyage_chance:
            reap_delay = 0
            added_time *= GameStat.voyage_reward
            for win in range(20):
                reap_message += '**🌌!!!ABYSSAL VOYAGE SUCCESSFUL!!!🌌**\n Reap Time Increased to {}%!!!\n' \
                    .format(GameStat.voyage_reward * 100)
            DataManager.update_logs_win(True, "VOYAGE")
        else:
            added_time *= GameStat.voyage_reduction
            reap_message += '**' + GameStat.get_voyage_msg() + '**\n Reap Time Reduced to {}%\n' \
                .format(GameStat.voyage_reduction * 100)

    elif player.class_type == 9:
        if added_time > GameStat.sniper_threshold:
            reap_message += '**COSMIC SHOT LANDED!**\n Reap Cooldown Reset\n'
            player.next_reap = current_time
        else:
            reap_message += '**Cosmic Shot Missed**\n Reap Cooldown Not Affected\n'

    DataManager.write_players(players, latest_clear)
    reap_in_progress = added_time
    global reap_name
    reap_name = player.name
    # ------------------------------- Initialize Reaping -------------------------
    reap_lockin_message = await ctx.message.channel.send("Reap Initiated, Will be Completed in 60 Seconds")
    await bot.change_presence(
        activity=discord.Game(name='⚔️Reaping: {}'.format("{}H {}M {}S".format(*hms(added_time)))))

    fun_fact = GameStat.get_fun_fact()
    while reap_delay > 0:
        if reap_in_progress != 0:
            await asyncio.sleep(5)
            reap_delay -= 5
            try:
                await reap_lockin_message.edit(
                    content="Reap Initiated, Will be Completed in {} Seconds\nFun Fact: {}"
                            "".format(reap_delay, fun_fact))
            except discord.errors.NotFound:
                reap_lockin_message = await ctx.message.channel.send(
                    "Reap Initiated, Will be Completed in {} Seconds".format(reap_delay))
        else:
            await reap_lockin_message.edit(content="<@!{}> Your Reap Has Been *STOLEN* by {}"
                                           .format(player.id, str(thief_id)[:-5]))
            return

    await reap_lockin_message.edit(content="Reap Successful")

    reap_in_progress = 0
    # --------------------- Store Data ------------------
    player.reaped_time = math.floor(player.reaped_time + added_time)
    reap_message += '<@!{}> has added **{}** to their total\n' \
                    'Adding up to be **{}**\nNext reap in **{}**\n' \
        .format(author.id, seconds_format(added_time), seconds_format(player.reaped_time),
                "{} hours and {} minutes".format(*hms(player.next_reap - current_time)))

    # --------------------- Roll Shell ------------------
    reap_message += roll_shell(added_time, players, author)

    await ctx.message.channel.send(reap_message)
    # Strip out the last five characters (the #NNNN part)
    DataManager.update_logs_reap(str(author)[:-5], seconds_format(added_time), player.class_type)
    latest_clear = current_time

    DataManager.write_players(players, latest_clear)
    print("reap by {} with {}".format(author, math.floor(added_time)))
    # await start_timer()
    await update_time_status()


def roll_shell(added_time, players, author):
    reap_message = ""
    if random.random() < GameStat.blue_shell_chance and len(players) > 3:
        # compose blue shell message
        reap_message += "\n{} BLUE SHELL ACTIVATED {}\n**{}** lost *{}*\n**{}** lost *{}*\n**{}** lost *{}*" \
            .format(GameStat.blue_shell_icon, GameStat.blue_shell_icon,
                    players[0].name, seconds_format(added_time),
                    players[1].name, seconds_format(added_time * 0.75),
                    players[2].name, seconds_format(added_time * 0.5), )
        # calculate damage
        players[0].reaped_time -= added_time
        players[1].reaped_time -= added_time * 0.75
        players[2].reaped_time -= added_time * 0.5
        DataManager.update_logs_shell(str(author)[:-5], seconds_format(added_time))
    return reap_message


@bot.command(pass_context=True)
async def steal(ctx):
    # unique thief steal command
    player_package = await check_player(ctx)
    if player_package is None:
        return
    player = player_package[0]
    players = player_package[1]

    global reap_in_progress

    if player is None:
        return
    if player.class_type != 5:
        await ctx.message.channel.send("Sorry **t!steal** is Only Allowed for the Dimensional Bandits")
        return
    if reap_in_progress == 0:
        await ctx.message.channel.send("Sorry no One is Reaping Right Now\nUse **t!reap** to do so")
        return

    global thief_id
    thief_id = ctx.message.author

    author = ctx.message.author.display_name
    current_time = time.time()
    player.reaped_time += reap_in_progress
    player.reap_count += 1
    player.next_reap = current_time + GameStat.reap_cooldown
    player.name = str(author)[:-5]
    reap_message = '<@!{}> has *STOLEN* **{}** to their total\n' \
                   'Adding up to be **{}**\nNext reap in **{}**' \
        .format(ctx.message.author.id, seconds_format(reap_in_progress), seconds_format(player.reaped_time),
                "{} hours and {} minutes".format(*hms(player.next_reap - current_time)))

    global latest_clear
    await ctx.message.channel.send(reap_message)
    # Strip out the last five characters (the #NNNN part)
    DataManager.update_logs_reap(str(author)[:-5], seconds_format(reap_in_progress), player.class_type,
                                 stolen=reap_name)
    latest_clear = current_time
    await update_time_status()
    DataManager.write_players(players, latest_clear)
    reap_in_progress = 0
    # await start_timer()


async def check_player(ctx):
    print("- Check by {} -".format(ctx.message.author.display_name))
    if maintenance:
        await ctx.message.channel.send("Sorry currently under maintenance")
        return None

    # Bot detection
    if ctx.message.author.bot:
        await ctx.message.channel.send("bot detected, command canceled")
        return None

    # find player

    author_id = ctx.message.author.id
    try:
        players = DataManager.read_players()
        player = next(player for player in players if player.id == author_id)
    except StopIteration:
        # We couldn't find the player, so create a new one and insert it into players
        await ctx.message.channel.send("Looks like you never played before~\nUse **t!start** to get started~")
        return None

    current_time = time.time()

    # check for cooldown
    if current_time < player.next_reap:
        await ctx.message.channel.send("""Sorry, actions is still on cooldown
                      please wait another **{} hours {} minutes and {} seconds**
                      """.format(*hms(player.next_reap - current_time)))
        return None

    return player, players


@bot.command(pass_context=True)
async def classes(ctx):
    await ctx.message.channel.send(" " + GameStat.char_list)


@bot.command(pass_context=True)
async def characters(ctx):
    await ctx.message.channel.send(" " + GameStat.char_list)


@bot.command(pass_context=True)
async def c(ctx):
    await ctx.message.channel.send(" " + GameStat.char_list)


@bot.command(pass_context=True)
async def info(ctx):
    if '@' in ctx.message.content:
        user_id = ctx.message.content.split('@')[1][:-1]
        if user_id[0] == '!':
            user_id = user_id[1:]
        await print_info(ctx.message.channel, user_id=int(user_id))
    elif '#' in ctx.message.content:
        user_rank = ctx.message.content.split('#')[1]
        await print_info(ctx.message.channel, user_rank=user_rank)
    else:
        await ctx.message.channel.send("Sorry I don't understand\nUse t!info @player or t!info #<rank> or t!me")
        return


@bot.command(pass_context=True)
async def me(ctx):
    user_id = ctx.message.author.id
    await print_info(ctx.message.channel, user_id=user_id)


async def print_info(channel, user_id=0, user_rank=0):
    if notice_message != "":
        # await channel.send(notice_message)
        await channel.send(notice_message)

    players = DataManager.read_players()
    player = None
    index = 0
    if user_id != 0:
        try:
            # Find the current player
            index, player = next((index, player) for index, player in enumerate(players) if player.id == user_id)
        except StopIteration:
            # Player doesn't exist in our logs, so tell them to reap
            await channel.send("""<@!{}> has stored 0 seconds
                                use t!reap to get started""".format(user_id))
            return
    elif user_rank != 0:
        user_rank = int(user_rank)
        try:
            # Find the current player
            index, player = next((index, player) for index, player in enumerate(players) if index + 1 == user_rank)
        except StopIteration:
            # Player doesn't exist in our logs, so tell them to reap
            await channel.send("""<@!{}> has stored 0 seconds
                                use t!reap to get started""".format(user_id))
            return

    current_time = float(time.time())
    if current_time < player.next_reap:
        next_reap = seconds_format(player.next_reap - current_time)
    else:
        if player.class_type == 11:
            next_reap = "Your next reap is available ({}%)".format(
                round((current_time - player.next_reap) / 864 * GameStat.capacitor_boost) + 100)
        else:
            next_reap = 'Your next reap is available'

    average_reap = seconds_format(0 if (player.reap_count == 0) else player.reaped_time / player.reap_count)
    # in case of div by zero
    embed = discord.Embed(color=0xfc795c)
    embed.add_field(name="Stats of *{}*".format(player.name), value="""
    **Class:** {}
    **Rank:** {}
    **Stored Time:** {}
    **Average Reap:** {}
    **Reap Count:** {}
    **Next Reap:** {}
    """.format(GameStat.class_name[player.class_type], index + 1,
               seconds_format(player.reaped_time), average_reap,
               int(player.reap_count), next_reap))
    await channel.send(embed=embed)


@bot.command(pass_context=True)
async def log(ctx):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
    log_string = ''.join(content[:20])
    embed = discord.Embed(color=0x42d7f4)
    embed.title = "Reap Log"
    embed.description = log_string
    await ctx.message.channel.send(embed=embed)


@bot.command(pass_context=True)
async def pn(ctx):
    msg = await ctx.message.channel.send(embed=generate_patch_embed(1))
    await msg.add_reaction("⬅")
    await msg.add_reaction("➡")


def generate_patch_embed(start_point):
    with open("./data/patchNotes.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
    record = False
    log_string = ""
    content = content[(start_point - 1) * GameStat.log_size:]
    if len(content) == 0:
        return None
    for index, line in enumerate(content):
        if line.startswith("**"):
            if record and index > GameStat.log_size:
                break
            else:
                record = True

        if record:
            log_string += line

    embed = discord.Embed(color=0x644fdd)
    embed.title = "Patch Notes"
    embed.description = log_string
    embed.set_footer(text="Patch Notes Page: {}".format(start_point))
    return embed


@bot.command(pass_context=True)
async def ping(ctx):
    t = await ctx.message.channel.send('Pong!')
    ms = 0
    try:
        ms = (t.created_at - ctx.message.created_at).total_seconds() * 1000
        await t.edit(content='Pong! Took: {}ms'.format(int(ms)))
    except discord.ext.commands.errors.CommandInvokeError:
        await ctx.message.channel.send('(Missing Message Editing Permission) Took: {}ms'.format(int(ms)))


@bot.command(pass_context=True)
async def help(ctx):
    await ctx.message.channel.send(GameStat.help_str)


@bot.command(pass_context=True)
async def leaderboard(ctx):
    if len(ctx.message.content) == 13:
        await print_leaderboard(ctx.message.channel)
    else:
        await print_season_leaderboard(ctx.message.channel, ctx.message.content)


@bot.command(pass_context=True)
async def b(ctx):
    if len(ctx.message.content) == 3:
        await print_leaderboard(ctx.message.channel)
    else:
        await print_season_leaderboard(ctx.message.channel, ctx.message.content)


async def print_season_leaderboard(channel, msg):
    try:
        target_season = int(msg.split()[1])
        if target_season > GameStat.current_season:
            raise ValueError()
    except ValueError:
        await channel.send("Sorry I don't Understand")
        return

    if notice_message != "":
        await channel.send(notice_message)

    embed = generate_leaderboard_embed(1, target_season)
    msg = await channel.send(embed=embed)
    await msg.add_reaction("⬅")
    await msg.add_reaction("➡")


async def print_leaderboard(channel):
    if notice_message != "":
        await channel.send(notice_message)

    embed = generate_leaderboard_embed(1)
    msg = await channel.send(embed=embed)
    await msg.add_reaction("⬅")
    await msg.add_reaction("➡")


def generate_leaderboard_embed(start_rank, season=GameStat.current_season):
    players = DataManager.read_players(season)[start_rank - 1: start_rank + 9]
    if len(players) == 0:
        return None
    embed = discord.Embed(color=0x42d7f4)

    # determine title
    if season == GameStat.current_season:
        if start_rank == 1:
            embed.title = "The Current Top {} Are!!!".format(len(players))
        else:
            embed.title = "The {} to {} Place are:".format(start_rank, start_rank + len(players) - 1)
        embed.set_footer(text="Rank: {} - {}".format(start_rank, start_rank + len(players) - 1))
    else:
        if start_rank == 1:
            embed.title = "The Season {}: Top {} Are!".format(season, len(players))
        else:
            embed.title = "The Season {}: {} to {} Place are:".format(season, start_rank, start_rank + len(players) - 1)
        embed.set_footer(text="Season {} Rank: {} - {}".format(season, start_rank, start_rank + len(players) - 1))

    # cycle through players
    for index, player in enumerate(players):
        # Drop the number at the end of the author's name (#NNNN)
        player_title = player.name

        # sets the icons if it's current_season
        if season >= 4:  # the season where classes are introduced
            if player.id in GameStat.reward_icons.keys():
                player_title += " " + GameStat.reward_icons[player.id]

            player_class_type = GameStat.class_name_short[player.class_type]
            embed.add_field(name='*#{}* {}: {}'.format(index + start_rank, player_class_type, player_title),
                            value=seconds_format(player.reaped_time))
        else:
            embed.add_field(name='*#{}* {}'.format(index + start_rank, player_title),
                            value=seconds_format(player.reaped_time))
    return embed


@bot.command(pass_context=True)
async def invite(ctx):
    embed = discord.Embed(color=0x42d7f4)
    embed.description = \
        "[Invite me~]" \
        "(https://discordapp.com/api/oauth2/authorize?client_id=538078061682229258&permissions=14336&scope=bot)"
    await ctx.message.channel.send(embed=embed)


@bot.event
async def on_reaction_add(reaction, user):
    if user.name != bot.user.name:
        if reaction.message.author.name == bot.user.name:
            if reaction.message.content.startswith("<@!"):  # this should be a player
                if str(reaction.emoji) == "✅":
                    if reaction.message.content[3:21] == str(user.id):
                        change_player_class(int(reaction.message.content[3:21]), (reaction.message.content[148:-34] + "#1234")
                                            .strip(), 8)
                        await reaction.message.channel.send(
                            "<@!{}> is now a **{}**".format(reaction.message.content[3:21],
                                                            GameStat.class_name[8]))
                else:
                    await reaction.message.channel.send("Class Change Cancelled")
                await reaction.message.delete()
            else:  # this should be a leaderboard or patch note msg
                await reaction.remove(user)
                embed = None
                footer = reaction.message.embeds[0].footer.text

                if footer.startswith('Rank'):  # process for current leaderboard
                    index = int(footer.split()[1])

                    if str(reaction.emoji) == "➡":
                        embed = generate_leaderboard_embed(index + 10)
                    elif str(reaction.emoji) == "⬅":
                        if index - 10 < 1:
                            return
                        embed = generate_leaderboard_embed(index - 10)
                    if embed is not None:
                        await reaction.message.edit(embed=embed)
                elif footer.startswith('Season'):
                    index = int(footer.split()[3])
                    season = int(footer.split()[1])
                    if str(reaction.emoji) == "➡":
                        embed = generate_leaderboard_embed(index + 10, season)
                    elif str(reaction.emoji) == "⬅":
                        if index - 10 < 1:
                            return
                        embed = generate_leaderboard_embed(index - 10, season)
                    if embed is not None:
                        await reaction.message.edit(embed=embed)
                elif footer.startswith('Patch Notes'):  # process for patch notes
                    index = int(footer.split()[3])
                    if str(reaction.emoji) == "➡":
                        embed = generate_patch_embed(index + 1)
                    elif str(reaction.emoji) == "⬅":
                        if int(footer.split()[3]) - 1 < 1:
                            return
                        embed = generate_patch_embed(index - + 1)
                    if embed is not None:
                        await reaction.message.edit(embed=embed)


@bot.command(pass_context=True)
async def status(ctx):
    await send_status(ctx.message.channel)


@bot.event
async def on_message(message):
    if '538078061682229258' in message.content:
        await send_status(message.channel)
    await bot.process_commands(message)


async def send_status(channel):
    await channel.send('Currently stored {}\n'
                       'across {} servers'
                       .format(seconds_format(math.floor(time.time() - latest_clear)), len(bot.guilds)))


def run_client(client, *args, **kwargs):
    loop = asyncio.get_event_loop()
    while True:
        try:
            loop.run_until_complete(client.start(*args, **kwargs))
        except Exception as e:
            print("Error", e)  # or use proper logging
        print("Waiting until restart")
        time.sleep(600)


while True:
    try:
        print('-------------------starting-------------------')
        bot.run(SecretFile.get_token())  # are you happy now Soap????
    except ConnectionResetError:
        print('-------------------c_error-------------------')
        time.sleep(600)
    except TimeoutError:
        print('-------------------t_error-------------------')
        time.sleep(600)
