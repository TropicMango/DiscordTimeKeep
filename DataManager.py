from DiscordTimeKeep import GameStat
import pathlib


def read_players(season=GameStat.current_season):
    # beginning is reserved for last_reap timer, and the last one is an empty new line
    if season == GameStat.current_season:
        return list(map(GameStat.Player, pathlib.Path("./data/playerData.txt")
                        .read_text(encoding='utf-8').split("\n")[1:]))
    else:
        path = "./data/S{}.txt".format(season)
        return list(map(GameStat.Player, pathlib.Path(path)
                        .read_text(encoding='utf-8').split("\n")[1:]))


def write_players(players, latest_clear):
    with open("./data/playerData.txt", "w", encoding='utf-8') as f:
        f.writelines(str(latest_clear) + "\n" +
                     "\n".join(map(str, sorted(players, key=lambda player: player.reaped_time, reverse=True))))


def update_logs_shell(author, added_time):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()

    info = '***Blue Shell <:Blue_Shell:580276103491485701>*** - {} has activated a blue shell\n'\
        .format(author)

    content = [info] + content
    while len(content) > 100:
        content.pop()
    with open("./data/reapLog.txt", "w", encoding='utf-8') as f:
        f.writelines(content)


def update_logs_win(success, type, author=None, amount=None):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()

    if success:
        if type == "GAMBLE":
            info = '**💰!!!LUCKY COIN ACTIVATED!!!💰**\n'
        elif type == "VOYAGE":
            info = '**🌌!!!ABYSSAL VOYAGE SUCCESSFUL!!!🌌**\n'
    else:
        if type == "GAMBLE":
            info = '***GAMBLE*** - {} failed by **{}**\n'.format(amount, author)
        elif type == "VOYAGE":
            info = '***VOYAGE*** - {} failed by **{}**\n'.format(amount, author)

    content = [info] + content
    while len(content) > 100:
        content.pop()
    with open("./data/reapLog.txt", "w", encoding='utf-8') as f:
        f.writelines(content)


def update_logs_reap(author, added_time, class_type, stolen=False):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()

    if stolen:
        info = '***REAP*** - {} - *STOLEN* by **{}**\n'.format(added_time, author)
    else:
        if class_type == 7:
            info = '***GAMBLE💰*** - {} - *{}:* **{}**\n'.format(added_time, GameStat.class_name[class_type], author)
        elif class_type == 8:
            info = '***🌌VOYAGE🌌*** - {} - *{}:* **{}**\n'.format(added_time, GameStat.class_name[class_type], author)
        else:
            info = '***REAP*** - {} - *{}:* **{}**\n'.format(added_time, GameStat.class_name[class_type], author)

    content = [info] + content
    while len(content) > 100:
        content.pop()
    with open("./data/reapLog.txt", "w", encoding='utf-8') as f:
        f.writelines(content)


def update_logs_class(author, class_type, change=False):
    with open("./data/reapLog.txt", "r", encoding='utf-8') as f:
        content = f.readlines()

    if change:
        info = '***Class Change:*** *{}* is now a *{}*\n'.format(author, class_type)
    else:
        info = '***New Player:*** *{}* joined the arena as a *{}*\n'.format(author, class_type)

    content = [info] + content
    if len(content) > 100:
        content.pop()
    with open("./data/reapLog.txt", "w", encoding='utf-8') as f:
        f.writelines(content)

