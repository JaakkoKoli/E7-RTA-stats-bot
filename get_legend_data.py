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
    current_season_code = get_season_info()['season_code']
    try:
        for i in range(10):
            response = requests.post(
            f"https://epic7.onstove.com/gg/gameApi/getWorldUserRankingDetail?season_code={current_season_code}&world_code=all&current_page={i+1}&lang=en"
            )
            if len(response.json()["result_body"]) == 0:
                response = requests.post(
                f"https://epic7.onstove.com/gg/gameApi/getWorldUserRankingDetail?season_code=pvp_rta_ss17&world_code=all&current_page={i+1}&lang=en"
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
matches.remove_duplicates()

presence = matches.get_all_heroes_present_counts()

match_results = matches.get_match_result_vector()

picks = matches.get_all_own_pick_counts()
picks_all = matches.get_all_pick_counts()
wins = matches.get_all_own_pick_win_counts()

early_picks = matches.get_all_own_pick_counts_by_pick_order([0,1])
early_picks_all = matches.get_all_pick_counts_by_pick_order([0,1])
early_picks_wins = matches.get_all_own_win_counts_by_pick_order([0,1])

third_picks = matches.get_all_own_pick_counts_by_pick_order([2])
third_picks_all = matches.get_all_pick_counts_by_pick_order([2])
third_picks_wins = matches.get_all_own_win_counts_by_pick_order([2])

late_picks = matches.get_all_own_pick_counts_by_pick_order([3,4])
late_picks_all = matches.get_all_pick_counts_by_pick_order([3,4])
late_picks_wins = matches.get_all_own_win_counts_by_pick_order([3,4])

prebans = matches.get_all_own_preban_counts()
prebans_all = matches.get_all_preban_counts()
prebans_wins = matches.get_all_own_preban_win_counts()

first_picks = matches.get_all_own_first_pick_counts()
first_picks_all = matches.get_all_first_pick_counts()
first_picks_wins = matches.get_all_own_first_pick_win_counts()

combinations = matches.get_own_combinations_picks()
combinations_wins = matches.get_own_combinations_wins()

combinations_dict = {}
combinations_dict_ = {}
for i, key in enumerate(combinations.keys()):
    combinations_dict[i] = key
    combinations_dict_[i] = list(key)
combinations_ = {i: combinations.get(combinations_dict[i], 0) for i in range(len(combinations.keys()))}
combinations_wins_ = {i: combinations_wins.get(combinations_dict[i], 0) for i in range(len(combinations.keys()))}


legend_data = {"match_result_vector": match_results,
               "presence": presence,
               "picks": picks,
               "picks_all": picks_all,
               "wins": wins,
               "early_picks": early_picks,
               "early_picks_all": early_picks_all,
               "early_picks_wins": early_picks_wins,
               "third_picks": third_picks,
               "third_picks_all": third_picks_all,
               "third_picks_wins": third_picks_wins,
               "late_picks": late_picks,
               "late_picks_all": late_picks_all,
               "late_picks_wins": late_picks_wins,
               "prebans": prebans,
               "prebans_all": prebans_all,
               "prebans_wins": prebans_wins,
               "first_picks": first_picks,
               "first_picks_all": first_picks_all,
               "first_picks_wins": first_picks_wins,
               "pick_vectors": legend_player_pick_vectors,
               "individual_prebans": legend_player_prebans,
               "combinations": combinations_,
               "combinations_wins": combinations_wins_,
               "combinations_keys": combinations_dict_}

with open("data/legend_data.json", "w") as json_file:
    json.dump(legend_data, json_file, indent=4)