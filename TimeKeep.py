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
bot = commands.Bot(command_prefix='t!', description=description)
bot.remove_command("help")

maintenance = False
latest_clear = 0

restart = False
notice_message = ""

reap_in_progress = 0
thief_id = 0

# notice_message = "** ------ Notice ------ **\nSeason Ending (delayed) May 12th 11:59 P.M.\nClass Systems Coming~"


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
            await asyncio.sleep(30)
    except websockets.exceptions.ConnectionClosed:
        await asyncio.sleep(10)
        global restart
        restart = True


async def update_time_status():
    if reap_in_progress != 0:
        return
    flowed_time = int(time.time() - latest_clear)
    time_str = "{}H {}M {}S".format(*hms(flowed_time))
    await bot.change_presence(game=discord.Game(name='t!: ' + time_str))


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


@bot.command()
async def start():
    embed = discord.Embed(color=0x42d7f4)
    embed.title = "Welcome~ "
    embed.description = GameStat.start_str
    # embed.set_image(url="https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{}.jpg".format(my_champ[0]))
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def choose(ctx):
    players = DataManager.read_players()
    try:
        # Find the current player
        next(player for player in players if player.id == ctx.message.author.id)
        await bot.say("Sorry you have already chosen your class \n"
                      "However class change is a available with **t!change <class #>**")
        return
    except StopIteration:
        # Player doesn't exist in our logs, so tell them to reap
        try:
            player_class_id = (int(ctx.message.content[9:]))
            await bot.say("<@!{}> is now a **{}**".format(ctx.message.author.id,
                                                          GameStat.class_name[player_class_id]))
        except ValueError:
            msg = "Sorry I don't understand\nUse t!choose <Class #>\n" + GameStat.char_list
            await bot.say(msg)
            return

        author = ctx.message.author
        player = GameStat.Player("{}|{}|{}|{}|{}|{}".format(author.id, author, 0, 0, 0, player_class_id))
        players.append(player)
        DataManager.write_players(players, latest_clear)
        DataManager.update_logs_class(str(player.name)[:-5], GameStat.class_name[player_class_id])


@bot.command(pass_context=True)
async def change(ctx):
    # if await check_player(ctx) is None:
    #    return
    players = DataManager.read_players()
    try:
        # Find the current player
        player = next(player for player in players if player.id == ctx.message.author.id)
        try:
            player_class_id = (int(ctx.message.content[9:]))
            await bot.say("<@!{}> is now a **{}**".format(ctx.message.author.id,
                                                          GameStat.class_name[player_class_id]))
        except ValueError:
            msg = "Sorry I don't understand\nUse t!change <Class #>\n" + GameStat.char_list
            await bot.say(msg)
            return

        player.name = ctx.message.author
        player.class_type = player_class_id
        if player.class_type == 2:
            player.next_reap = time.time() + GameStat.reap_cooldown * (1 - GameStat.mage_reduction_rate)
        else:
            player.next_reap = time.time() + GameStat.reap_cooldown
        DataManager.write_players(players, latest_clear)
        DataManager.update_logs_class(str(player.name)[:-5], GameStat.class_name[player_class_id], True)
    except StopIteration:
        # Player doesn't exist in our logs, so tell them to reap
        await bot.say("Sorry But You Haven't Been Assigned a Class Yet \nUse **t!start** to get started")
        return


