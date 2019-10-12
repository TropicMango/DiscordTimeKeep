import random

game_update_str = '**UPDATE** new patch released, use t!pn for more information~'
log_size = 20
current_season = 6

warrior_buff = 1.25
hunter_crit_rate = 0.25
hunter_crit_dmg = 2
mage_reduction_rate = 0.30
fairy_boost = 25
gamble_chance = 0.125
gamble_reward = 10
gamble_cost = 15
voyage_reduction = 0.25
voyage_chance = 0.001
voyage_reward = 150
sniper_threshold = 7200
striker_max_reward = 3
striker_reward_drop = 5 / 18
capacitor_boost = 1
reap_cooldown = 21600  # reap_cooldown = 21600

blue_shell_chance = 0.05
blue_shell_icon = '<:Blue_Shell:580276103491485701>'

class_name = {1: "Chrono Warrior", 2: "Time Mage",
              3: "Space-Time Hunter", 4: "Thousand Year Fairy",
              5: "Dimensional Bandit", 6: "Twilight Mercenary",
              7: "Void Gambler", 8: "Abyssal Voyager",
              9: "Cosmic Sniper", 10: "Momentum Striker",
              11: "Unknown Capacitor"}

class_name_short = {1: "Warrior", 2: "Mage",
                    3: "Hunter", 4: "Fairy",
                    5: "Bandit", 6: "Merc",
                    7: "Gambler", 8: "Voyager",
                    9: "Sniper", 10: "Striker",
                    11: "Capacitor"}

reward_icons = {'193550776340185088': '<:Challenger_Rank:559574999149838377>',
                '219324654290993153': '<:Diamond_Rank:559575017885532194>',
                '137016970917707776': '<:Plat_Rank:559575046516113423>',
                '297971074518351872': '<:Gold_Rank:559575070670848001>',
                '236279950259257345': '<:Silver_Rank:559575087955836938>',
                '585607406143406080': '<:Bronze_Rank:559575105634566144>',
                '500656746440949761': '<:Gamble:580329443374006282>'}

help_str = """Current Available Commands
               **t!start:** Game Description~
               **t!choose:** Choose Your Class
               **t!change:** Change Your Class (resets reap)
               **t!reap:** Reap The Time as Your Own
               **t!me:** See How Much Time You Reaped
               **t!leaderboard / b:** Shows Who's Top 10, and more
               **t!leaderboard / b: <Season #>** Shows the Season
               **t!log:** Shows Who Recently Reaped
               **t!info @player / #rank:** Get Player Info
               **t!pn** Get Patch Notes
               **t!invite:** Invite Me :heart:"""

char_list = """
1. **Chrono Warrior**: bonus {}% Time Reaped
2. **Time Mage**: {}% Faster Reap Cooldown
3. **Space-Time Hunter**: {}% Chance to Crit
4. **Thousand Year Fairy**: Bonus {} Min per Reap
5. **Dimensional Bandit**: Gains a *steal* ability
 - Bandit Only - **t!steal:** Available 1 Min After the Latest Reap
6. **Twilight Mercenary**: Instant Reap, Can't be Stolen
7. **Void Gambler**: {}% Chance of Getting {}x or Lose {} Minutes
8. **Abyssal Voyager**: {}% Less Time Reaped, but {}% chance to gain {}x
9. **Cosmic Sniper**: Reset Cooldown When Reap is over {} Minutes
10. **Momentum Striker**: Gains Up to {}x Based on Time Since Reap Ready
11. **Unknown Capacitor**: Gains {}x for Each Day Since Your Last Reap
"""\
    .format((warrior_buff - 1) * 100,
            mage_reduction_rate * 100,
            hunter_crit_rate * 100,
            fairy_boost,
            gamble_chance * 100, gamble_reward, gamble_cost,
            (1 - voyage_reduction) * 100, voyage_chance * 100, voyage_reward,
            sniper_threshold / 60,
            striker_max_reward,
            capacitor_boost)


start_str = """"Welcome to the Arena of Time,
     Use **t!choose <Class #>** begin
     You can change with **t!change <Class #>**
     """ + char_list


voyage_msg = [
    'there is nothing in the abyss',
    'you stared into the abyss, and the abyss stared back',
    'the abyss is judging you silently',
    'you met a lost voyager',
    'i laila este hapana nel ang A-B-Y-S-S',
    'you are getting hungry',
    'sleep.......',
    'i\'m sorry for your loss?',
    'you hear . . . nothing (cuz space :3)'
]


def get_voyage_msg():
    return random.choice(voyage_msg)


fun_fact = [
    'there\'s like actually nothing in the abyss',
    'find who last reaped by doing t!log',
    'find patch notes with t!pn',
    'change class whenever you like with t!change',
    'introduce me to your friends with t!invite',
    'some of the classes are not balanced, cuz the developer\'s dumb and lazy'
]


def get_fun_fact():
    return random.choice(fun_fact)


class Player:
    def __init__(self, representation):
        representation = str(representation).split("|")
        self.id = int(representation[0])
        self.name = representation[1]
        self.reaped_time = float(representation[2])
        self.next_reap = float(representation[3])

        try:
            self.reap_count = int(representation[4])
            self.class_type = int(representation[5])
        except (ValueError, IndexError):
            return  # Nothing happens

    def __str__(self):
        return "{}|{}|{}|{}|{}|{}"\
            .format(self.id, self.name, round(self.reaped_time), self.next_reap, self.reap_count, self.class_type)
