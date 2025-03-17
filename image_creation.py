from PIL import Image
import matplotlib.pyplot as plt
from pylab import gcf
import numpy as np
import io
import matplotlib.gridspec as gridspec
import math
from functions import *
from match_data import *
import json
from hero_data import *

def n_lowest_winrates(counter:Counter, n:int):
    counter = dict(counter)
    for key in counter.keys():
        counter[key] = 1 - counter[key]
    counter = Counter(counter)
    return counter.most_common(5)

def get_predicted_winrate(picks:Counter, wins:Counter, wins_total:int, matches_total:int) -> Counter:
    winrate = {}
    for hero_code in picks.keys():
        if hero_code != "total":
            winrate[hero_code] = (wins[hero_code] + wins_total) / (picks[hero_code] + matches_total)
    return Counter(winrate)

def create_hero_analysis_image(user_id:str, server:str, target_hero_code:str, hero_data:HeroList, darkmode:bool=False) -> tuple[np.ndarray, int, int, MatchHistory]:
    response = get_match_data_by_user_id(user_id, server)
    allies = allies_wins = matchups = matchups_wins = Counter([])
    match_result_vector = []
    matches = MatchHistory([])
    if response.status_code == 200:
        match_list = response.json()["result_body"]["battle_list"]
        matches = MatchHistory([Match(match, hero_data) for match in match_list])
        matchups = matches.get_matchup_counts()[target_hero_code]
        matchups_wins = matches.get_matchup_win_counts()[target_hero_code]
        allies = matches.get_ally_counts()[target_hero_code]
        allies_wins = matches.get_ally_win_counts()[target_hero_code]
        match_result_vector = matches.get_match_result_vector()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    if len(allies.keys()) == 0:
        return None, None, None, None
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
    
    fig, axes = plt.subplots(nrows=4, ncols=6, figsize=(10, 10), gridspec_kw={'width_ratios': [2, 1, 1, 1, 1, 1]})
    textcol = "#000000"
    if darkmode:
        fig.set_facecolor("#313338")
        textcol = "#ffffff"
    fontsize_s = 18

    axes[0, 0].text(1.0, 1.2, f"{hero_data.get_hero_by_code(target_hero_code).name}", fontsize=40, va='center', transform=axes[0, 0].transAxes, color=textcol)
    axes[0, 0].text(-0.5, 0.5, "Best allies", fontsize=24, va='center', transform=axes[0, 0].transAxes, color=textcol)
    axes[0, 0].axis('off')
    best_allies = allies_winrate.most_common(5)
    for i in range(5):
        if i<len(best_allies):
            icon = get_hero_img(best_allies[i][0])
            axes[0, i+1].imshow(icon)
            axes[0, i+1].text(0.5, -0.4, f"{allies_wins[best_allies[i][0]]} - {allies[best_allies[i][0]] - allies_wins[best_allies[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[0, i+1].transAxes, color=textcol)
            axes[0, i+1].text(0.5, -0.7, f"{round(100*allies_wins[best_allies[i][0]]/allies[best_allies[i][0]])}%", fontsize=fontsize_s, ha='center', transform=axes[0, i+1].transAxes, color=textcol)
        axes[0, i+1].axis('off')

    axes[1, 0].text(-0.5, 0.5, "Worst allies", fontsize=24, va='center', transform=axes[1, 0].transAxes, color=textcol)
    axes[1, 0].axis('off')
    worst_allies = n_lowest_winrates(allies_winrate, 5)
    for i in range(5):
        if i<len(worst_allies):
            icon = get_hero_img(worst_allies[i][0])
            axes[1, i+1].imshow(icon)
            axes[1, i+1].text(0.5, -0.4, f"{allies_wins[worst_allies[i][0]]} - {allies[worst_allies[i][0]] - allies_wins[worst_allies[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[1, i+1].transAxes, color=textcol)
            axes[1, i+1].text(0.5, -0.7, f"{round(100*allies_wins[worst_allies[i][0]]/allies[worst_allies[i][0]])}%", fontsize=fontsize_s, ha='center', transform=axes[1, i+1].transAxes, color=textcol)
        axes[1, i+1].axis('off')

    axes[2, 0].text(-0.5, 0.5, "Best matchups", fontsize=24, va='center', transform=axes[2, 0].transAxes, color=textcol)
    axes[2, 0].axis('off')
    best_enemies = matchup_winrate.most_common(5)
    for i in range(5):
        if i<len(best_enemies):
            icon = get_hero_img(best_enemies[i][0])
            axes[2, i+1].imshow(icon)
            axes[2, i+1].text(0.5, -0.4, f"{matchups_wins[best_enemies[i][0]]} - {matchups[best_enemies[i][0]] - matchups_wins[best_enemies[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[2, i+1].transAxes, color=textcol)
            axes[2, i+1].text(0.5, -0.7, f"{round(100*matchups_wins[best_enemies[i][0]]/matchups[best_enemies[i][0]])}%", fontsize=fontsize_s, ha='center', transform=axes[2, i+1].transAxes, color=textcol)
        axes[2, i+1].axis('off')

    axes[3, 0].text(-0.5, 0.5, "Worst matchups", fontsize=24, va='center', transform=axes[3, 0].transAxes, color=textcol)
    axes[3, 0].axis('off')
    worst_enemies = n_lowest_winrates(matchup_winrate, 5)
    for i in range(5):
        if i<len(worst_enemies):
            icon = get_hero_img(worst_enemies[i][0])
            axes[3, i+1].imshow(icon)
            axes[3, i+1].text(0.5, -0.4, f"{matchups_wins[worst_enemies[i][0]]} - {matchups[worst_enemies[i][0]] - matchups_wins[worst_enemies[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[3, i+1].transAxes, color=textcol)
            axes[3, i+1].text(0.5, -0.7, f"{round(100*matchups_wins[worst_enemies[i][0]]/matchups[worst_enemies[i][0]])}%", fontsize=fontsize_s, ha='center', transform=axes[3, i+1].transAxes, color=textcol)
        axes[3, i+1].axis('off')

    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    plt.close('all')
    return Image.open(buf), matches.get_matchup_counts()[target_hero_code]["total"], matches.get_matchup_win_counts()[target_hero_code]["total"], matches

def create_match_summary_image(user_id:str, server:str, hero_data:HeroList, darkmode:bool=False) -> tuple[np.ndarray, MatchHistory]:
    response = get_match_data_by_user_id(user_id, server)
    picks = wins = enemy_picks = enemy_wins = prebans = first_picks = matchups = matchups_wins = Counter([])
    match_result_vector = []
    matches = MatchHistory([])
    if response.status_code == 200:
        match_list = response.json()["result_body"]["battle_list"]
        if len(match_list) <= 5:
            return None, None  
        matches = MatchHistory([Match(match, hero_data) for match in match_list])
        picks = matches.get_all_own_pick_counts()
        wins = matches.get_all_own_pick_win_counts()
        enemy_picks = matches.get_all_enemy_pick_counts()
        enemy_wins = matches.get_all_enemy_pick_win_against_counts()
        prebans = matches.get_all_own_preban_counts()
        first_picks = matches.get_all_own_first_pick_counts()
        matchups = matches.get_matchup_counts()
        matchups_wins = matches.get_matchup_win_counts()
        match_result_vector = matches.get_match_result_vector()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)  
    
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

    fig, axes = plt.subplots(nrows=8, ncols=6, figsize=(10, 10), gridspec_kw={'width_ratios': [1.8, 1, 1, 1, 1, 1]})
    fig.subplots_adjust(hspace=1)
    fontsize_s = 16
    textcol = "#000000"
    if darkmode:
        fig.set_facecolor("#313338")
        textcol = "#ffffff"
    axes[1, 0].text(-0.5, 0.5, "Picks", fontsize=24, va='center', transform=axes[1, 0].transAxes, color=textcol)

    axes[1, 0].axis('off')
    axes[0, 0].plot([0, 1], [0.17, 0.17], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.275, 0.275], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.375, 0.375], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.48, 0.48], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.585, 0.585], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.685, 0.685], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.79, 0.79], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)

    axes[0, 0].axis('off')
    axes[0, 1].axis('off')
    axes[0, 2].axis('off')
    axes[0, 3].axis('off')
    axes[0, 4].axis('off')
    axes[0, 5].axis('off')
    axes[0, 0].text(-0.5, 0.5, "Winrate", fontsize=24, va='center', transform=axes[0, 0].transAxes, color=textcol)

    gs = gridspec.GridSpec(8, 6, figure=fig)
    ax2 = fig.add_subplot(gs[0:2, 0:2])
    ax = fig.add_subplot(gs[0:2, 2:7])
    ax.axis("off")
    ax2.axis("off")
    wr_graph = create_winrate_graph(match_result_vector)
    wr_min = int(math.floor(min(wr_graph)*20)/2)
    wr_max = int(math.ceil(max(wr_graph)*20)/2)
    ax.plot(range(len(wr_graph)), wr_graph, color=textcol, lw=2)
    ax.plot(range(len(wr_graph)), [0.5]*len(wr_graph), color="red", lw=1)
    ax.plot(range(len(wr_graph)), [((wr_max/10.0))]*len(wr_graph), color=textcol, lw=1)
    ax.plot(range(len(wr_graph)), [((wr_min/10.0))]*len(wr_graph), color=textcol, lw=1)
    ax2.text(0.9, 0.55, f"{wr_min*10}%", fontsize=16, color=textcol)
    ax2.text(0.9, 1.35, f"{wr_max*10}%", fontsize=16, color=textcol)

    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0 + 0.09, pos.width, pos.height*0.9])

    top_picks = picks.most_common(5)
    
    for i in range(5):
        if i<len(top_picks):
            icon = get_hero_img(top_picks[i][0])
            axes[1, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{top_picks[i][1]}", fontsize=fontsize_s+2, ha='center', transform=axes[1, i+1].transAxes, color=textcol)
        axes[1, i+1].axis('off')

    axes[2, 0].text(-0.5, 0.5, "First picks", fontsize=24, va='center', transform=axes[2, 0].transAxes, color=textcol)
    axes[2, 0].axis('off')
    top_first_picks = first_picks.most_common(5)
    for i in range(5):
        if i<len(top_first_picks):
            icon = get_hero_img(top_first_picks[i][0])
            axes[2, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{top_first_picks[i][1]}", fontsize=fontsize_s+2, ha='center', transform=axes[2, i+1].transAxes, color=textcol)
        axes[2, i+1].axis('off')

    axes[3, 0].text(-0.5, 0.5, "Prebans", fontsize=24, va='center', transform=axes[3, 0].transAxes, color=textcol)
    axes[3, 0].axis('off')
    top_prebans = prebans.most_common(5)
    for i in range(5):
        if i<len(top_prebans):
            icon = get_hero_img(top_prebans[i][0])
            axes[3, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{top_prebans[i][1]}", fontsize=fontsize_s+2, ha='center', transform=axes[3, i+1].transAxes, color=textcol)
        axes[3, i+1].axis('off')


    axes[4, 0].text(-0.5, 0.5, "Best picks", fontsize=24, va='center', transform=axes[4, 0].transAxes, color=textcol)
    axes[4, 0].axis('off')
    best_picks = matchup_winrate.most_common(5)
    for i in range(5):
        if i<len(best_picks):
            icon = get_hero_img(best_picks[i][0])
            axes[4, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{wins[best_picks[i][0]]}-{picks[best_picks[i][0]]-wins[best_picks[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[4, i+1].transAxes, color=textcol)
        axes[4, i+1].axis('off')

    axes[5, 0].text(-0.5, 0.5, "Worst picks", fontsize=24, va='center', transform=axes[5, 0].transAxes, color=textcol)
    axes[5, 0].axis('off')
    
    worst_picks = n_lowest_winrates(matchup_winrate, 5)
    for i in range(5):
        if i<len(worst_picks):
            icon = get_hero_img(worst_picks[i][0])
            axes[5, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{wins[worst_picks[i][0]]}-{picks[worst_picks[i][0]]-wins[worst_picks[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[5, i+1].transAxes, color=textcol)
        axes[5, i+1].axis('off')

    axes[6, 0].text(-0.5, 0.5, "Best matchups", fontsize=24, va='center', transform=axes[6, 0].transAxes, color=textcol)
    axes[6, 0].axis('off')
    best_matchups = enemy_pick_winrate.most_common(5)
    for i in range(5):
        if i<len(best_matchups):
            icon = get_hero_img(best_matchups[i][0])
            axes[6, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{enemy_wins[best_matchups[i][0]]}-{enemy_picks[best_matchups[i][0]]-enemy_wins[best_matchups[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[6, i+1].transAxes, color=textcol)
        axes[6, i+1].axis('off')

    axes[7, 0].text(-0.5, 0.5, "Worst matchups", fontsize=24, va='center', transform=axes[7, 0].transAxes, color=textcol)
    axes[7, 0].axis('off')
    worst_matchups = n_lowest_winrates(enemy_pick_winrate, 5)
    for i in range(5):
        if i<len(worst_matchups):
            icon = get_hero_img(worst_matchups[i][0])
            axes[7, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{enemy_wins[worst_matchups[i][0]]}-{enemy_picks[worst_matchups[i][0]]-enemy_wins[worst_matchups[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[7, i+1].transAxes, color=textcol)
        axes[7, i+1].axis('off')

    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    plt.close('all')
    return Image.open(buf), matches
    

def create_trios_image(user_id:str, server:str, hero_data:HeroList, darkmode:bool=False) -> tuple[np.ndarray, MatchHistory]:
    response = get_match_data_by_user_id(user_id, server)
    trios_picks = trios_wins = Counter([])
    match_result_vector = []
    matches = MatchHistory([])
    if response.status_code == 200:
        match_list = response.json()["result_body"]["battle_list"]
        matches = MatchHistory([Match(match, hero_data) for match in match_list])
        match_result_vector = matches.get_match_result_vector()
        trios_picks = matches.get_own_trios_picks()
        trios_wins = matches.get_own_trios_wins()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    trios_winrate = {}
    for hero_code in trios_picks.keys():
        if hero_code != "total":
            trios_winrate[hero_code] = (trios_wins.get(hero_code, 0) + sum(match_result_vector)) / (trios_picks.get(hero_code, 0) + len(match_result_vector))
    trios_winrate = Counter(trios_winrate)
    fig, axes = plt.subplots(nrows=10, ncols=5, figsize=(10, 10), gridspec_kw={'width_ratios': [1.5, 1.5, 1.5, 1.5, 1.5]})
    textcol = "#000000"
    if darkmode:
        fig.set_facecolor("#313338")
        textcol = "#ffffff"

    fontsize_s = 18
    axes[0, 0].text(-0.5, 0.5, "Best trios", fontsize=30, va='center', transform=axes[0, 0].transAxes, color=textcol)
    axes[0, 0].plot([0.05, 0.95], [0.495, 0.495], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0.30, 0.90], [0.575, 0.575], color=textcol, lw=1,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0.30, 0.90], [0.655, 0.655], color=textcol, lw=1,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0.30, 0.90], [0.730, 0.730], color=textcol, lw=1,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0.30, 0.90], [0.810, 0.810], color=textcol, lw=1,transform=gcf().transFigure, clip_on=False)

    axes[0, 0].plot([0.30, 0.90], [0.418, 0.418], color=textcol, lw=1,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0.30, 0.90], [0.340, 0.340], color=textcol, lw=1,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0.30, 0.90], [0.262, 0.262], color=textcol, lw=1,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0.30, 0.90], [0.182, 0.182], color=textcol, lw=1,transform=gcf().transFigure, clip_on=False)
    best_trios = trios_winrate.most_common(5)

    for i in range(len(best_trios)):
        icon = get_hero_img(list(best_trios[i][0])[0])
        axes[i, 1].imshow(icon)
        icon = get_hero_img(list(best_trios[i][0])[1])
        axes[i, 2].imshow(icon)
        icon = get_hero_img(list(best_trios[i][0])[2])
        axes[i, 3].imshow(icon)
        axes[i, 4].text(0.5, 0.3, f"{trios_wins[best_trios[i][0]]}-{trios_picks[best_trios[i][0]]-trios_wins[best_trios[i][0]]} ({round(100*trios_wins[best_trios[i][0]]/trios_picks[best_trios[i][0]])}%)", fontsize=fontsize_s+2, ha='center', transform=axes[i, 4].transAxes, color=textcol)
        axes[i, 0].axis('off')
        axes[i, 1].axis('off')
        axes[i, 2].axis('off')
        axes[i, 3].axis('off')
        axes[i, 4].axis('off')

    trios_winrate = dict(trios_winrate)
    for key in trios_winrate.keys():
        trios_winrate[key] = 100 - trios_winrate[key]
    trios_winrate = Counter(trios_winrate)
    worst_trios = trios_winrate.most_common(5)
    axes[5, 0].text(-0.5, 0.5, "Worst trios", fontsize=30, va='center', transform=axes[5, 0].transAxes, color=textcol)
    for i in range(5):
        icon = get_hero_img(list(worst_trios[i][0])[0])
        axes[i+5, 1].imshow(icon)
        icon = get_hero_img(list(worst_trios[i][0])[1])
        axes[i+5, 2].imshow(icon)
        icon = get_hero_img(list(worst_trios[i][0])[2])
        axes[i+5, 3].imshow(icon)
        axes[i+5, 4].text(0.5, 0.3, f"{trios_wins[worst_trios[i][0]]}-{trios_picks[worst_trios[i][0]]-trios_wins[worst_trios[i][0]]} ({round(100*trios_wins[worst_trios[i][0]]/trios_picks[worst_trios[i][0]])}%)", fontsize=fontsize_s+2, ha='center', transform=axes[i+5, 4].transAxes, color=textcol)
        axes[i+5, 0].axis('off')
        axes[i+5, 1].axis('off')
        axes[i+5, 2].axis('off')
        axes[i+5, 3].axis('off')
        axes[i+5, 4].axis('off')

    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    plt.close('all')
    return Image.open(buf), matches

def create_legend_data_summary_image(darkmode:bool=False) -> np.ndarray:
    with open("data/legend_data.json", "r") as json_file:
        legend_data = json.load(json_file)

    presence = Counter(legend_data["presence"])

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

    fig, axes = plt.subplots(nrows=8, ncols=6, figsize=(10, 10), gridspec_kw={'width_ratios': [1.8, 1, 1, 1, 1, 1]})
    fig.subplots_adjust(hspace=1)
    fontsize_s = 16
    textcol = "#000000"
    if darkmode:
        fig.set_facecolor("#313338")
        textcol = "#ffffff"
        
    axes[0, 0].plot([0, 1], [0.17, 0.17], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.275, 0.275], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.375, 0.375], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.48, 0.48], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.585, 0.585], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.685, 0.685], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)


    axes[0, 0].axis('off')
    axes[0, 1].axis('off')
    axes[0, 2].axis('off')
    axes[0, 3].axis('off')
    axes[0, 4].axis('off')
    axes[0, 5].axis('off')
    axes[0, 0].text(1.0, 1.0, "Legend data", fontsize=46, va='center', transform=axes[0, 0].transAxes, color=textcol)

    gs = gridspec.GridSpec(8, 6, figure=fig)
    ax2 = fig.add_subplot(gs[0:2, 0:2])
    ax = fig.add_subplot(gs[0:2, 2:7])
    ax.axis("off")
    ax2.axis("off")

    axes[1, 0].text(-0.5, 0.5, "Best picks", fontsize=24, va='center', transform=axes[1, 0].transAxes, color=textcol)
    axes[1, 0].axis('off')
    top_picks = winrate.most_common(5)
    for i in range(5):
        if i<len(top_picks):
            icon = get_hero_img(top_picks[i][0])
            axes[1, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{round(100*wins[top_picks[i][0]]/picks[top_picks[i][0]],1)}%", fontsize=fontsize_s+2, ha='center', transform=axes[1, i+1].transAxes, color=textcol)
        axes[1, i+1].axis('off')

    axes[2, 0].text(-0.5, 0.5, "Best early picks", fontsize=24, va='center', transform=axes[2, 0].transAxes, color=textcol)
    axes[2, 0].axis('off')
    top_early_picks = winrate_early_picks.most_common(5)
    for i in range(5):
        if i<len(top_early_picks):
            icon = get_hero_img(top_early_picks[i][0])
            axes[2, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{round(100*early_picks_wins[top_early_picks[i][0]]/early_picks[top_early_picks[i][0]],1)}%", fontsize=fontsize_s+2, ha='center', transform=axes[2, i+1].transAxes, color=textcol)
        axes[2, i+1].axis('off')

    axes[3, 0].text(-0.5, 0.5, "Best third picks", fontsize=24, va='center', transform=axes[3, 0].transAxes, color=textcol)
    axes[3, 0].axis('off')
    top_third_picks = winrate_third_picks.most_common(5)
    for i in range(5):
        if i<len(top_third_picks):
            icon = get_hero_img(top_third_picks[i][0])
            axes[3, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{round(100*third_picks_wins[top_third_picks[i][0]]/third_picks[top_third_picks[i][0]],1)}%", fontsize=fontsize_s+2, ha='center', transform=axes[3, i+1].transAxes, color=textcol)
        axes[3, i+1].axis('off')

    axes[4, 0].text(-0.5, 0.5, "Best late picks", fontsize=24, va='center', transform=axes[4, 0].transAxes, color=textcol)
    axes[4, 0].axis('off')
    top_late_picks = winrate_late_picks.most_common(5)
    for i in range(5):
        if i<len(top_late_picks):
            icon = get_hero_img(top_late_picks[i][0])
            axes[4, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{round(100*late_picks_wins[top_late_picks[i][0]]/late_picks[top_late_picks[i][0]],1)}%", fontsize=fontsize_s+2, ha='center', transform=axes[4, i+1].transAxes, color=textcol)
        axes[4, i+1].axis('off')

    axes[5, 0].text(-0.5, 0.5, "Best prebans", fontsize=24, va='center', transform=axes[5, 0].transAxes, color=textcol)
    axes[5, 0].axis('off')
    
    top_prebans = winrate_prebans.most_common(5)
    for i in range(5):
        if i<len(top_prebans):
            icon = get_hero_img(top_prebans[i][0])
            axes[5, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{round(100*prebans_wins[top_prebans[i][0]]/prebans[top_prebans[i][0]],1)}%", fontsize=fontsize_s+2, ha='center', transform=axes[5, i+1].transAxes, color=textcol)
        axes[5, i+1].axis('off')

    axes[6, 0].text(-0.5, 0.5, "Best first picks", fontsize=24, va='center', transform=axes[6, 0].transAxes, color=textcol)
    axes[6, 0].axis('off')
    top_first_picks = winrate_first_picks.most_common(5)
    for i in range(5):
        if i<len(top_first_picks):
            icon = get_hero_img(top_first_picks[i][0])
            axes[6, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{round(100*first_picks_wins[top_first_picks[i][0]]/first_picks[top_first_picks[i][0]],1)}%", fontsize=fontsize_s+2, ha='center', transform=axes[6, i+1].transAxes, color=textcol)
        axes[6, i+1].axis('off')

    axes[7, 0].text(-0.5, 0.5, "Highest presence", fontsize=24, va='center', transform=axes[7, 0].transAxes, color=textcol)
    axes[7, 0].axis('off')
    top_presence = presence.most_common(5)
    for i in range(5):
        if i<len(top_presence):
            icon = get_hero_img(top_presence[i][0])
            axes[7, i+1].imshow(icon)
            axes[0, i+1].text(0.6, -0.6, f"{round(100*presence[top_presence[i][0]]/(sum(picks.values())/5),1)}%", fontsize=fontsize_s+2, ha='center', transform=axes[7, i+1].transAxes, color=textcol)
        axes[7, i+1].axis('off')

    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    plt.close('all')
    return Image.open(buf)

def create_legend_data_image_one_hero(target_hero_code:str, target_hero_name:str, darkmode:bool=False) -> tuple[np.ndarray, bool]:
    with open("data/legend_data.json", "r") as json_file:
        legend_data = json.load(json_file)

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
    
    if picks[target_hero_code] == 0:
        fig, axes = plt.subplots(nrows=8, ncols=6, figsize=(10, 10), gridspec_kw={'width_ratios': [1.8, 1, 1, 1, 1, 1]})
        buf = io.BytesIO()
        fig.savefig(buf)
        buf.seek(0)
        plt.close('all')
        return np.zeros((10,10)), False
    
    matches_n = int(sum(picks.values())/5)
    wins_n = int(sum(wins.values())/5)
    
    fig, axes = plt.subplots(nrows=8, ncols=6, figsize=(10, 10), gridspec_kw={'width_ratios': [1.8, 1, 1, 1, 1, 1]})
    fig.subplots_adjust(hspace=1)
    fontsize_s = 16
    fontsize_m = 24
    textcol = "#000000"
    if darkmode:
        fig.set_facecolor("#313338")
        textcol = "#ffffff"
        
    axes[0, 0].plot([0, 1], [0.17, 0.17], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.275, 0.275], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.375, 0.375], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.48, 0.48], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.585, 0.585], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)
    axes[0, 0].plot([0, 1], [0.685, 0.685], color=textcol, lw=2,transform=gcf().transFigure, clip_on=False)


    axes[0, 0].axis('off')
    axes[0, 1].axis('off')
    axes[0, 2].axis('off')
    axes[0, 3].axis('off')
    axes[0, 4].axis('off')
    axes[0, 5].axis('off')
    axes[0, 0].text(0.5+(max((15-len(target_hero_name))/10, 0)), 1.5, f"{target_hero_name}", fontsize=46, va='center', transform=axes[0, 0].transAxes, color=textcol)
    axes[0, 0].text(1.2, 0.6, "Legend data", fontsize=32, va='center', transform=axes[0, 0].transAxes, color=textcol)
    
    
    gs = gridspec.GridSpec(8, 6, figure=fig)
    ax2 = fig.add_subplot(gs[0:2, 0:2])
    ax = fig.add_subplot(gs[0:2, 2:7])
    ax.axis("off")
    ax2.axis("off")
    
    axes[1, 0].text(-0.5, 0.2, "Winrate", fontsize=fontsize_m+2, va='center', color=textcol)
    axes[1, 0].axis('off')
    for i in range(5):
        axes[1, i+1].axis('off')
    target_winrate = round(100*wins[target_hero_code]/picks[target_hero_code],1)
    legend_winrate = round(100*wins_n/matches_n,1)
    axes[1, 1].text(0.1, 0.4, f"{target_winrate}%", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[1, 2].text(0.2, 0.4, f"({wins[target_hero_code]}-{picks[target_hero_code]})", fontsize=fontsize_s+2, ha='center', color=textcol)
    if target_winrate>legend_winrate:
        axes[1, 2].text(1.3, -0.3, f"{round(target_winrate-legend_winrate,1)}% higher than average legend winrate ({legend_winrate}%)", fontsize=fontsize_s, ha='center', color=textcol)
    else:
        axes[1, 2].text(1.3, -0.3, f"{round(legend_winrate-target_winrate,1)}% lower than average legend winrate ({legend_winrate}%)", fontsize=fontsize_s, ha='center', color=textcol)

    axes[2, 0].text(-0.5, 0.2, "Pickrate", fontsize=fontsize_m+2, va='center', color=textcol)
    axes[2, 0].axis('off')
    for i in range(5):
        axes[2, i+1].axis('off')
    axes[2, 1].text(0.1, 0.4, f"{round(100*picks[target_hero_code]/matches_n,1)}%", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[2, 2].text(0.6, -0.3, f"Picked in {picks[target_hero_code]} out of {matches_n} matches.", fontsize=fontsize_s, ha='center', color=textcol)

    axes[3, 0].text(-0.5, 0.2, "Preban", fontsize=fontsize_m+2, va='center',  color=textcol)
    axes[3, 0].axis('off')
    for i in range(5):
        axes[3, i+1].axis('off')
    axes[3, 1].text(0, 0.4, f"{round(100*prebans[target_hero_code]/matches_n,1)}%", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[3, 1].text(0.8, 0.4, f" - ", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[3, 4].text(0, 0.4, f"Prebanned in {prebans[target_hero_code]} out of {matches_n} matches.", fontsize=fontsize_s+2, ha='center', color=textcol)
    if first_picks[target_hero_code] != 0:
        axes[3, 1].text(1.0, -0.3, f"Preban winrate: {round(100*prebans_wins[target_hero_code]/prebans[target_hero_code],1)}%", fontsize=fontsize_s, ha='center', color=textcol)
    else:
        axes[3, 1].text(1.0, -0.3, f"Preban winrate: 0%", fontsize=fontsize_s, ha='center', color=textcol)

    axes[4, 0].text(-0.5, 0.2, "First pick", fontsize=fontsize_m+2, va='center', color=textcol)
    axes[4, 0].axis('off')
    for i in range(5):
        axes[4, i+1].axis('off')
    axes[4, 1].text(0, 0.4, f"{round(100*first_picks[target_hero_code]/matches_n,1)}%", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[4, 1].text(0.8, 0.4, f" - ", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[4, 4].text(0, 0.4, f"First picked in {first_picks[target_hero_code]} out of {matches_n} matches.", fontsize=fontsize_s+2, ha='center', color=textcol)
    if first_picks[target_hero_code] != 0:
        axes[4, 1].text(1.0, -0.3, f"First pick winrate: {round(100*first_picks_wins[target_hero_code]/first_picks[target_hero_code],1)}%", fontsize=fontsize_s, ha='center', color=textcol)
    else:
        axes[4, 1].text(1.0, -0.3, f"First pick winrate: 0%", fontsize=fontsize_s, ha='center', color=textcol)

    axes[5, 0].text(-0.5, 0.2, "Early pick", fontsize=fontsize_m+2, va='center', color=textcol)
    axes[5, 0].axis('off')
    for i in range(5):
        axes[5, i+1].axis('off')
    axes[5, 1].text(0, 0.4, f"{round(100*early_picks[target_hero_code]/matches_n,1)}%", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[5, 1].text(0.8, 0.4, f" - ", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[5, 4].text(0, 0.4, f"Picked early in {early_picks[target_hero_code]} out of {matches_n} matches.", fontsize=fontsize_s+2, ha='center', color=textcol)
    if early_picks[target_hero_code] != 0:
        axes[5, 1].text(1.0, -0.3, f"Early pick winrate: {round(100*early_picks_wins[target_hero_code]/early_picks[target_hero_code],1)}%", fontsize=fontsize_s, ha='center', color=textcol)
    else:
        axes[5, 1].text(1.0, -0.3, f"Early pick winrate: 0%", fontsize=fontsize_s, ha='center', color=textcol)

    axes[6, 0].text(-0.5, 0.2, "Third pick", fontsize=fontsize_m+2, va='center', color=textcol)
    axes[6, 0].axis('off')
    for i in range(5):
        axes[6, i+1].axis('off')
    axes[6, 1].text(0, 0.4, f"{round(100*third_picks[target_hero_code]/matches_n,1)}%", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[6, 1].text(0.8, 0.4, f" - ", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[6, 4].text(0, 0.4, f"Picked third in {third_picks[target_hero_code]} out of {matches_n} matches.", fontsize=fontsize_s+2, ha='center', color=textcol)
    if third_picks[target_hero_code] != 0:
        axes[6, 1].text(1.0, -0.3, f"Third pick winrate: {round(100*third_picks_wins[target_hero_code]/third_picks[target_hero_code],1)}%", fontsize=fontsize_s, ha='center', color=textcol)
    else:
        axes[6, 1].text(1.0, -0.3, f"Third pick winrate: 0%", fontsize=fontsize_s, ha='center', color=textcol)

    axes[7, 0].text(-0.5, 0.2, "Late pick", fontsize=fontsize_m+2, va='center', color=textcol)
    axes[7, 0].axis('off')
    for i in range(5):
        axes[7, i+1].axis('off')
    axes[7, 1].text(0, 0.4, f"{round(100*late_picks[target_hero_code]/matches_n,1)}%", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[7, 1].text(0.8, 0.4, f" - ", fontsize=fontsize_s+2, ha='center', color=textcol)
    axes[7, 4].text(0, 0.4, f"Picked late in {late_picks[target_hero_code]} out of {matches_n} matches.", fontsize=fontsize_s+2, ha='center', color=textcol)
    if late_picks[target_hero_code] != 0:
        axes[7, 1].text(1.0, -0.3, f"Late pick winrate: {round(100*late_picks_wins[target_hero_code]/late_picks[target_hero_code],1)}%", fontsize=fontsize_s, ha='center', color=textcol)
    else:
        axes[7, 1].text(1.0, -0.3, f"Late pick winrate: 0%", fontsize=fontsize_s, ha='center', color=textcol)

    
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    plt.close('all')
    return Image.open(buf), True

def create_ban_summary_image(user_id:str, server:str, hero_data:HeroList, darkmode:bool=False) -> tuple[np.ndarray, MatchHistory]:
    response = get_match_data_by_user_id(user_id, server)
    own_ban_counts = enemy_ban_counts = own_ban_win_counts = enemy_ban_win_counts = Counter([])
    match_result_vector = []
    matches = MatchHistory([])

    if response.status_code == 200:
        match_list = response.json()["result_body"]["battle_list"]
        matches = MatchHistory([Match(match, hero_data) for match in match_list])
        own_ban_counts = matches.get_all_own_ban_counts()
        enemy_ban_counts = matches.get_all_enemy_ban_counts()
        own_ban_win_counts = matches.get_all_own_ban_win_counts()
        enemy_ban_win_counts = matches.get_all_enemy_ban_win_counts()
        match_result_vector = matches.get_match_result_vector()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

    own_ban_winrate_counts = get_predicted_winrate(own_ban_counts, own_ban_win_counts, sum(match_result_vector), len(match_result_vector))
    enemy_ban_winrate_counts = get_predicted_winrate(enemy_ban_counts, enemy_ban_win_counts, sum(match_result_vector), len(match_result_vector))

    fig, axes = plt.subplots(nrows=4, ncols=6, figsize=(10, 10), gridspec_kw={'width_ratios': [2, 1, 1, 1, 1, 1]})
    textcol = "#000000"
    if darkmode:
        fig.set_facecolor("#313338")
        textcol = "#ffffff"
    fontsize_s = 18

    axes[0, 0].text(1.0, 1.2, f"Ban data", fontsize=40, va='center', transform=axes[0, 0].transAxes, color=textcol)
    axes[0, 0].text(-0.5, 0.4, "Best performance", fontsize=22, va='center', transform=axes[0, 0].transAxes, color=textcol)
    axes[0, 0].text(-0.5, 0.1, "Own hero banned", fontsize=18, va='center', transform=axes[0, 0].transAxes, color=textcol)
    axes[0, 0].axis('off')
    best_own_bans = own_ban_winrate_counts.most_common(5)
    for i in range(5):
        if i<len(best_own_bans):
            icon = get_hero_img(best_own_bans[i][0])
            axes[0, i+1].imshow(icon)
            axes[0, i+1].text(0.5, -0.4, f"{own_ban_win_counts[best_own_bans[i][0]]} - {own_ban_counts[best_own_bans[i][0]] - own_ban_win_counts[best_own_bans[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[0, i+1].transAxes, color=textcol)
            axes[0, i+1].text(0.5, -0.7, f"{round(100*own_ban_win_counts[best_own_bans[i][0]]/own_ban_counts[best_own_bans[i][0]])}%", fontsize=fontsize_s, ha='center', transform=axes[0, i+1].transAxes, color=textcol)
        axes[0, i+1].axis('off')
    
    axes[1, 0].text(-0.5, 0.4, "Worst performance", fontsize=22, va='center', transform=axes[1, 0].transAxes, color=textcol)
    axes[1, 0].text(-0.5, 0.1, "Own hero banned", fontsize=18, va='center', transform=axes[1, 0].transAxes, color=textcol)
    axes[1, 0].axis('off')
    worst_own_bans = n_lowest_winrates(own_ban_winrate_counts, 5)
    for i in range(5):
        if i<len(worst_own_bans):
            icon = get_hero_img(worst_own_bans[i][0])
            axes[1, i+1].imshow(icon)
            axes[1, i+1].text(0.5, -0.4, f"{own_ban_win_counts[worst_own_bans[i][0]]} - {own_ban_counts[worst_own_bans[i][0]] - own_ban_win_counts[worst_own_bans[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[1, i+1].transAxes, color=textcol)
            axes[1, i+1].text(0.5, -0.7, f"{round(100*own_ban_win_counts[worst_own_bans[i][0]]/own_ban_counts[worst_own_bans[i][0]])}%", fontsize=fontsize_s, ha='center', transform=axes[1, i+1].transAxes, color=textcol)
        axes[1, i+1].axis('off')

    axes[2, 0].text(-0.5, 0.4, "Best performance", fontsize=22, va='center', transform=axes[2, 0].transAxes, color=textcol)
    axes[2, 0].text(-0.5, 0.1, "Enemy hero banned", fontsize=18, va='center', transform=axes[2, 0].transAxes, color=textcol)
    axes[2, 0].axis('off')
    best_enemy_bans = enemy_ban_winrate_counts.most_common(5)
    for i in range(5):
        if i<len(best_enemy_bans):
            icon = get_hero_img(best_enemy_bans[i][0])
            axes[2, i+1].imshow(icon)
            axes[2, i+1].text(0.5, -0.4, f"{enemy_ban_win_counts[best_enemy_bans[i][0]]} - {enemy_ban_counts[best_enemy_bans[i][0]] - enemy_ban_win_counts[best_enemy_bans[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[2, i+1].transAxes, color=textcol)
            axes[2, i+1].text(0.5, -0.7, f"{round(100*enemy_ban_win_counts[best_enemy_bans[i][0]]/enemy_ban_counts[best_enemy_bans[i][0]])}%", fontsize=fontsize_s, ha='center', transform=axes[2, i+1].transAxes, color=textcol)
        axes[2, i+1].axis('off')

    axes[3, 0].text(-0.5, 0.4, "Worst performace", fontsize=22, va='center', transform=axes[3, 0].transAxes, color=textcol)
    axes[3, 0].text(-0.5, 0.1, "Enemy hero banned", fontsize=18, va='center', transform=axes[3, 0].transAxes, color=textcol)
    axes[3, 0].axis('off')
    worst_enemy_bans = n_lowest_winrates(enemy_ban_winrate_counts, 5)
    for i in range(5):
        if i<len(worst_enemy_bans):
            icon = get_hero_img(worst_enemy_bans[i][0])
            axes[3, i+1].imshow(icon)
            axes[3, i+1].text(0.5, -0.4, f"{enemy_ban_win_counts[worst_enemy_bans[i][0]]} - {enemy_ban_counts[worst_enemy_bans[i][0]] - enemy_ban_win_counts[worst_enemy_bans[i][0]]}", fontsize=fontsize_s+2, ha='center', transform=axes[3, i+1].transAxes, color=textcol)
            axes[3, i+1].text(0.5, -0.7, f"{round(100*enemy_ban_win_counts[worst_enemy_bans[i][0]]/enemy_ban_counts[worst_enemy_bans[i][0]])}%", fontsize=fontsize_s, ha='center', transform=axes[3, i+1].transAxes, color=textcol)
        axes[3, i+1].axis('off')
 
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)
    plt.close('all')
    return Image.open(buf), matches