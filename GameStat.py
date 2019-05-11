class_name = {1: "Chrono Warrior", 2: "Time Mage",
              3: "Space-Time Hunter", 4: "Thousand Year Fairy",
              5: "Dimensional Bandit"}

class_name_short = {1: "Warrior", 2: "Mage",
                    3: "Hunter", 4: "Fairy",
                    5: "Bandit"}

teir_list = ['Howyu#7873', 'Tropic Mango#6755',
             'Soap#3672', 'ExcaliburSux#7162',
             'Ajisoo#9487', 'LuxuFate#8990']

rank_icon = ['<:Challenger_Rank:559574999149838377>', '<:Diamond_Rank:559575017885532194>',
             '<:Plat_Rank:559575046516113423>', '<:Gold_Rank:559575070670848001>',
             '<:Silver_Rank:559575087955836938>', '<:Bronze_Rank:559575105634566144>']

help_str = """Current Available Commands
               **t!start:** game description~
               **t!reap:** reap the time as your own
               **t!me:** see how much time you reaped
               **t!leaderboard / b:** shows who's top 10
               **t!log:** shows who recently reaped
               **t!info @player:** get player info
               **t!invite:** invite me :heart:"""

start_str = """"Welcome to the Arena of Time,
     Use **t!choose <ID>** begin
     
    1. **Chrono Warrior**: bonus 25% Time Reaped
    2. **Time Mage**: 25% Faster Reap Cooldown
    3. **Space-Time Hunter**: 25% Chance to Crit
    4. **Thousand Year Fairy**: Bonus 15 Min per Reap
    5. **Dimensional Bandit**: Gains a *steal* ability
    (Bandit Only)*t!steal:* Available 1 Min After the Latest Reap"""

warrior_buff = 1.25
hunter_crit_rate = 0.25
hunter_crit_dmg = 2
mage_reduction_rate = 0.25
fairy_boost = 15
reap_cooldown = 600  # reap_cooldown = 21600


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
