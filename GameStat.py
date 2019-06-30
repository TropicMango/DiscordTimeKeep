game_update_str = '**UPDATE** new patch released, use t!pn for more information~'
log_size = 20
current_season = 5

warrior_buff = 1.25
hunter_crit_rate = 0.25
hunter_crit_dmg = 2
mage_reduction_rate = 0.25
fairy_boost = 15
gamble_chance = 0.125
gamble_reward = 10
gamble_cost = 15
voyage_chance = 0.005
voyage_reward = 150
reap_cooldown = 21600  # reap_cooldown = 21600

blue_shell_chance = 0.05
blue_shell_icon = '<:Blue_Shell:580276103491485701>'

class_name = {1: "Chrono Warrior", 2: "Time Mage",
              3: "Space-Time Hunter", 4: "Thousand Year Fairy",
              5: "Dimensional Bandit", 6: "Twilight Mercenary",
              7: "Void Gambler", 8: "Abyssal Voyager"}

class_name_short = {1: "Warrior", 2: "Mage",
                    3: "Hunter", 4: "Fairy",
                    5: "Bandit", 6: "Merc",
                    7: "Gambler", 8: "Voyager"}

reward_icons = {'195755433766420480': '<:Challenger_Rank:559574999149838377>',
                '219324654290993153': '<:Diamond_Rank:559575017885532194>',
                '186208659221643264': '<:Plat_Rank:559575046516113423>',
                '192144504998854658': '<:Gold_Rank:559575070670848001>',
                '236279950259257345': '<:Silver_Rank:559575087955836938>',
                '137016970917707776': '<:Bronze_Rank:559575105634566144> 🌌',
                '117388990729945096': '<:Gamble:580329443374006282>'}

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
8. **Abyssal Voyager**: {}% Chance of Getting {}x (can't be stolen)
"""\
    .format((warrior_buff - 1) * 100,
            mage_reduction_rate * 100,
            hunter_crit_rate * 100,
            fairy_boost,
            gamble_chance * 100, gamble_reward, gamble_cost,
            voyage_chance * 100, voyage_reward)


start_str = """"Welcome to the Arena of Time,
     Use **t!choose <Class #>** begin
     You can change with **t!change <Class #>**
     """ + char_list


class Player:
    def __init__(self, representation):
        representation = str(representation).split("|")
        self.id = representation[0]
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
            .format(self.id, self.name, self.reaped_time, self.next_reap, self.reap_count, self.class_type)