@bot.command(pass_context=True)
async def reap(ctx):
    global reap_in_progress
    player_package = await check_player(ctx)
    if player_package is None:
        return
    player = player_package[0]
    players = player_package[1]
    if reap_in_progress != 0:
        await bot.say("Reap is Currently In Progress \nBandits are allowed to steal with *t!steal*")
        return

    global latest_clear
    current_time = time.time()
    added_time = current_time - latest_clear
    reap_message = ""

    author = ctx.message.author
    player.reap_count += 1
    player.next_reap = current_time + GameStat.reap_cooldown
    player.name = str(author)
    reap_delay = 60

    # --------------------- Unique Class Passive ------------------
    if player.class_type == 1:
        added_time *= GameStat.warrior_buff
        reap_message += '**HEROIC STRIKE ACTIVATED!**\n Reap Time Increased to {}%\n'\
            .format(GameStat.warrior_buff * 100)

    elif player.class_type == 2:
        reap_message += '**TIME WARP ACTIVATED!**\n Reap Cooldown Reduced by {}%\n'\
            .format(GameStat.mage_reduction_rate * 100)
        player.next_reap = current_time + GameStat.reap_cooldown * (1 - GameStat.mage_reduction_rate)

    elif player.class_type == 3:
        if random.random() < GameStat.hunter_crit_rate:
            added_time *= 2
            reap_message += '**HUNTER\'S MARK ACTIVATED!**\n Reap Time Increased to {}%\n'\
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
            reap_message += '**💰!!!LUCKY COIN ACTIVATED!!!💰**\n Reap Time Increased to {}%!!!\n'\
                .format(GameStat.gamble_reward * 100)
        else:
            await bot.say('**LUCKY COIN FAILED**\n Nothing happened\n')
            DataManager.write_players(players, latest_clear)
            return

    DataManager.write_players(players, latest_clear)

    # ------------------------------- Initialize Reaping -------------------------
    reap_in_progress = added_time
    reap_lockin_message = await bot.say("Reap Initiated, Will be Completed in 60 Seconds")
    await bot.change_presence(game=discord.Game(name='⚔️Reaping: {}'.format("{}H {}M {}S".format(*hms(added_time)))))
    while reap_delay > 0:
        if reap_in_progress != 0:
            await asyncio.sleep(1)
            reap_delay -= 1
            await bot.edit_message(reap_lockin_message, "Reap Initiated, Will be Completed in {} Seconds"
                                                        "".format(reap_delay))
        else:
            await bot.edit_message(reap_lockin_message, "<@!{}> Your Reap Has Been *STOLEN* by {}"
                                   .format(player.id, str(thief_id)[:-5]))
            return

    await bot.edit_message(reap_lockin_message, "Reap Successful")

    reap_in_progress = 0

    # --------------------- Store Data ------------------
    player.reaped_time = math.floor(player.reaped_time + added_time)
    reap_message += '<@!{}> has added **{}** to their total\n' \
                    'Adding up to be **{}**\nNext reap in **{}**'\
        .format(author.id, seconds_format(added_time), seconds_format(player.reaped_time),
                "{} hours and {} minutes".format(*hms(player.next_reap - current_time)))
    await bot.say(reap_message)
    # Strip out the last five characters (the #NNNN part)
    DataManager.update_logs_reap(str(author)[:-5], seconds_format(added_time), player.class_type)
    latest_clear = current_time

    DataManager.write_players(players, latest_clear)
    print("reap by {} with {}".format(author, math.floor(added_time)))
    # await start_timer()
    await update_time_status()


@bot.command(pass_context=True)
async def steal(ctx):
    player_package = await check_player(ctx)
    if player_package is None:
        return
    player = player_package[0]
    players = player_package[1]

    global reap_in_progress
    if player is None:
        return
    if player.class_type != 5:
        await bot.say("Sorry **t!steal** is Only Allowed for the Dimensional Bandits")
        return
    if reap_in_progress == 0:
        await bot.say("Sorry no One is Reaping Right Now\nUse **t!reap** to do so")
        return

    global thief_id
    thief_id = ctx.message.author

    author = ctx.message.author
    current_time = time.time()
    player.reaped_time += reap_in_progress
    player.reap_count += 1
    player.next_reap = current_time + GameStat.reap_cooldown
    player.name = str(author)
    reap_message = '<@!{}> has *STOLEN* **{}** to their total\n' \
                   'Adding up to be **{}**\nNext reap in **{}**' \
        .format(author.id, seconds_format(reap_in_progress), seconds_format(player.reaped_time),
                "{} hours and {} minutes".format(*hms(player.next_reap - current_time)))

    global latest_clear
    await bot.say(reap_message)
    # Strip out the last five characters (the #NNNN part)
    DataManager.update_logs_reap(str(author)[:-5], seconds_format(reap_in_progress), player.class_type, stolen=True)
    reap_in_progress = 0
    latest_clear = current_time
    await update_time_status()
    DataManager.write_players(players, latest_clear)
    # await start_timer()


async def check_player(ctx):
    print("- Check by {} -".format(ctx.message.author))
    if maintenance:
        await bot.say("Sorry currently under maintenance")
        return None

    # Bot detection
    if ctx.message.author.bot:
        await bot.say("bot detected, command canceled")
        return None

    # find player

    author_id = ctx.message.author.id
    try:
        players = DataManager.read_players()
        player = next(player for player in players if player.id == author_id)
    except StopIteration:
        # We couldn't find the player, so create a new one and insert it into players
        await bot.say("Looks like you never played before~\nUse **t!start** to get started~")
        return None

    current_time = time.time()

    # check for cooldown
    if current_time < player.next_reap:
        await bot.say("""Sorry, actions is still on cooldown
                      please wait another **{} hours {} minutes and {} seconds**
                      """.format(*hms(player.next_reap - current_time)))
        return None

    return player, players


