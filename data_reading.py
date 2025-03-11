from functions import *
from collections import Counter

class Pick:
    hero_data = init_hero_data_code_to_name()
    def __init__(self, hero:object, pick_order:int):
        self.hero_code:str = hero["hero_code"]
        self.hero_name:str = Pick.hero_data[self.hero_code]
        self.mvp:bool = hero["mvp"]
        self.ban:bool = hero["ban"]
        self.first_pick:bool = hero["first_pick"]
        self.pick_order:int = pick_order
        self.image:str = f"hero_images/{self.hero_code}.png"

class Match:
    hero_data = init_hero_data_code_to_name()
    
    def __init__(self, match_data:object):
        self.picks_own:list[Pick] = []
        self.picks_enemy:list[Pick] = []
        self.read_match_data(match_data)
        
    def read_match_data(self, match_data:object) -> None:
        for i, hero in enumerate(match_data["my_deck"]["hero_list"]):
            self.picks_own.append(Pick(hero, i))
            
        for i, hero in enumerate(match_data["enemy_deck"]["hero_list"]):
            self.picks_enemy.append(Pick(hero, i))
        
        self.preban_own_codes:list[str] = [x for x in match_data["my_deck"]["preban_list"] if x!=""]
        self.preban_own_names:list[str] = [Match.hero_data[x] for x in self.preban_own_codes]
        self.preban_enemy_codes:list[str] = [x for x in match_data["enemy_deck"]["preban_list"] if x!=""]
        self.preban_enemy_names:list[str] = [Match.hero_data[x] for x in self.preban_enemy_codes]
        
        self.win:bool = match_data["iswin"] == 1
        self.points_after_match:int = int(match_data["winScore"])
    
    def get_own_picks_codes(self) -> list[str]:
        return [x.hero_code for x in self.picks_own]
    
    def get_enemy_picks_codes(self) -> list[str]:
        return [x.hero_code for x in self.picks_enemy]
    
    def get_all_picks_codes(self) -> list[str]:
        return self.get_all_picks_codes + self.get_enemy_picks_codes
    
    def get_own_mvp(self) -> str:
        for pick in self.picks_own:
            if pick.mvp:
                return pick.hero_code
        return ""
    
    def get_own_ban(self) -> str:
        for pick in self.picks_own:
            if pick.ban:
                return pick.hero_code
        return ""
    
    def get_enemy_ban(self) -> str:
        for pick in self.picks_enemy:
            if pick.ban:
                return pick.hero_code
        return ""
    
    def get_own_first_pick(self) -> str:
        for pick in self.picks_own:
            if pick.first_pick:
                return pick.hero_code
        return ""
    
