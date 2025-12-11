from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands

import os
import random
import io
from datetime import datetime, timedelta, timezone

from update_data import *
from functions import get_match_data_by_user_id, get_season_info
from user_data import *
from image_creation import *
from search_history import *
from hero_data import *
from resource_handler import *

from sklearn.decomposition import NMF
import numpy as np

# Check if required folder structure exists, create if not

if not os.path.exists("data"):
    os.makedirs("data") 
if not os.path.exists("hero_images"):
    os.makedirs("hero_images")   
if not os.path.isfile("data/points.json"):
    with open("data/points.json", "w") as json_file:
        json.dump({}, json_file, indent=4)
  

# Load environmental variable(s)            
load_dotenv()

# Update hero data, check if new image(s) need to be downloaded
hero_popularity = HeroPopularity()
if os.path.isfile("data/hero_popularity.json"):
    hero_popularity.load_popularity()

resource_handler = ResourceHandler()

hero_list = resource_handler.hero_list
hero_dict = hero_list.get_hero_vector_dict()

# Load and update user data, and create a search index
user_data = UserData()
points = Points()
points.load_points()
server_list = ["global", "asia", "jpn", "kor", "eu"]
for server in server_list:
    get_new_userdata(server)
    with open(f"data/epic7_user_world_{server}.json", "r") as json_file:
        server_user_data = json.load(json_file)
        user_data.read_data(server_user_data, server)
user_data.create_search_index()
user_data.load_points(points.points)
# Initiate search history and load if previous data exists
search_history = SearchHistory()
if os.path.exists("data/search_history.json"):
    search_history.load_search_history()
    
image_creation = ImageCreation(resource_handler, user_data)

def update_legend_data() -> tuple[dict, datetime, NMF, np.ndarray]:
    with open("data/legend_data.json", "r") as json_file:
        legend_data = json.load(json_file)
    nmf = NMF(n_components=4, init="nndsvd", random_state=42)
    legend_vectors = np.asarray([vector for vector in legend_data["pick_vectors"].values()]) / 100.0
    return legend_data, datetime.now(), nmf, nmf.fit_transform(legend_vectors)

def twelve_hours_from_last_update(last_update:datetime) -> bool:
    return datetime.now() - last_update >= timedelta(hours=12)

legend_data, legend_data_update_time, nmf, transformed_legend_picks = update_legend_data()

# Load banned users/discord servers
poobrain_set = set()
if os.path.isfile("poobrain.txt"):
    with open('poobrain.txt', 'r') as file:
        for line in file:
            values = line.strip().split(', ')
            poobrain_set.update(values)
        
pooguild_set = set()
if os.path.isfile("pooguilds.txt"):
    with open('pooguilds.txt', 'r') as file:
        for line in file:
            values = line.strip().split(', ')
            pooguild_set.update(values)

def add_n_weeks(time:datetime, n:int) -> datetime:
    i = 1
    now = datetime.now()
    while time + timedelta(days=7*n*i) < now:
        i += 1
    return time + timedelta(days=7*n*i)

def get_next_month_time() -> datetime:
    now = datetime.now(timezone.utc)
    return datetime.fromtimestamp(now.replace(month=(now.month+1)%12, day=1, hour=3, minute=0, second=0, microsecond=0).timestamp())

