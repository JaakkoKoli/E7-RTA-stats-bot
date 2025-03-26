import requests
import json
import os
from match_data import *
from functions import *
from hero_data import *

if not os.path.exists("data"):
    os.makedirs("data") 

def get_legend_players() -> tuple[list[int], list[str]]:
    responses = []
    try:
        for i in range(10):
            response = requests.post(
            f"https://epic7.onstove.com/gg/gameApi/getWorldUserRankingDetail?season_code=pvp_rta_ss16&world_code=all&current_page={i+1}&lang=en"
            )
            if response.status_code == 200:
                responses += [response.json()]
    except:
        print("error in get top 100")
    
    user_ids = []
    user_servers = []
    for page in responses:
        for player_data in page["result_body"]:
            user_ids += [player_data["nick_no"]]
            user_servers += [player_data["world_code"].replace("world_","")]
    return user_ids, user_servers
        
if not os.path.exists("data"):
    os.makedirs("data")        

get_new_heroname_json()
with open("data/heronames.json", "r") as json_file:
    hero_list = HeroList(json.load(json_file))
hero_dict = hero_list.get_hero_vector_dict()

legend_player_ids, legend_player_servers = get_legend_players()

legend_player_dict = {}
for i in range(len(legend_player_ids)):
    legend_player_dict[str(i)] = f"{legend_player_ids[i]}#{legend_player_servers[i]}"

match_list = []
match_list_all = []
for i in range(len(legend_player_ids)):
    response = get_match_data_by_user_id(legend_player_ids[i], legend_player_servers[i])
    if response.status_code == 200:
        match_list += [response.json()["result_body"]["battle_list"]]
        match_list_all += response.json()["result_body"]["battle_list"]

legend_player_pick_vectors = {}
legend_player_prebans = {}
for i in range(len(match_list)):
    matches = MatchHistory([Match(match, hero_list) for match in match_list[i]])
    legend_player_pick_vectors[legend_player_dict[str(i)]] = matches.get_pick_vector(hero_dict)
    legend_player_prebans[legend_player_dict[str(i)]] = {x[0]: x[1] for x in matches.get_all_own_preban_counts().most_common(3)}

matches = MatchHistory([Match(match, hero_list) for match in match_list_all])

presence = matches.get_all_heroes_present_counts()

picks = matches.get_all_own_pick_counts()
wins = matches.get_all_own_pick_win_counts()

early_picks = matches.get_all_own_pick_counts_by_pick_order([0,1])
early_picks_wins = matches.get_all_own_win_counts_by_pick_order([0,1])

third_picks = matches.get_all_own_pick_counts_by_pick_order([2])
third_picks_wins = matches.get_all_own_win_counts_by_pick_order([2])

late_picks = matches.get_all_own_pick_counts_by_pick_order([3,4])
late_picks_wins = matches.get_all_own_win_counts_by_pick_order([3,4])

prebans = matches.get_all_own_preban_counts()
prebans_wins = matches.get_all_own_preban_win_counts()

first_picks = matches.get_all_own_first_pick_counts()
first_picks_wins = matches.get_all_own_first_pick_win_counts()



legend_data = {"presence": presence,
               "picks": picks,
               "wins": wins,
               "early_picks": early_picks,
               "early_picks_wins": early_picks_wins,
               "third_picks": third_picks,
               "third_picks_wins": third_picks_wins,
               "late_picks": late_picks,
               "late_picks_wins": late_picks_wins,
               "prebans": prebans,
               "prebans_wins": prebans_wins,
               "first_picks": first_picks,
               "first_picks_wins": first_picks_wins,
               "pick_vectors": legend_player_pick_vectors,
               "individual_prebans": legend_player_prebans}

with open("data/legend_data.json", "w") as json_file:
    json.dump(legend_data, json_file, indent=4)