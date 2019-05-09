import discord
import asyncio
import math
import pathlib
import random
import time
import websockets
from discord.ext import commands
from DiscordTimeKeep import SecretFile

description = '''An bot designed to get time'''
bot = commands.Bot(command_prefix='t!', description=description)
bot.remove_command("help")


latest_clear = 0
CD = 43200
restart = False
multiplier = 1
notice_message = "** ------ Notice ------ **\nSeason Ending (delayed) May 12th 11:59 P.M.\nClass Systems Coming~"
crit_chance = 6

teir_list = ['Howyu#7873','Tropic Mango#6755', 'Soap#3672', 'ExcaliburSux#7162', 'Ajisoo#9487', 'LuxuFate#8990']
rank_icon = ['<:Challenger_Rank:559574999149838377>', '<:Diamond_Rank:559575017885532194>',
             '<:Plat_Rank:559575046516113423>', '<:Gold_Rank:559575070670848001>',
             '<:Silver_Rank:559575087955836938>', '<:Broze_Rank:559575105634566144>']


class Player:
    def __init__(self, representation):
        representation = str(representation).split("|")
        self.id = representation[0]
        self.name = representation[1]
        self.reaped_time = float(representation[2])
        self.next_reap = float(representation[3])
        self.reap_count = float(representation[4])

    def __str__(self):
        return "{}|{}|{}|{}|{}".format(self.id, self.name, self.reaped_time, self.next_reap, self.reap_count)


def read_players():
    # beginning is reserved for last_reap timer, and the last one is an empty new line
    return list(map(Player, pathlib.Path("./data/playerData.txt").read_text(encoding='utf-8').split("\n")[1:]))


def write_players(players):
    with open("./data/playerData.txt", "w", encoding='utf-8') as f:
        f.writelines(str(latest_clear) + "\n" +
                     "\n".join(map(str, sorted(players, key=lambda player: player.reaped_time, reverse=True))))


