import discord
import asyncio
import math
import pathlib
import random
import time
from discord.ext import commands
from DiscordTimeKeep import SecretFile

description = '''An bot designed to get time'''
bot = commands.Bot(command_prefix='t!', description=description)
bot.remove_command("help")


latest_clear = 0
CD = 43200


class Player:
    def __init__(self, representation):
        representation = str(representation).split("|")
        self.id = representation[0]
        self.name = representation[1]
        self.reaped_time = float(representation[2])
        self.next_reap = float(representation[3])

    def __str__(self):
        return "{}|{}|{}|{}".format(self.id, self.name, self.reaped_time, self.next_reap)


def read_players():
    # beginning is reserved for last_reap timer, and the last one is an empty new line
    return list(map(Player, pathlib.Path("./data/playerData.txt").read_text().split("\n")[1:]))


def write_players(players):
    with open("./data/playerData.txt", "w") as f:
        f.writelines(str(latest_clear) + "\n" +
                     "\n".join(map(str, sorted(players, key=lambda player: player.reaped_time, reverse=True))))


def get_latest_time():
    with open("./data/playerData.txt", "r") as f:
        content = f.readlines()
    return content[0]


def hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return int(h), int(m), int(s)


def seconds_format(seconds):
    return '{} Hours {} Minutes {} Seconds'.format(*hms(seconds))


async def start_timer():
    while True:
        await update_time_status()
        await asyncio.sleep(4.975)


async def update_time_status():
    flowed_time = int(time.time() - latest_clear)
    time_str = "{}H {}M {}S".format(*hms(flowed_time))
    await bot.change_presence(game=discord.Game(name='t!: ' + time_str))


@bot.event
async def on_ready():  # when ready it prints the username, id, and starts the status update
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    global latest_clear
    latest_clear = float(get_latest_time())
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
    global latest_clear
    author_id = ctx.message.author.id
    author = ctx.message.author
    current_time = float(time.time())
    added_time = current_time - latest_clear

    players = read_players()
    try:
        # Find the current player
        player = next(player for player in players if player.id == author_id)
    except StopIteration:
        # We couldn't find the player, so create a new one and insert it into players
        # This is kind of ugly, but Python doesn't have overloading...
        player = Player("{}|{}|{}|{}".format(author_id, author, 0, 0))
        players.append(player)

    if current_time < player.next_reap:
        await bot.say("""Sorry, reaping is still on cooldown
                      please wait another {} hours {} minutes and {} seconds
                      """.format(*hms(player.next_reap - current_time)))
    else:
        await bot.say('<@!{}> has added {} to their total'.format(author_id, seconds_format(added_time)))
        latest_clear = current_time
        player.reaped_time += added_time
        player.next_reap = current_time + CD
        # Strip out the last five characters (the #NNNN part)
        update_logs(str(author)[:-5], seconds_format(added_time))

    write_players(players)
    print("reap attempt by {} with {}".format(author, math.floor(added_time)))


def update_logs(author, added_time):
    with open("./data/reapLog.txt", "r") as f:
        content = f.readlines()
    info = '{} reaped for {}\n'.format(author, added_time)
    content = [info] + content
    if len(content) > 10:
        content.pop()
    with open("./data/reapLog.txt", "w") as f:
        f.writelines(content)


@bot.command(pass_context=True)
async def me(ctx):
    author_id = ctx.message.author.id
    players = read_players()
    try:
        # Find the current player
        index, player = next((index, player) for index, player in enumerate(players) if player.id == author_id)
    except StopIteration:
        # Player doesn't exist in our logs, so tell them to reap
        await bot.say("""<@!{}> has stored 0 seconds
                        use t!reap to get started""".format(author_id))
        index = len(players)

    current_time = float(time.time())
    if current_time < player.next_reap:
        next_reap = seconds_format(player.next_reap - current_time)
    else:
        next_reap = 'Your next reap is up'

    await bot.say("""Stats of <@!{}>
                  stored time: {} seconds
                  or {}
                  Next Reap: {}
                  Rank: {}
                  """.format(author_id, str(player.reaped_time)[:-2],
                             seconds_format(player.reaped_time),
                             next_reap, index + 1))


@bot.command(pass_context=True)
async def log(ctx):
    with open("./data/reapLog.txt", "r") as f:
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


@bot.command(pass_context=True)
async def dev(ctx):
    if not str(ctx.message.author.id) == '297971074518351872':
        await bot.say("Sorry~ this one's only for mango")
        return
    global latest_clear
    latest_clear -= 60
    await bot.say("Dev detected: {}".format("storing extra 60 seconds"))


@bot.command()
async def help():
    help_str = """Current Available Commands
               **t!start:** game description~
               **t!reap:** reap the time as your own
               **t!me:** see how much time you reaped
               **t!leaderboard:** shows who's top 10
               **t!log:** shows who recently reaped"""
    await bot.say(help_str)


@bot.command(pass_context=True)
async def leaderboard(ctx):
    players = read_players()[:10]
    embed = discord.Embed(color=0x42d7f4)
    embed.title = "The current top {} are:".format(len(players))
    for index, player in enumerate(players):
        # Drop the number at the end of the author's name (#NNNN)
        embed.add_field(name='#{} {}'.format(index + 1, player.name[:-5]),
                        value=seconds_format(player.reaped_time))
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def invite(ctx):
    embed = discord.Embed(color=0x42d7f4)
    embed.description = \
        "[Invite me~](https://discordapp.com/api/oauth2/authorize?client_id=538078061682229258&permissions=0&scope=bot)"
    await bot.say(embed=embed)


@bot.command(pass_context=True)
async def stored(ctx):
    await bot.say('Currently stored {}'.format(seconds_format(int(time.time() - latest_clear))))


@bot.event
async def on_message(message):
    if '538078061682229258' in message.content:
        await bot.send_message(message.channel, 'Currently stored {}'
                               .format(seconds_format(int(time.time() - latest_clear))))
    await bot.process_commands(message)


bot.run(SecretFile.get_token())  # are you happy now Soap????