def get_next_hour(hour:int) -> datetime:
    now = datetime.now(timezone.utc)
    if now.hour >= hour:
        return (now + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
    return now.replace(hour=hour, minute=0, second=0, microsecond=0)

def get_asia_reset_time(time:datetime)->datetime:
    return time - timedelta(hours=9)

def get_global_reset_time(time:datetime)->datetime:
    return time + timedelta(hours=7)

def get_next_time(base:datetime, interval:timedelta) -> datetime:
    now = datetime.now()
    time = base
    while time <= now:
        time += interval
    return time

def get_next_artifact_shop_rotation() -> datetime:
    base = datetime.fromtimestamp(1758164400)
    six_weeks = timedelta(days=42)
    return get_next_time(base, six_weeks)

def get_next_maintenance_time() -> datetime:
    base = datetime.fromtimestamp(1759978800)
    two_weeks = timedelta(days=14)
    return get_next_time(base, two_weeks)

def get_next_sidestory_time() -> datetime:
    base = datetime.fromtimestamp(1759374000)
    two_weeks = timedelta(days=14)
    return get_next_time(base, two_weeks)

def get_next_hot_reset_time() -> datetime:
    base = datetime.fromtimestamp(1759114800)
    two_weeks = timedelta(days=14)
    return get_next_time(base, two_weeks)
    
def get_next_automaton_tower_reset_time() -> datetime:
    base = datetime.fromtimestamp(1759719600)
    two_weeks = timedelta(days=14)
    return get_next_time(base, two_weeks)

# Bot setup

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

TOKEN = os.getenv('TOKEN')
PREFIX = '!!'

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

############
# COMMANDS #
############

from image_creation import *

@tree.command(name="shitpost")
async def shitpost(ctx:discord.Interaction):
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Just read your own message history')
    else:
        shitpost_list = [" In the digital universe of Epic Seven, Traptrix stands tall, embodying the essence of commitment with an astonishing 5000 games per season. Clad in the prestigious legend frame, their motto, no frame no opinion, speaks volumes, underscoring the significance and authority their seasoned expertise lends to the strategic discussions and decisions within the game. As an arbiter of insight and wisdom, Traptrix's every move echoes with the resonant power of their gameplay, a living testament to their dedication to this virtual realm.",
                          "You see that? it's called a legend frame, something you'll never have!", 
                          "Yield pls", 
                          "Idk what you want me to say dude it was his little sister's birthday so the boys surprised him with a frame if that's wintrading lock me tf up", 
                          "Switch to Caerliss's profile card, free wins late in season"]
        response = random.choice(shitpost_list)
        await ctx.response.send_message(response)

@tree.command(name="links", description="List of useful links.")
async def links(ctx:discord.Interaction):
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('https://www.google.com/search?q=am+i+dumb')
    else:
        await ctx.response.send_message("# Official useful links\n[News](<https://page.onstove.com/epicseven/global/list/e7en001?listType=2&direction=latest&page=1>)\n[YouTube (EN)](<https://www.youtube.com/@EpicSeven>)\n[YouTube (JP)](<https://www.youtube.com/@EpicSevenJP>)\n[RTA Match History](<https://epic7.onstove.com/en/gg>)\n[Redeem coupons](<https://epic7.onstove.com/en/coupon>)\n[Redeem Twitch drops](<https://epic7.onstove.com/en/twitchdrops>)\n\n# Unofficial useful links\n[Damage Calculator](<https://e7calc.xyz/>)\n[Fribbels Gear Optimiser](<https://github.com/fribbels/Fribbels-Epic-7-Optimizer>)\n[Fribbels Hero Library](<https://fribbels.github.io/e7/hero-library.html>)\n[CeciliaBot - hero stats, timeline, etc.](<https://ceciliabot.github.io/#/>)\n[Skill Multiplier Spreadsheet](<https://docs.google.com/spreadsheets/d/e/2PACX-1vRWZw_BeIhf32W9UIyPuyrr1VDeBuX6p1Nzxov4-5Pkt5DplChLovysSDN83mGVbsZ0XgYs2FICuRXA/pubhtml>)")       

@tree.command(name="timers", description="Timers for different activities.")
async def timers(ctx:discord.Interaction):
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('https://www.google.com/search?q=am+i+dumb')
    else:
        response = f"# Regular Content\nServer reset times: Global <t:{int(get_next_hour(10).timestamp())}:R> - Europe: <t:{int(get_next_hour(3).timestamp())}:R> - Asia, Japan, Korea: <t:{int(get_next_hour(18).timestamp())}:R>\nAutomaton Tower: Global <t:{int(get_global_reset_time(get_next_automaton_tower_reset_time()).timestamp())}:R> - Europe <t:{int(get_next_automaton_tower_reset_time().timestamp())}:R> - Asia, Japan, Korea <t:{int(get_asia_reset_time(get_next_automaton_tower_reset_time()).timestamp())}:R>\nHall of Trials: Global <t:{int(get_global_reset_time(get_next_hot_reset_time()).timestamp())}:R> - Europe <t:{int(get_next_hot_reset_time().timestamp())}:R> - Asia, Japan, Korea <t:{int(get_asia_reset_time(get_next_hot_reset_time()).timestamp())}:R>\nBiweekly sidestory: <t:{int(get_next_sidestory_time().timestamp())}:R>\nMaintenance: <t:{int(get_next_maintenance_time().timestamp())}:R>\nExpeditions: Global <t:{int(get_global_reset_time(get_next_month_time() - timedelta(hours=5)).timestamp())}:R> - Europe <t:{int((get_next_month_time() - timedelta(hours=5)).timestamp())}:R> - Asia, Japan, Korea <t:{int(get_asia_reset_time(get_next_month_time() - timedelta(hours=5)).timestamp())}:R>\nTrial of Constellations: Global <t:{int(get_global_reset_time(get_next_month_time()).timestamp())}:R> - Europe <t:{int(get_next_month_time().timestamp())}:R> - Asia, Japan, Korea <t:{int(get_asia_reset_time(get_next_month_time()).timestamp())}:R>\n\n# Shops \nCoin shops: <t:{int(get_next_month_time().timestamp())}:R>\nPowder shop: <t:{int(get_next_artifact_shop_rotation().timestamp())}:R>"
        await ctx.response.send_message(response)       


@tree.command(name="seasoninfo", description="Basic information about the current RTA season.")
async def shitpost(ctx:discord.Interaction):
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('https://www.google.com/search?q=am+i+dumb')
    else:
        season_info = get_season_info()
        await ctx.response.send_message(f"# {season_info['name']}\n**Start date:** {season_info['startDate'][:11]}\n**Predicted end date:** {season_info['endDate'][:11]}")

async def name_autocomplete(ctx:discord.Interaction, current:str):
    data = []
    history = search_history.get_user_history(ctx.user.id)
    # if nothing typed, recommend previous searches
    if len(current) == 0:
        for entry in history:
            data.append(app_commands.Choice(name=entry, value=entry))
    else:
        users = user_data.find_user(current)
        usernames = [user.name for user in users]
        # Add if some name matches the search exactly
        if current in usernames:
            user_string = users[usernames.index(current)].get_name_with_server()
            data.append(app_commands.Choice(name=user_string, value=user_string))
        if len(users) != 0:
            # Priority for users with a matching name: in search history > highest rank > shortest name > highest account level
            best_indices = np.flip(np.argsort([user.points + user.level + (2000 - len(user.name)) + 9000*sum([user == entry for entry in history]) for user in users]))
            i = 0
            # Add results until 3 or no vaild left
            while len(data) < 3 and i < len(best_indices):
                user = users[best_indices[i]]
                if user.name != current:
                    user_string = user.get_name_with_server()
                    data.append(app_commands.Choice(name=user_string, value=user_string))
                i += 1
        else:
            for entry in history:
                data.append(app_commands.Choice(name=entry, value=entry))
    return data

async def darkmode_autocomplete(ctx:discord.Interaction, current:str):
    return [app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")]

async def server_autocomplete(ctx:discord.Interaction, current:str):
    return [app_commands.Choice(name="global", value="global"), app_commands.Choice(name="korea", value="korea"), app_commands.Choice(name="asia", value="asia"), app_commands.Choice(name="europe", value="europe"), app_commands.Choice(name="japan", value="japan")]

@tree.command(name="scout", description="Gives information about the player's matches.")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(nickname=name_autocomplete)
async def scout(ctx:discord.Interaction, nickname:str, darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True

    user_name_and_server = nickname.rsplit("#", 1)
    user = user_data.get_user(user_name_and_server[0], user_name_and_server[1])
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Just dm them for the free win, you should know how to do that right?')
    else:
        if user is not None:
            try:
                await ctx.response.defer()
                image, matches = image_creation.create_match_summary_image(user, darkmode)
                if image is not None:
                    match_result_vector = matches.get_match_result_vector()
                    first_pick_vector = matches.get_first_pick_vector()
                    first_pick_wins_vector = matches.get_first_pick_wins_vector()
                    
                    points.points[str(user.id)] = int(matches.matches[0].points)
                    user.points = int(matches.matches[0].points)
                    points.save_points()
                    search_history.add_search_query(ctx.user.id, nickname)
                    search_history.save_search_history()
                    with io.BytesIO() as image_binary:
                        image.save(image_binary, 'PNG')
                        image_binary.seek(0)
                        
                        response_text = f"""
                        Scouting info for **{user.name.capitalize()} ({user.server})**
                        
                        Overall winrate: {round(100.0*sum(match_result_vector)/len(match_result_vector))}%
                        First pick winrate: {round(100.0*sum(first_pick_wins_vector)/sum(first_pick_vector))}%
                        Second pick winrate: {round(100.0*(sum(match_result_vector)-sum(first_pick_wins_vector))/(len(match_result_vector)-sum(first_pick_vector)))}%
                        First pick in {sum(first_pick_vector)} of the last {len(match_result_vector)} matches"""
                        
                        await ctx.followup.send(response_text, file=discord.File(fp=image_binary, filename='image.png'))
                else:
                    await ctx.followup.send('This player has not played enough games.')
            except Exception as e:
                print(e)
                await ctx.followup.send('This player has not played enough games.')

        else:
            await ctx.response.send_message('Player not found, have you tried typing better (and make sure to add server if not global)?')



async def hero_autocomplete(ctx:discord.Interaction, current:str):
    data = []
    search_results = hero_list.find_up_to_n_most_popular_by_name(current, 3, hero_popularity)
    for hero in search_results:
       data.append(app_commands.Choice(name=hero.name, value=hero.name))
    return data

@tree.command(name="analyse", description="Analyse a player's recent performance with a specific hero.")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(hero=hero_autocomplete)
@app_commands.autocomplete(nickname=name_autocomplete)
async def analyze(ctx:discord.Interaction, nickname:str, hero:str, darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Analyze deez nuts lmao')
    else:
        user_name_and_server = nickname.rsplit("#", 1)
        user = user_data.get_user(user_name_and_server[0], user_name_and_server[1])
        try:
            await ctx.response.defer()
            target_hero = hero_list.get_hero_by_name(hero)
            image, picks, wins, matches = image_creation.create_hero_analysis_image(user, target_hero.code, darkmode)
            if image is not None:
                points.points[str(user.id)] = int(matches.matches[0].points)
                user.points = int(matches.matches[0].points)
                points.save_points()
                hero_popularity.increase_popularity(target_hero.code)
                hero_popularity.save_popularity()
                search_history.add_search_query(ctx.user.id, nickname)
                search_history.save_search_history()
                with io.BytesIO() as image_binary:
                    image.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    response_text = f'{user.name.capitalize()} ({user.server}) has played {picks} games with {hero.capitalize()} and has a {round(100*wins/picks)}% winrate with the hero.'
                    await ctx.followup.send(response_text, file=discord.File(fp=image_binary, filename='image.png'))
            else:
                await ctx.followup.send('That player has played too few matches with {}.'.format(hero.capitalize()))
        except Exception as e:
            print(e)
            await ctx.followup.send('That player has played too few matches with {}.'.format(hero.capitalize()))


@tree.command(name="trios", description="Analyse a player's recent performance with combinations of 3 heroes")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(nickname=name_autocomplete)
async def trios(ctx:discord.Interaction, nickname:str, darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Analyze deez nuts lmao')
    else:
        try:
            await ctx.response.defer()
            user_name_and_server = nickname.rsplit("#", 1)
            user = user_data.get_user(user_name_and_server[0], user_name_and_server[1])
            image, matches = image_creation.create_trios_image(user, darkmode)
            
            points.points[str(user.id)] = int(matches.matches[0].points)
            user.points = int(matches.matches[0].points)
            points.save_points()
            search_history.add_search_query(ctx.user.id, nickname)
            search_history.save_search_history()
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'PNG')
                image_binary.seek(0)
                response_text = f'Trios for {user.name.capitalize()} ({user.server})'
                await ctx.followup.send(response_text, file=discord.File(fp=image_binary, filename='image.png'))
        except Exception as e:
            print(e)

@tree.command(name="bans", description="Analyse bans in the player's matches")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(nickname=name_autocomplete)
async def bans(ctx:discord.Interaction, nickname:str, darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Ban deez nuts lmao')
    else:
        try:
            await ctx.response.defer()
            user_name_and_server = nickname.rsplit("#", 1)
            user = user_data.get_user(user_name_and_server[0], user_name_and_server[1])
            image, matches = image_creation.create_ban_summary_image(user, darkmode)
            
            points.points[str(user.id)] = int(matches.matches[0].points)
            user.points = int(matches.matches[0].points)
            points.save_points()
            search_history.add_search_query(ctx.user.id, nickname)
            search_history.save_search_history()
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'PNG')
                image_binary.seek(0)
                response_text = f'Ban data for {user.name.capitalize()} ({user.server})'
                await ctx.followup.send(response_text, file=discord.File(fp=image_binary, filename='image.png'))
        except Exception as e:
            print(e)

@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@tree.command(name="legendstats")
async def legendstats(ctx:discord.Interaction, darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Analyze deez nuts lmao')
    else:
        try:
            await ctx.response.defer()
            global legend_data, legend_data_update_time, nmf, transformed_legend_picks
            if twelve_hours_from_last_update(legend_data_update_time):
                legend_data, legend_data_update_time, nmf, transformed_legend_picks = update_legend_data()
            image = image_creation.create_legend_data_summary_image(legend_data, darkmode)
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'PNG')
                image_binary.seek(0)
                response_text = f'Stats from legend players, updated daily. "Best" for each category is determined by both winrate and pick frequency.'
                await ctx.followup.send(response_text, file=discord.File(fp=image_binary, filename='image.png'))
        except Exception as e:
            print(e)


@tree.command(name="legendherostats", description="Show how a specific hero is performing in legend")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(hero=hero_autocomplete)
async def legend_data_one_hero(ctx:discord.Interaction, hero:str, darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Analyze deez nuts lmao')
    else:
        try:
            await ctx.response.defer()
            global legend_data, legend_data_update_time, nmf, transformed_legend_picks
            if twelve_hours_from_last_update(legend_data_update_time):
                legend_data, legend_data_update_time, nmf, transformed_legend_picks = update_legend_data()
            target_hero = hero_list.get_hero_by_name(hero)
            image, success = image_creation.create_legend_data_image_one_hero(target_hero.code, target_hero.name, legend_data, darkmode)
            if success:
                with io.BytesIO() as image_binary:
                    image.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    await ctx.followup.send('', file=discord.File(fp=image_binary, filename='image.png'))
            else:
                await ctx.followup.send('Not enough games played with the hero.')
        except Exception as e:
            print(e)
            await ctx.followup.send('Not enough games played with the hero.')
            
@tree.command(name="similarlegendplayers", description="Find legend players with similar play styles.")
@app_commands.autocomplete(nickname=name_autocomplete)
async def legend_data_one_hero(ctx:discord.Interaction, nickname:str):
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Deez nuts are the most similar lmao')
    else:
        try:
            await ctx.response.defer()
            user_name_and_server = nickname.lower().rsplit("#", 1)
            user = user_data.get_user(user_name_and_server[0], user_name_and_server[1])
            response = get_match_data_by_user_id(user.id, user.server)
            if response.status_code == 200:
                match_list = response.json()["result_body"]["battle_list"]
                matches = MatchHistory([Match(match, hero_list) for match in match_list])
                prebans = {x[0]: x[1] for x in matches.get_all_own_preban_counts().most_common(3)}
                pick_vector = matches.get_pick_vector(hero_dict)
                global legend_data, legend_data_update_time, nmf, transformed_legend_picks
                if twelve_hours_from_last_update(legend_data_update_time):
                    legend_data, legend_data_update_time, nmf, transformed_legend_picks = update_legend_data()
                legend_prebans = legend_data["individual_prebans"]

                points.points[str(user.id)] = int(matches.matches[0].points)
                user.points = int(matches.matches[0].points)
                points.save_points()
                search_history.add_search_query(ctx.user.id, nickname)
                search_history.save_search_history()
                
                legend_players = list(legend_prebans.keys())
                n = len(legend_players)
                # Calculate how similar prebans are
                preban_similiarities = [0]*n
                for i, legend_player in enumerate(legend_players):
                    similiarity = 0
                    for legend_preban in legend_prebans[legend_player].keys():
                        if legend_preban in prebans.keys():
                            similiarity += min(prebans[legend_preban], legend_prebans[legend_player][legend_preban])
                    preban_similiarities[i] = similiarity
                # Calculate how similar picks are
                pick_dists = [0.0]*n
                transformed_picks = nmf.transform(np.asarray(pick_vector).reshape(1, -1) / 100.0)[0]
                for i, legend_player in enumerate(legend_players):
                    pick_dists[i] = np.linalg.norm(transformed_picks-transformed_legend_picks[i])
                # Normalise scores
                picks_max = max(pick_dists)
                pick_scores = [100 - 100*x/picks_max for x in pick_dists]
                preban_scores = [x/2 for x in preban_similiarities]
                # Final score based on 80% picks, 20% prebans
                final_scores = [0.8*pick_scores[i] + 0.2*preban_scores[i] for i in range(len(preban_scores))]
                top_5_similiar = np.flip(np.argsort(final_scores))[:5]
                users = []
                for i in range(5):
                    user_id_and_server = legend_players[top_5_similiar[i]].rsplit("#", 1)
                    users.append(user_data.get_user_by_id(user_id_and_server[0],user_id_and_server[1]))
                response = f"5 most similar legend players for {user.name} ({user.server}): \n\n"
                for i, u in enumerate(users):
                    response += f"{i+1} [{u.name} ({u.server})](<https://epic7.onstove.com/en/gg/battlerecord/world_{u.server}/{u.id}>) ({round(final_scores[top_5_similiar[i]], 1)})\n"
                await ctx.followup.send(response)
            else:
                await ctx.followup.send('Not enough games played.')
        except Exception as e:
            print(e)
            await ctx.followup.send('Not enough games played.')

async def cumulative_autocomplete(ctx:discord.Interaction, current:str):
    return [app_commands.Choice(name="yes", value="yes"), app_commands.Choice(name="no", value="no")]

async def type_autocomplete(ctx:discord.Interaction, current:str):
    return [app_commands.Choice(name="probability", value="probability"), app_commands.Choice(name="average attempts", value="average attempts")]

async def gear_quality_autocomplete(ctx:discord.Interaction, current:str):
    return [app_commands.Choice(name="red", value="red"), app_commands.Choice(name="purple", value="purple")]

async def starting_level_autocomplete(ctx:discord.Interaction, current:str):
    return [app_commands.Choice(name=x*3, value=x*3) for x in range(5)]

def red_odds(level:int, speed:int, logp:float, speed_rolls:int, probabilities:np.array[np.longdouble]):
    if level == 4:
        probabilities[speed + min(4, speed_rolls)] += np.exp(logp + np.log(0.75))
        probabilities[speed + 2 + min(4, speed_rolls+1)] += np.exp(np.longdouble(logp + np.log(0.33223 * 0.25)))
        probabilities[speed + 3 + min(4, speed_rolls+1)] += np.exp(np.longdouble(logp + np.log(0.33223 * 0.25)))
        probabilities[speed + 4 + min(4, speed_rolls+1)] += np.exp(np.longdouble(logp + np.log(0.33223 * 0.25)))
        probabilities[speed + 5 + min(4, speed_rolls+1)] += np.exp(np.longdouble(logp + np.log(0.00331 * 0.25)))
    else:
        red_odds(level+1, speed, logp + np.log(0.75), speed_rolls, probabilities)
        red_odds(level+1, speed+2, logp + np.log(0.33223 * 0.25), speed_rolls+1, probabilities)
        red_odds(level+1, speed+3, logp + np.log(0.33223 * 0.25), speed_rolls+1, probabilities)
        red_odds(level+1, speed+4, logp + np.log(0.33223 * 0.25), speed_rolls+1, probabilities)
        red_odds(level+1, speed+5, logp + np.log(0.00331 * 0.25), speed_rolls+1, probabilities)
        
def purple_odds(level:int, speed:int, logp:float, speed_rolls:int, probabilities:np.array[np.longdouble]):
    if level == 3:
        probabilities[speed + min(4, speed_rolls)] += np.exp(logp + np.log(0.75))
        probabilities[speed + 1 + min(4, speed_rolls+1)] += np.exp(np.longdouble(logp + np.log(0.03833 * 0.25)))
        probabilities[speed + 2 + min(4, speed_rolls+1)] += np.exp(np.longdouble(logp + np.log(0.34843 * 0.25)))
        probabilities[speed + 3 + min(4, speed_rolls+1)] += np.exp(np.longdouble(logp + np.log(0.34843 * 0.25)))
        probabilities[speed + 4 + min(4, speed_rolls+1)] += np.exp(np.longdouble(logp + np.log(0.26481 * 0.25)))
    else:
        purple_odds(level+1, speed, logp + np.log(0.75), speed_rolls, probabilities)
        purple_odds(level+1, speed+1, logp + np.log(0.03833 * 0.25), speed_rolls+1, probabilities)
        purple_odds(level+1, speed+2, logp + np.log(0.34843 * 0.25), speed_rolls+1, probabilities)
        purple_odds(level+1, speed+3, logp + np.log(0.34843 * 0.25), speed_rolls+1, probabilities)
        purple_odds(level+1, speed+4, logp + np.log(0.26481 * 0.25), speed_rolls+1, probabilities)

def cumulative_odds(probabilities:np.array[np.longdouble]):
    probabilities_cumulative = np.zeros(len(probabilities), dtype=np.longdouble)
    cumulative  = np.longdouble(0.0)
    start_i = 0
    end_i = -1
    for i in range(len(probabilities)-1, 0, -1):
        if cumulative == 1.0:
            start_i = i
        if cumulative == 0.0:
            end_i = i
        cumulative = min(1.0, cumulative + probabilities[i])
        probabilities_cumulative[i] = cumulative
    return probabilities_cumulative, start_i, end_i

@tree.command(name="speedcheck", description="Check probability distribution for speed.")
@app_commands.autocomplete(gear_quality=gear_quality_autocomplete)
@app_commands.autocomplete(starting_level=starting_level_autocomplete)
@app_commands.autocomplete(cumulative=cumulative_autocomplete)
@app_commands.autocomplete(type=type_autocomplete)
async def speedcheck(ctx:discord.Interaction, gear_quality:str="red", starting_speed:int=4, starting_level:int=0, rolls_in_speed:int=0, cumulative:str="yes", type:str="probability"):
    if gear_quality not in ["red","purple"] or starting_speed<=0 or starting_speed>25 or starting_speed/(rolls_in_speed+1.01)>=5:
        await ctx.response.send_message("Invalid arguments")
    else:
        if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
            await ctx.response.send_message('https://www.google.com/search?q=am+i+dumb')
        else:
            if gear_quality=="purple":
                probabilities = np.zeros(25, dtype=np.longdouble)
            else:
                probabilities = np.zeros(35, dtype=np.longdouble)
            if gear_quality=="red":
                red_odds(int(starting_level/3), int(starting_speed), 0.0, rolls_in_speed, probabilities)
            else:
                purple_odds(int(starting_level/3), int(starting_speed), 0.0, rolls_in_speed, probabilities)
            if cumulative == "yes":
                probabilities, start_i, end_i = cumulative_odds(probabilities)
            else:
                _, start_i, end_i = cumulative_odds(probabilities)
            if end_i == -1:
                end_i == len(probabilities)-1
            if type=="probability":
                response = "Probabilities\n"
                for i, p in enumerate(probabilities):
                    if i>=start_i and i<=end_i:
                        if p > 1e-2:
                            response += f"**{i}**: {100*p:.1f}%\n"
                        elif p > 1e-4:
                            response += f"**{i}**: {100*p:.3f}%\n"
                        elif p > 1e-6:
                            response += f"**{i}**: {100*p:.5f}%\n"
                        elif p > 1e-10:
                            response += f"**{i}**: {100*p:.8f}%\n"
                        else:
                            response += f"**{i}**: {100*p:.15f}%\n"
            else:
                response = "Attempts to get on average\n"
                for i, p in enumerate(probabilities):
                    if p!=0.0 and i>=start_i and i<=end_i:
                        response += f"**{i}**: {round(1.0/p,1)}\n"
            await ctx.response.send_message(response)

@bot.event
async def on_ready():
    await tree.sync()

@client.event
async def on_ready():
    await tree.sync()

@bot.event
async def on_command_error(ctx:discord.Interaction, error):
    await ctx.response.send_message("Unknown command")

def run_bot():
    client.run(TOKEN)

run_bot()