def get_latest_time():
    with open("./data/playerData.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
    return content[0]


def hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return int(h), int(m), int(s)


def seconds_format(seconds):
    return '{} Hours {} Minutes {} Seconds'.format(*hms(seconds))


async def start_timer():
    try:
        while True:
            await update_time_status()
            await asyncio.sleep(30)
    except websockets.exceptions.ConnectionClosed:
        await asyncio.sleep(10)
        global restart
        restart = True


async def update_time_status():
    flowed_time = int(time.time() - latest_clear)
    time_str = "{}H {}M {}S".format(*hms(flowed_time))
    await bot.change_presence(game=discord.Game(name='t!: ' + time_str))


@bot.event
async def on_ready():  # when ready it prints the username, id, and starts the status update
    global latest_clear
    latest_clear = float(get_latest_time())
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
    embed.description = ("""Thank you for playing REAPER
                         in this game I store every single second for you to reap
                         the amount of time I stored is set as my status
                         using <t!reap> you will take all the stored time as your own
                         it will take 12 hours for you to recharge your reap
                         feel free to @mention me to get the stored time
                         compete with others to become the TOP REAPER! Good Luck""")
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def reap(ctx):
    if False:
        await bot.say("Sorry currently under maintenance")
    else:
        if ctx.message.author.bot:
            await bot.say("bot detected, reap canceled")
            return

        global multiplier
        multiplier = 1
        # calculating crit
        if random.randint(0, 9) < crit_chance:
            multiplier = 2

        global latest_clear
        author_id = ctx.message.author.id
        author = ctx.message.author
        current_time = float(time.time())
        added_time = current_time - latest_clear

        added_time = added_time * multiplier

        players = read_players()
        try:
            # Find the current player
            player = next(player for player in players if player.id == author_id)
        except StopIteration:
            # We couldn't find the player, so create a new one and insert it into players
            # This is kind of ugly, but Python doesn't have overloading...
            player = Player("{}|{}|{}|{}|{}".format(author_id, author, 0, 0, 0))
            players.append(player)

        if current_time < player.next_reap:
            await bot.say("""Sorry, reaping is still on cooldown
                          please wait another {} hours {} minutes and {} seconds
                          """.format(*hms(player.next_reap - current_time)))
        else:
            player.reaped_time = math.floor(player.reaped_time + added_time)
            player.reap_count += 1
            player.next_reap = current_time + CD

            if multiplier != 1:
                await bot.say('**REAP BONUS ACTIVATED!**\n reap time x{}'.format(multiplier))

            await bot.say('<@!{}> has added {} to their total\n'
                          'Adding up to be {}'.format(author_id, seconds_format(added_time),
                                                      seconds_format(player.reaped_time)))
            # Strip out the last five characters (the #NNNN part)
            update_logs(str(author)[:-5], seconds_format(added_time), multiplier)
            latest_clear = current_time
            await update_time_status()

        write_players(players)
        print("reap attempt by {} with {}".format(author, math.floor(added_time)))
        # time.sleep(10)
        # await bot.say("REWIND~ Just kidding~ \ndid you really think I'll let you crit for that much :heart:")


def update_logs(author, added_time, multiplier):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
    if multiplier == 1:
        info = '{} reaped for {}\n'.format(author, added_time)
    else:
        info = '{} CRIT x{} for {}\n'.format(author, multiplier, added_time)
    content = [info] + content
    if len(content) > 10:
        content.pop()
    with open("./data/reapLog.txt", "w", encoding='utf-8') as f:
        f.writelines(content)


@bot.command(pass_context=True)
async def info(ctx):
    if '@' not in ctx.message.content:
        await bot.say("Sorry I don't understand")
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

    players = read_players()
    try:
        # Find the current player
        index, player = next((index, player) for index, player in enumerate(players) if player.id == author_id)
    except StopIteration:
        # Player doesn't exist in our logs, so tell them to reap
        await bot.send_message(channel, """<@!{}> has stored 0 seconds
                            use t!reap to get started""".format(author_id))
        index = len(players)
        return

    current_time = float(time.time())
    if current_time < player.next_reap:
        next_reap = seconds_format(player.next_reap - current_time)
    else:
        next_reap = 'Your next reap is up'

    await bot.send_message(channel, "Stats of <@!{}>\n"
                                    "```Rank: {}\nStored Time: {}\nAverage Reap: {}\n"
                                    "Reap Count: {}\nNext Reap: {}\n"
                                    "```"
                                    .format(author_id, index + 1,
                                            seconds_format(player.reaped_time),
                                            seconds_format(player.reaped_time / player.reap_count),
                                            int(player.reap_count),
                                            next_reap))


@bot.command(pass_context=True)
async def log(ctx):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()
    log_string = '\n'.join(content)
    embed = discord.Embed(color=0x42d7f4)
    embed.title = "Reap Log"
    embed.description = log_string
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def ping(ctx):
    t = await bot.say('Pong!')
    ms = (t.timestamp - ctx.message.timestamp).total_seconds() * 1000
    await bot.edit_message(t, new_content='Pong! Took: {}ms'.format(int(ms)))


# @bot.command(pass_context=True)
# async def dev(ctx):
#     if not str(ctx.message.author.id) == '297971074518351872':
#         await bot.say("Sorry~ this one's only for mango")
#         return
#     global latest_clear
#     latest_clear -= 60
#     await bot.say("Dev detected: {}".format("storing extra 60 seconds"))


@bot.command()
async def help():
    help_str = """Current Available Commands
               **t!start:** game description~
               **t!reap:** reap the time as your own
               **t!me:** see how much time you reaped
               **t!leaderboard / b:** shows who's top 10
               **t!log:** shows who recently reaped
               **t!info @player:** get player info
               **t!invite:** invite me :heart:"""

    await bot.say(help_str)


@bot.command(pass_context=True)
async def leaderboard(ctx):
    await print_leaderboard(ctx.message.channel)


@bot.command(pass_context=True)
async def b(ctx):
    await print_leaderboard(ctx.message.channel)


async def print_leaderboard(channel):
    if notice_message != "":
        await bot.send_message(channel, notice_message)

    players = read_players()[:10]
    embed = discord.Embed(color=0x42d7f4)
    embed.title = "The current top {} are:".format(len(players))
    for index, player in enumerate(players):
        # Drop the number at the end of the author's name (#NNNN)
        player_title = player.name[:-5]
        for i, ranked_player in enumerate(teir_list):
            if ranked_player == player.name:
                player_title += " " + rank_icon[i]

        embed.add_field(name='#{} {}'.format(index + 1, player_title),
                        value=seconds_format(player.reaped_time))
    await bot.send_message(channel, embed=embed)


@bot.command(pass_context=True)
async def invite(ctx):
    embed = discord.Embed(color=0x42d7f4)
    embed.description = \
        "[Invite me~](https://discordapp.com/api/oauth2/authorize?client_id=538078061682229258&permissions=0&scope=bot)"
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
# except:
# print('error')
# time.sleep(20)