@bot.command(pass_context=True)
async def info(ctx):
    if '@' not in ctx.message.content:
        await bot.say("Sorry I don't understand\nUse t!info @player or t!me")
        return
    user_id = ctx.message.content.split('@')[1][:-1]
    if user_id[0] == '!':
        user_id = user_id[1:]
    await print_info(ctx.message.channel, user_id)


@bot.command(pass_context=True)
async def me(ctx):
    author_id = ctx.message.author.id
    await print_info(ctx.message.channel, author_id)


async def print_info(channel, author_id):
    if notice_message != "":
        await bot.send_message(channel, notice_message)

    players = DataManager.read_players()
    try:
        # Find the current player
        index, player = next((index, player) for index, player in enumerate(players) if player.id == author_id)
    except StopIteration:
        # Player doesn't exist in our logs, so tell them to reap
        await bot.send_message(channel, """<@!{}> has stored 0 seconds
                            use t!reap to get started""".format(author_id))
        return

    current_time = float(time.time())
    if current_time < player.next_reap:
        next_reap = seconds_format(player.next_reap - current_time)
    else:
        next_reap = 'Your next reap is up'

    average_reap = seconds_format(0 if (player.reap_count == 0) else player.reaped_time / player.reap_count)
    # in case of div by zero
    await bot.send_message(channel, "Stats of <@!{}>\n"
                                    "```"
                                    "Class: {}\n"
                                    "Rank: {}\nStored Time: {}\nAverage Reap: {}\n"
                                    "Reap Count: {}\nNext Reap: {}\n"
                                    "```"
                           .format(author_id, GameStat.class_name[player.class_type], index + 1,
                                   seconds_format(player.reaped_time), average_reap,
                                   int(player.reap_count), next_reap))


@bot.command()
async def log():
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
    log_string = ''.join(content)
    embed = discord.Embed(color=0x42d7f4)
    embed.title = "Reap Log"
    embed.description = log_string
    await bot.say(embed=embed)


@bot.command()
async def pn():
    with open("./data/patchNotes.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
    log_string = ''.join(content)
    embed = discord.Embed(color=0x644fdd)
    embed.title = "Patch Notes"
    embed.description = log_string
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def ping(ctx):
    t = await bot.say('Pong!')
    ms = (t.timestamp - ctx.message.timestamp).total_seconds() * 1000
    await bot.edit_message(t, new_content='Pong! Took: {}ms'.format(int(ms)))


@bot.command()
async def help():
    await bot.say(GameStat.help_str)


@bot.command(pass_context=True)
async def leaderboard(ctx):
    await print_leaderboard(ctx.message.channel)


@bot.command(pass_context=True)
async def b(ctx):
    await print_leaderboard(ctx.message.channel)


async def print_leaderboard(channel):
    if notice_message != "":
        await bot.send_message(channel, notice_message)

    players = DataManager.read_players()[:10]
    embed = discord.Embed(color=0x42d7f4)
    embed.title = "The current top {} are:".format(len(players))
    for index, player in enumerate(players):
        # Drop the number at the end of the author's name (#NNNN)
        player_title = player.name[:-5]
        for i, ranked_player in enumerate(GameStat.teir_list):
            if ranked_player == player.name:
                player_title += " " + GameStat.rank_icon[i]
        player_class_type = GameStat.class_name_short[player.class_type]
        embed.add_field(name='#{} {}: {}'.format(index + 1, player_class_type, player_title),
                        value=seconds_format(player.reaped_time))
    await bot.send_message(channel, embed=embed)


@bot.command()
async def invite():
    embed = discord.Embed(color=0x42d7f4)
    embed.description = \
        "[Invite me~]" \
        "(https://discordapp.com/api/oauth2/authorize?client_id=538078061682229258&permissions=14336&scope=bot)"
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def status(ctx):
    await send_status(ctx.message.channel)


@bot.event
async def on_message(message):
    if '538078061682229258' in message.content:
        await send_status(message.channel)
    await bot.process_commands(message)


async def send_status(channel):
    await bot.send_message(channel, 'Currently stored {}\n'
                                    'across {} servers'
                           .format(seconds_format(math.floor(time.time() - latest_clear)), len(bot.servers)))


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
        bot.run(SecretFile.get_token())  # are you happy now Soap????
    except ConnectionResetError:
        print('-------------------error-------------------')
        time.sleep(10)
