from DiscordTimeKeep import GameStat
import pathlib


def read_players():
    # beginning is reserved for last_reap timer, and the last one is an empty new line
    return list(map(GameStat.Player, pathlib.Path("./data/playerData.txt").read_text(encoding='utf-8').split("\n")[1:]))


def write_players(players, latest_clear):
    with open("./data/playerData.txt", "w", encoding='utf-8') as f:
        f.writelines(str(latest_clear) + "\n" +
                     "\n".join(map(str, sorted(players, key=lambda player: player.reaped_time, reverse=True))))


def update_logs_reap(author, added_time, class_type, stolen=False):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()

    if stolen:
        info = '**{}** - *STOLEN* by {}\n'.format(added_time, author)
    else:
        info = '**{}** - *{}:* {}\n'.format(added_time, GameStat.class_name[class_type], author)

    content = [info] + content
    if len(content) > 10:
        content.pop()
    with open("./data/reapLog.txt", "w", encoding='utf-8') as f:
        f.writelines(content)


def update_logs_class(author, class_type, change=False):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()

    if change:
        info = '**{}** is changed class to *{}*\n'.format(author, class_type)
    else:
        info = '**{}** joined the arena as a *{}*\n'.format(author, class_type)

    content = [info] + content
    if len(content) > 10:
        content.pop()
    with open("./data/reapLog.txt", "w", encoding='utf-8') as f:
        f.writelines(content)