class MatchHistory:
    
    def __init__(self, matches:list[Match]):
        self.matches = matches
    
    def get_match_result_vector(self) -> list[int]:
        return [match.win for match in self.matches]
    
    def get_all_heroes_present_counts(self) -> Counter:
        picks = []
        for match in self.matches:
            picks += match.get_own_picks_codes() + match.get_enemy_picks_codes() + list(set(match.preban_enemy_codes + match.preban_own_codes))
        return Counter(picks)
    
    def get_all_own_pick_counts_by_pick_order(self, pick_order:list[int]) -> Counter:
        picks = []
        for match in self.matches:
            for pick in match.picks_own:
                if pick.pick_order in pick_order:
                    picks += [pick.hero_code]
        return Counter(picks)
    
    def get_all_own_win_counts_by_pick_order(self, pick_order:list[int]) -> Counter:
        picks = []
        for match in self.matches:
            if match.win:
                for pick in match.picks_own:
                    if pick.pick_order in pick_order:
                        picks += [pick.hero_code]
        return Counter(picks)
    
    def get_all_own_pick_counts(self) -> Counter:
        picks = []
        for match in self.matches:
            picks += match.get_own_picks_codes()
        return Counter(picks)

    def get_all_enemy_pick_counts(self) -> Counter:
        picks = []
        for match in self.matches:
            picks += match.get_enemy_picks_codes()
        return Counter(picks)
    
    def get_all_own_pick_win_counts(self) -> Counter:
        picks = []
        for match in self.matches:
            if match.win:
                picks += match.get_own_picks_codes()
        return Counter(picks)
    
    def get_all_enemy_pick_win_against_counts(self) -> Counter:
        picks = []
        for match in self.matches:
            if match.win:
                picks += match.get_enemy_picks_codes()
        return Counter(picks)
    
    def get_all_own_preban_counts(self) -> Counter:
        prebans = []
        for match in self.matches:
            prebans += match.preban_own_codes
        return Counter(prebans)
    
    def get_all_own_preban_win_counts(self) -> Counter:
        prebans = []
        for match in self.matches:
            if match.win:
                prebans += match.preban_own_codes
        return Counter(prebans)
    
    def get_all_own_mvp_counts(self) -> Counter:
        mvps = []
        for match in self.matches:
            mvp = match.get_own_mvp()
            if mvp != "":
                mvps.append(mvp)
        return Counter(mvps)
    
    def get_all_own_ban_counts(self) -> Counter:
        bans = []
        for match in self.matches:
            ban = match.get_own_ban()
            if ban != "":
                bans.append(ban)
        return Counter(bans)
    
    def get_all_enemy_ban_counts(self) -> Counter:
        bans = []
        for match in self.matches:
            ban = match.get_enemy_ban()
            if ban != "":
                bans.append(ban)
        return Counter(bans)
    
    def get_all_own_ban_win_counts(self) -> Counter:
        bans = []
        for match in self.matches:
            ban = match.get_own_ban()
            if ban != "" and match.win:
                bans.append(ban)
        return Counter(bans)
    
    def get_all_enemy_ban_win_counts(self) -> Counter:
        bans = []
        for match in self.matches:
            ban = match.get_enemy_ban()
            if ban != "" and match.win:
                bans.append(ban)
        return Counter(bans)
    
    def get_all_own_first_pick_counts(self) -> Counter:
        first_picks = []
        for match in self.matches:
            first_pick = match.get_own_first_pick()
            if first_pick != "":
                first_picks.append(first_pick)
        return Counter(first_picks)
    
    def get_all_own_first_pick_win_counts(self) -> Counter:
        first_picks = []
        for match in self.matches:
            if match.win:
                first_pick = match.get_own_first_pick()
                if first_pick != "":
                    first_picks.append(first_pick)
        return Counter(first_picks)
    
    def get_matchup_counts(self) -> dict:
        matchups = {}
        for match in self.matches:
            for own_code in match.get_own_picks_codes():
                if not own_code in matchups.keys():
                    matchups[own_code] = []
                matchups[own_code] += match.get_enemy_picks_codes() + ["total"]
        for key in matchups.keys():
            matchups[key] = Counter(matchups[key])
        return matchups
    
    def get_matchup_win_counts(self) -> dict:
        matchups = {}
        for match in self.matches:
            if match.win:
                for own_code in match.get_own_picks_codes():
                    if not own_code in matchups.keys():
                        matchups[own_code] = []
                    matchups[own_code] += match.get_enemy_picks_codes() + ["total"]
        for key in matchups.keys():
            matchups[key] = Counter(matchups[key])
        return matchups
    
    def get_ally_counts(self) -> dict:
        allies = {}
        for match in self.matches:
            own_pick_codes = match.get_own_picks_codes()
            for i, own_code in enumerate(own_pick_codes):
                if not own_code in allies.keys():
                    allies[own_code] = []
                if len(own_pick_codes) == 5:
                    allies[own_code] += own_pick_codes[:i] + own_pick_codes[i+1:]  + ["total"]
        for key in allies.keys():
            allies[key] = Counter(allies[key])
        return allies
    
    def get_ally_win_counts(self) -> dict:
        allies = {}
        for match in self.matches:
            own_pick_codes = match.get_own_picks_codes()
            for i, own_code in enumerate(own_pick_codes):
                if not own_code in allies.keys():
                    allies[own_code] = []
                if match.win and len(own_pick_codes) == 5:
                    allies[own_code] += own_pick_codes[:i] + own_pick_codes[i+1:] + ["total"]
        for key in allies.keys():
            allies[key] = Counter(allies[key])
        return allies
    
    def get_own_ban_vector(self) -> list[int]:
        bans = [0]*len(self.matches)
        for i, match in enumerate(self.matches):
            bans[i] = int(match.get_own_ban()!= "")
        return bans
    
    def get_enemy_ban_vector(self) -> list[int]:
        bans = [0]*len(self.matches)
        for i, match in enumerate(self.matches):
            bans[i] = int(match.get_enemy_ban()!= "")
        return bans
    
    def get_first_pick_vector(self) -> list[int]:
        first_picks = [0]*len(self.matches)
        for i, match in enumerate(self.matches):
            first_picks[i] = int(match.get_own_first_pick() != "")
        return first_picks
    
    def get_first_pick_wins_vector(self) -> list[int]:
        first_picks = [0]*len(self.matches)
        for i, match in enumerate(self.matches):
            first_picks[i] = int((match.get_own_first_pick() != "") and match.win)
        return first_picks
    
    def get_own_trios_picks(self):
        trios = []
        for match in self.matches:
            picks = match.get_own_picks_codes()
            if len(picks) == 5:
                trios += [frozenset({picks[0],picks[1],picks[2]}), 
                          frozenset({picks[0],picks[1],picks[3]}),
                          frozenset({picks[0],picks[1],picks[4]}),
                          frozenset({picks[0],picks[2],picks[3]}),
                          frozenset({picks[0],picks[2],picks[4]}),
                          frozenset({picks[0],picks[3],picks[4]}),
                          frozenset({picks[1],picks[2],picks[3]}),
                          frozenset({picks[1],picks[2],picks[4]}),
                          frozenset({picks[1],picks[3],picks[4]}),
                          frozenset({picks[2],picks[3],picks[4]})]
        return Counter(trios)
    
    def get_own_trios_wins(self):
        trios = []
        for match in self.matches:
            picks = match.get_own_picks_codes()
            if len(picks) == 5 and match.win:
                trios += [frozenset({picks[0],picks[1],picks[2]}), 
                          frozenset({picks[0],picks[1],picks[3]}),
                          frozenset({picks[0],picks[1],picks[4]}),
                          frozenset({picks[0],picks[2],picks[3]}),
                          frozenset({picks[0],picks[2],picks[4]}),
                          frozenset({picks[0],picks[3],picks[4]}),
                          frozenset({picks[1],picks[2],picks[3]}),
                          frozenset({picks[1],picks[2],picks[4]}),
                          frozenset({picks[1],picks[3],picks[4]}),
                          frozenset({picks[2],picks[3],picks[4]})]
        return Counter(trios)