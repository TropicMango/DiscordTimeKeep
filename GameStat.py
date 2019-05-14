warrior_buff = 1.25
hunter_crit_rate = 0.25
hunter_crit_dmg = 2
mage_reduction_rate = 0.25
fairy_boost = 15
reap_cooldown = 21600  # reap_cooldown = 21600

class_name = {1: "Chrono Warrior", 2: "Time Mage",
              3: "Space-Time Hunter", 4: "Thousand Year Fairy",
              5: "Dimensional Bandit"}

class_name_short = {1: "Warrior", 2: "Mage",
                    3: "Hunter", 4: "Fairy",
                    5: "Bandit"}

teir_list = ['Soap#3672', 'Porolific#3003',
             'LuxuFate#8990', 'Tropic Mango#6755',
             'Howyu#7873', 'Whispyr#0001']

rank_icon = ['<:Challenger_Rank:559574999149838377>', '<:Diamond_Rank:559575017885532194>',
             '<:Plat_Rank:559575046516113423>', '<:Gold_Rank:559575070670848001>',
             '<:Silver_Rank:559575087955836938>', '<:Bronze_Rank:559575105634566144>']

help_str = """Current Available Commands
               **t!start:** Game Description~
               **t!choose** Choose Your Class
               **t!change** Change Your Class (resets reap)
               **t!reap:** Reap The Time as Your Own
               **t!me:** See How Much Time You Reaped
               **t!leaderboard / b:** Shows Who's Top 10
               **t!log:** Shows Who Recently Reaped
               **t!info @player:** Get Player Info
               **t!invite:** Invite Me :heart:"""

start_str = """"Welcome to the Arena of Time,
     Use **t!choose <Class #>** begin
     DW you can change with **t!change <Class #>**
     
    1. **Chrono Warrior**: bonus {}% Time Reaped
    2. **Time Mage**: {}% Faster Reap Cooldown
    3. **Space-Time Hunter**: {}% Chance to Crit
    4. **Thousand Year Fairy**: Bonus {} Min per Reap
    5. **Dimensional Bandit**: Gains a *steal* ability
    (Bandit Only)**t!steal:** Available 1 Min After the Latest Reap"""\
    .format((warrior_buff - 1) * 100, mage_reduction_rate * 100, hunter_crit_rate * 100, fairy_boost)


class Player:
    def __init__(self, representation):
        representation = str(representation).split("|")
        self.id = representation[0]
        self.name = representation[1]
        self.reaped_time = float(representation[2])
        self.next_reap = float(representation[3])
        self.reap_count = int(representation[4])
        self.class_type = int(representation[5])

    def __str__(self):
        return "{}|{}|{}|{}|{}|{}"\
            .format(self.id, self.name, self.reaped_time, self.next_reap, self.reap_count, self.class_type)
