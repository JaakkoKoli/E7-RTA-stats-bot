import os
from datetime import datetime, timedelta

from update_data import *
from functions import save_image_from_url, get_match_data_by_user_id, get_season_info
from user_data import *
from search_history import *
from hero_data import *
from match_data import *
from resource_handler import *

from flask import Flask, render_template, request, redirect, url_for, jsonify
from sklearn.decomposition import NMF
import numpy as np

########
# Data #
########

# Check if required folder structure exists, create if not

if not os.path.exists("data"):
    os.makedirs("data") 
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("static/hero_images"):
    os.makedirs("static/hero_images")   
if not os.path.exists("static/rank_icons"):
    os.makedirs("static/rank_icons")   
if not os.path.isfile("data/points.json"):
    with open("data/points.json", "w") as json_file:
        json.dump({}, json_file, indent=4)
  

# Update hero data, check if new image(s) need to be downloaded
hero_popularity = HeroPopularity()
if os.path.isfile("data/hero_popularity.json"):
    hero_popularity.load_popularity()

resource_handler = ResourceHandler(image_location="static/hero_images/")

hero_list = resource_handler.hero_list
hero_dict = hero_list.get_hero_vector_dict()

current_rank_images = [f.split(".")[0] for f in os.listdir("static/rank_icons") if os.path.isfile(os.path.join("static/rank_icons", f))]
for rank in ["bronze", "silver", "gold", "master", "challenger", "champion", "warlord", "emperor", "legend"]:
    if rank not in current_rank_images:
        save_image_from_url(f"https://static.smilegatemegaport.com/event/live/epic7/gg/images/common/grade/grade_{rank}.png", f"static/rank_icons/{rank}.png")

# Load and update user data, and create a search index
user_data = UserData()
points = Points()
points.load_points()
server_list = ["global", "asia", "jpn", "kor", "eu"]
for server in server_list:
    #get_new_userdata(server)
    with open(f"data/epic7_user_world_{server}.json", "r") as json_file:
        server_user_data = json.load(json_file)
        user_data.read_data(server_user_data, server)
user_data.create_search_index()
user_data.load_points(points.points)
# Initiate search history and load if previous data exists
search_history = SearchHistory()
if os.path.exists("data/search_history.json"):
    search_history.load_search_history()

def update_legend_data() -> tuple[dict, datetime, NMF, np.ndarray]:
    with open("data/legend_data.json", "r") as json_file:
        legend_data = json.load(json_file)
    nmf = NMF(n_components=4, init="nndsvd", random_state=42)
    legend_vectors = np.asarray([vector for vector in legend_data["pick_vectors"].values()]) / 100.0
    return legend_data, datetime.now(), nmf, nmf.fit_transform(legend_vectors)

def twelve_hours_from_last_update(last_update:datetime) -> bool:
    return datetime.now() - last_update >= timedelta(hours=12)

legend_data, legend_data_update_time, nmf, transformed_legend_picks = update_legend_data()

def get_predicted_winrate(picks:Counter, wins:Counter, wins_total:int, matches_total:int) -> Counter:
    winrate = {}
    for hero_code in picks.keys():
        if hero_code != "total":
            winrate[hero_code] = (wins[hero_code] + wins_total) / (picks[hero_code] + matches_total)
    return Counter(winrate)

def n_lowest_winrates(counter:Counter, n:int):
            counter = dict(counter)
            for key in counter.keys():
                counter[key] = 1 - counter[key]
            counter = Counter(counter)
            return counter.most_common(n)

def name_autocomplete(current:str):
    data = []
    users = user_data.find_user(current)
    usernames = [user.name for user in users]
    if current in usernames:
        user_string = users[usernames.index(current)].get_name_with_server()
        data.append(user_string)
    if len(users) != 0:
        best_indices = np.flip(np.argsort([user.points + user.level + (2000 - len(user.name)) for user in users]))
        i = 0
        while len(data) < 3 and i < len(best_indices):
            user = users[best_indices[i]]
            if user.name != current:
                user_string = user.get_name_with_server()
                data.append(user_string)
            i += 1
    return data


