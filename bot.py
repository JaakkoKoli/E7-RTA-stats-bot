from dotenv import load_dotenv
import os
from update_data import *
import discord
import random
from discord import app_commands
from discord.ext import commands
import io
from functions import save_image_from_url, get_match_data_by_user_id
from user_data import *
from search_history import *
from hero_data import *
from datetime import datetime, timedelta
from sklearn.decomposition import NMF
import numpy as np
import matplotlib.pyplot as plt

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

get_new_heroname_json()
with open("data/heronames.json", "r") as json_file:
    hero_list = HeroList(json.load(json_file))
hero_dict = hero_list.get_hero_vector_dict()

current_hero_image_codes = [f.split(".")[0] for f in os.listdir("hero_images") if os.path.isfile(os.path.join("hero_images", f))]
for herocode in hero_list.hero_code_list:
    if herocode not in current_hero_image_codes:
        image_url = 'https://static.smilegatemegaport.com/event/live/epic7/guide/images/hero/{}_s.png'.format(herocode)
        save_image_from_url(image_url, 'hero_images/{}.png'.format(herocode))


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

def update_legend_data() -> tuple[dict, datetime, NMF, np.ndarray]:
    with open("data/legend_data.json", "r") as json_file:
        legend_data = json.load(json_file)
    nmf = NMF(n_components=4, init="nndsvd", random_state=42)
    legend_vectors = np.asarray([vector for vector in legend_data["pick_vectors"].values()])
    return legend_data, datetime.now(), nmf, nmf.fit_transform(legend_vectors)

def twelve_hours_from_last_update(last_update:datetime) -> bool:
    return datetime.now() - last_update >= timedelta(hours=12)

legend_data, legend_data_update_time, nmf, transformed_legend_picks = update_legend_data()

# Load banned users/discord servers
poobrain_set = set()
with open('poobrain.txt', 'r') as file:
    for line in file:
        values = line.strip().split(', ')
        poobrain_set.update(values)
        
pooguild_set = set()
with open('pooguilds.txt', 'r') as file:
    for line in file:
        values = line.strip().split(', ')
        pooguild_set.update(values)

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
        
        
async def name_autocomplete(ctx:discord.Interaction, current:str):
    data = []
    history = search_history.get_user_history(ctx.user.id)
    if len(current) == 0:
        for entry in history:
            data.append(app_commands.Choice(name=entry, value=entry))
    else:
        users = user_data.find_user(current)
        usernames = [user.name for user in users]
        if current in usernames:
            user_string = users[usernames.index(current)].get_name_with_server()
            data.append(app_commands.Choice(name=user_string, value=user_string))
        if len(users) != 0:
            best_indices = np.flip(np.argsort([user.points + user.level + 9000*sum([user == entry for entry in history]) for user in users]))
            i = 0
            while len(data) < 3 and i < len(best_indices):
                user_string = users[best_indices[i]].get_name_with_server()
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
                image, matches = create_match_summary_image(user.id, user.server, hero_list, darkmode)
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
            image, picks, wins, matches = create_hero_analysis_image(user.id, user.server, target_hero.code, hero_list, darkmode)
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
            image, matches = create_trios_image(user.id, user.server, hero_list, darkmode)
            
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
            image, matches = create_ban_summary_image(user.id, user.server, hero_list, darkmode)
            
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
            image = create_legend_data_summary_image(legend_data, darkmode)
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
            image, success = create_legend_data_image_one_hero(target_hero.code, target_hero.name, legend_data, darkmode)
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
                prebans = [x[0] for x in matches.get_all_own_preban_counts().most_common(3)]
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
                preban_similiarities = [0]*n

                for i, legend_player in enumerate(legend_players):
                    similiarity = 0
                    for legend_preban in legend_prebans[legend_player]:
                        if legend_preban in prebans:
                            similiarity += (6 - 2*prebans.index(legend_preban)) * (6 - 2*legend_prebans[legend_player].index(legend_preban))
                    preban_similiarities[i] = similiarity / (len(legend_prebans[legend_player]) + len(prebans))
                    
                pick_dists = [0.0]*n
                transformed_picks = nmf.transform(np.asarray(pick_vector).reshape(1, -1))[0]
                for i, legend_player in enumerate(legend_players):
                    pick_dists[i] = np.linalg.norm(transformed_picks-transformed_legend_picks[i])
                argsorted_preban_similiarities = np.flip(np.argsort(preban_similiarities))    
                argsorted_pick_dists = np.argsort(pick_dists)
                final_similiarity_scores = [0]*n
                for i in range(n):
                    final_similiarity_scores[argsorted_preban_similiarities[i]] += (n - i)*0.2
                    final_similiarity_scores[argsorted_pick_dists[i]] += (n - i)*0.8
                top_5_similiar = np.flip(np.argsort(final_similiarity_scores))[:5]
                users = []
                for i in range(5):
                    user_id_and_server = legend_players[top_5_similiar[i]].rsplit("#", 1)
                    users.append(user_data.get_user_by_id(user_id_and_server[0],user_id_and_server[1]))
                response = f"5 most similar legend players for {user.name} ({user.server}): \n\n"
                for i, u in enumerate(users):
                    response += f"{i+1} [{u.name} ({u.server})](<https://epic7.onstove.com/en/gg/battlerecord/world_{u.server}/{u.id}>) ({round(final_similiarity_scores[top_5_similiar[i]], 1)})\n"
                await ctx.followup.send(response)
            else:
                await ctx.followup.send('Not enough games played.')
        except Exception as e:
            print(e)
            await ctx.followup.send('Not enough games played.')

@bot.event
async def on_ready():
    await tree.sync()

@client.event
async def on_ready():
    await tree.sync()

@bot.event
async def on_command_error(ctx:discord.Interaction, error):
    await ctx.response.send_message("Unknown command")

client.run(TOKEN)