#############
# Flask app #
#############

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username_and_server = request.form.get("username").rsplit("#", 1)
        return redirect(url_for("user_summary", username=username_and_server[0], server=username_and_server[1]))
    return render_template("index.html")

@app.route("/user/<server>/<username>")
def user_summary(username, server):
    user = user_data.get_user(username, server)
    
    response = get_match_data_by_user_id(user.id, server)
    match_result_vector = []
    matches = MatchHistory([])
    if response.status_code == 200:
        match_list = response.json()["result_body"]["battle_list"]
        matches = MatchHistory([Match(match, hero_list) for match in match_list])
        match_result_vector = matches.get_match_result_vector()
        matches_n = len(match_result_vector)
        wins_n = sum(match_result_vector)
        
        enemy_picks = matches.get_all_enemy_pick_counts()
        enemy_wins = matches.get_all_enemy_pick_win_against_counts()
        matchups = matches.get_all_matchup_counts()
        matchups_wins = matches.get_all_matchup_win_counts()
    
        
        matchup_winrate = {}
        for hero_code in matchups.keys():
            if hero_code != "total":
                matchup_winrate[hero_code] = (matchups_wins.get(hero_code, Counter([]))["total"] + sum(match_result_vector)) / (matchups.get(hero_code, Counter([]))["total"] + len(match_result_vector))
        matchup_winrate = Counter(matchup_winrate)
        
        enemy_pick_winrate = {}
        for hero_code in enemy_picks.keys():
            if hero_code != "total":
                enemy_pick_winrate[hero_code] = (enemy_wins.get(hero_code, 0) + sum(match_result_vector)) / (enemy_picks.get(hero_code, 0) + len(match_result_vector))
        enemy_pick_winrate = Counter(enemy_pick_winrate)
        
        match_summary = {
            "username": username,
            "server": server,
            "point": user.points,
            "total_matches": matches_n,
            "wins": wins_n,
            "losses": matches_n - wins_n,
            "win_rate": f"{round(wins_n/matches_n*100,1)}%",
            "icon": f"hero_images/{user.profile_hero_code}.png"
        }
        
        rank_history = [{
            "date": "",
            "rank": match.points_after_match
        } for match in matches.matches]
        
        def create_picks_list(picks_list):
            picks_dicts = []
            
            picks = matches.get_all_own_pick_counts()
            wins = matches.get_all_own_pick_win_counts()
            matchups = matches.get_all_matchup_counts()
            matchups_wins = matches.get_all_matchup_win_counts()
            
            for code in picks_list:
                
                matchups = matches.get_matchup_counts(code)
                matchups_wins = matches.get_matchup_win_counts(code)
                allies = matches.get_ally_counts(code)
                allies_wins = matches.get_ally_win_counts(code)
                allies_winrate = {}
                for hero_code in allies.keys():
                    if hero_code != "total":
                        allies_winrate[hero_code] = (allies_wins[hero_code] + sum(match_result_vector)) / (allies[hero_code] + len(match_result_vector))
                allies_winrate = Counter(allies_winrate)
                matchup_winrate = {}
                for hero_code in matchups.keys():
                    if hero_code != "total":
                        matchup_winrate[hero_code] = (matchups_wins[hero_code] + sum(match_result_vector)) / (matchups[hero_code] + len(match_result_vector))
                matchup_winrate = Counter(matchup_winrate)
                
                best_allies = allies_winrate.most_common(3)
                worst_allies = n_lowest_winrates(allies_winrate, 3)
                best_enemies = matchup_winrate.most_common(3)
                worst_enemies = n_lowest_winrates(matchup_winrate, 3)
                picks_dicts.append({
                    "name": hero_list.get_hero_by_code(code).name,
                    "icon": f"{code}.png",
                    "wins": wins[code],
                    "losses": picks[code] - wins[code],
                    "best_allies": [
                        {"name": hero_list.get_hero_by_code(ally[0]).name, "icon": f"{ally[0]}.png", "wins": allies_wins[ally[0]], "losses": allies[ally[0]] - allies_wins[ally[0]]}
                    for ally in best_allies],
                    "worst_allies": [
                        {"name": hero_list.get_hero_by_code(ally[0]).name, "icon": f"{ally[0]}.png", "wins": allies_wins[ally[0]], "losses": allies[ally[0]] - allies_wins[ally[0]]}
                    for ally in worst_allies],
                    "best_enemies": [
                        {"name": hero_list.get_hero_by_code(enemy[0]).name, "icon": f"{enemy[0]}.png", "wins": matchups_wins[enemy[0]], "losses": matchups[enemy[0]] - matchups_wins[enemy[0]]}
                    for enemy in best_enemies],
                    "worst_enemies": [
                        {"name": hero_list.get_hero_by_code(enemy[0]).name, "icon": f"{enemy[0]}.png", "wins": matchups_wins[enemy[0]], "losses": matchups[enemy[0]] - matchups_wins[enemy[0]]}
                    for enemy in worst_enemies]
                })
            return picks_dicts
        
        def create_enemies_list(enemies_list):
            picks_dicts = []
            enemy_picks = matches.get_all_enemy_pick_counts()
            enemy_wins_against = matches.get_all_enemy_pick_win_against_counts()
            
            for code in enemies_list:
                picks_dicts.append({
                    "name": hero_list.get_hero_by_code(code).name,
                    "icon": f"{code}.png",
                    "wins": enemy_wins_against[code],
                    "losses": enemy_picks[code] - enemy_wins_against[code]
                })
            return picks_dicts
        
        best_picks_list = create_picks_list([x[0] for x in matchup_winrate.most_common(10)])
        worst_picks_list = create_picks_list([x[0] for x in n_lowest_winrates(matchup_winrate, 10)])
        best_enemies_list = create_enemies_list([x[0] for x in enemy_pick_winrate.most_common(10)])
        worst_enemies_list = create_enemies_list([x[0] for x in n_lowest_winrates(enemy_pick_winrate, 10)])
        
    else:
        match_summary = {
            "username": username,
            "server": server,
            "point": user.points,
            "total_matches": 100,
            "wins": 50,
            "losses": 50,
            "win_rate": "50%",
            "icon": f"hero_images/{user.profile_hero_code}.png"
        }
        rank_history = {}
        best_picks_list = {}
        worst_picks_list = {}
        best_enemies_list = {}
        worst_enemies_list = {}
    return render_template("summary.html", 
                           summary=match_summary, 
                           rank_history=rank_history, 
                           best_picks=best_picks_list, 
                           worst_picks=worst_picks_list, 
                           best_enemies=best_enemies_list,
                           worst_enemies=worst_enemies_list
                           )

@app.route("/suggest")
def suggest():
    query = request.args.get("q", "").lower()
    suggestions = name_autocomplete(query)
    return jsonify(suggestions)

@app.route("/legenddata")
def legenddata():
    global legend_data, legend_data_update_time, nmf, transformed_legend_picks
    if twelve_hours_from_last_update(legend_data_update_time):
        legend_data, legend_data_update_time, nmf, transformed_legend_picks = update_legend_data()
        
    presence = Counter(legend_data["presence"])
    match_results = legend_data["match_result_vector"]
    
    picks = Counter(legend_data["picks"])
    wins = Counter(legend_data["wins"])

    early_picks = Counter(legend_data["early_picks"])
    early_picks_wins = Counter(legend_data["early_picks_wins"])

    third_picks = Counter(legend_data["third_picks"])
    third_picks_wins = Counter(legend_data["third_picks_wins"])

    late_picks = Counter(legend_data["late_picks"])
    late_picks_wins = Counter(legend_data["late_picks_wins"])

    prebans = Counter(legend_data["prebans"])
    prebans_wins = Counter(legend_data["prebans_wins"])

    first_picks = Counter(legend_data["first_picks"])
    first_picks_wins = Counter(legend_data["first_picks_wins"])
    
    winrate = get_predicted_winrate(picks, wins, int(sum(wins.values())/5), int(sum(picks.values())/5))
    winrate_early_picks = get_predicted_winrate(early_picks, early_picks_wins, int(sum(early_picks_wins.values())/5), int(sum(early_picks.values())/5))
    winrate_third_picks = get_predicted_winrate(third_picks, third_picks_wins, int(sum(third_picks_wins.values())/5), int(sum(third_picks.values())/5))
    winrate_late_picks = get_predicted_winrate(late_picks, late_picks_wins, int(sum(late_picks_wins.values())/5), int(sum(late_picks.values())/5))
    winrate_prebans = get_predicted_winrate(prebans, prebans_wins, int(sum(prebans_wins.values())/5), int(sum(prebans.values())/5))
    winrate_first_picks = get_predicted_winrate(first_picks, first_picks_wins, int(sum(first_picks_wins.values())/5), int(sum(first_picks.values())/5))

    n_games = len(match_results)
    n_wins = sum(match_results)
    
    def create_picks_list(picks, wins, winrate, n):
        result = {
            "best": [
                {
                    "name": hero_list.get_hero_by_code(pick[0]).name, 
                    "icon": f"{pick[0]}.png", 
                    "wins": wins[pick[0]], 
                    "losses": picks[pick[0]] - wins[pick[0]],
                    "winrate": round(100 * wins[pick[0]] / picks[pick[0]], 1)
                 } for pick in winrate.most_common(n)],
            "worst": [
                {
                    "name": hero_list.get_hero_by_code(pick[0]).name, 
                    "icon": f"{pick[0]}.png", 
                    "wins": wins[pick[0]], 
                    "losses": picks[pick[0]] - wins[pick[0]],
                    "winrate": round(100 * wins[pick[0]] / picks[pick[0]], 1)
                } for pick in n_lowest_winrates(winrate, n)]
        }
        return result
    
    return render_template("legenddata.html",
                           general_stats={"matches": n_games, "wins": n_wins, "losses": n_games-n_wins, "winrate": round(100*n_wins/n_games,1)}, 
                           general_data=create_picks_list(picks, wins, winrate, 5),
                           presence_data=[{
                                        "name": hero_list.get_hero_by_code(pick[0]).name, 
                                        "icon": f"{pick[0]}.png",
                                        "presence_amount": pick[1],
                                        "presence": round(pick[1] / n_games * 100, 1)
                                    } for pick in presence.most_common(10)],
                           first_pick_data=create_picks_list(first_picks, first_picks_wins, winrate_first_picks, 5),
                           early_pick_data=create_picks_list(early_picks, early_picks_wins, winrate_early_picks, 5),
                           third_pick_data=create_picks_list(third_picks, third_picks_wins, winrate_third_picks, 5),
                           late_pick_data=create_picks_list(late_picks, late_picks_wins, winrate_late_picks, 5),
                           preban_data=create_picks_list(prebans, prebans_wins, winrate_prebans, 5)
                           )

@app.route("/tierlist")
def tierlist():
    classes = {"manauser": "soulweaver", "mage": "mage", "knight": "knight", "warrior": "warrior", "ranger": "ranger", "assassin": "thief"}
    elements = {"wind": "earth", "ice": "ice", "fire": "fire", "light": "light", "dark": "dark"}
    characters = [
        {"src": f"static/hero_images/{hero.code}.png", "name": hero.name, "code": hero.code, "element": elements.get(hero.element, ""), "class": classes.get(hero.role, "")} for hero in hero_list.hero_list
    ]
    return render_template("tierlist.html", characters=characters)

if __name__ == "__main__":
    app.run(debug=True)