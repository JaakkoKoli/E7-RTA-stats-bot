import discord
import random
from discord import app_commands
from discord.ext import commands
import io
from image_creation import *
from functions import *
from dotenv import load_dotenv
import os

load_dotenv()

if not os.path.exists("legend_data"):
    os.makedirs("legend_data") 
if not os.path.exists("hero_images"):
    os.makedirs("hero_images")   

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

TOKEN = os.getenv('TOKEN')
PREFIX = '!!'

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

global_user_dict = create_dict_with_nickName_key_by_server("global")
asia_user_dict = create_dict_with_nickName_key_by_server("asia")
jpn_user_dict = create_dict_with_nickName_key_by_server("jpn")
kor_user_dict = create_dict_with_nickName_key_by_server("kor")
eu_user_dict = create_dict_with_nickName_key_by_server("eu")

hero_data_name_to_code = init_hero_data_name_to_code()
hero_data_code_to_name = init_hero_data_code_to_name()

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

def get_user_dict(server):
    server = get_server_name(server)
    if server == "global":
        return global_user_dict
    elif server == "eu":
        return eu_user_dict
    elif server == "jpn":
        return jpn_user_dict
    elif server == "asia":
        return asia_user_dict
    elif server == "kor":
        return kor_user_dict
    else:
        return None

############
# COMMANDS #
############

@tree.command(name="shitpost")
async def shitpost(ctx:discord.Interaction):
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Just read your own message history')
    else:
        shitpost_list = [[" In the digital universe of Epic Seven, Traptrix stands tall, embodying the essence of commitment with an astonishing 5000 games per season. Clad in the prestigious legend frame, their motto, no frame no opinion, speaks volumes, underscoring the significance and authority their seasoned expertise lends to the strategic discussions and decisions within the game. As an arbiter of insight and wisdom, Traptrix's every move echoes with the resonant power of their gameplay, a living testament to their dedication to this virtual realm.",
                          "You see that? it's called a legend frame, something you'll never have!", 
                          "Yield pls", 
                          "Idk what you want me to say dude it was his little sister's birthday so the boys surprised him with a frame if that's wintrading lock me tf up", 
                          "Switch to Caerliss's profile card, free wins late in season"]]
        response = random.choice(shitpost_list)
        await ctx.response.send_message(response)

async def darkmode_autocomplete(ctx:discord.Interaction, current:str):
    return [app_commands.Choice(name="on", value="on"), app_commands.Choice(name="off", value="off")]

async def server_autocomplete(ctx:discord.Interaction, current:str):
    return [app_commands.Choice(name="global", value="global"), app_commands.Choice(name="korea", value="korea"), app_commands.Choice(name="asia", value="asia"), app_commands.Choice(name="europe", value="europe"), app_commands.Choice(name="japan", value="japan")]

@tree.command(name="scout", description="Gives information about the player's matches.")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(server=server_autocomplete)
async def scout(ctx:discord.Interaction, nickname:str, server:str="global", darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    server = get_server_name(server)
    user_id = get_id_by_username(nickname, get_user_dict(server))
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Just dm them for the free win, you should know how to do that right?')
    else:
        if user_id is not None:
            try:
                await ctx.response.defer()
                image, matches = create_match_summary_image(user_id, server, darkmode)
                match_result_vector = matches.get_match_result_vector()
                first_pick_vector = matches.get_first_pick_vector()
                first_pick_wins_vector = matches.get_first_pick_wins_vector()
                with io.BytesIO() as image_binary:
                    image.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    
                    response_text = f"""
                    Scouting info for **{nickname.capitalize()} ({server})**
                    
                    Overall winrate: {round(100.0*sum(match_result_vector)/len(match_result_vector))}%
                    First pick winrate: {round(100.0*sum(first_pick_wins_vector)/sum(first_pick_vector))}%
                    Second pick winrate: {round(100.0*(sum(match_result_vector)-sum(first_pick_wins_vector))/(len(match_result_vector)-sum(first_pick_vector)))}%
                    First pick in {sum(first_pick_vector)} of the last {len(match_result_vector)} matches"""
                    
                    await ctx.followup.send(response_text, file=discord.File(fp=image_binary, filename='image.png'))
            except Exception as e:
                print(e)
                await ctx.followup.send('This player has not played enough games.')

        else:
            await ctx.response.send_message('Player not found, have you tried typing better (and make sure to add server if not global)?')

@tree.command(name="find", description="Finds players with the given search query in their nickname")
async def find(ctx:discord.Interaction, query:str, server:str="global"):
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('**Searching.. Searching...** Sorry sir you do not have enough vBucks to complete this transaction!')
    else:
        matches = find_username(query, get_user_dict(server))
        if len(matches) != 0:
            await ctx.response.send_message('Player names in {server} server that contain **{}**: {}.'.format(query, clean(str(matches))))
        else:
            await ctx.response.send_message('No users found')


async def hero_autocomplete(ctx:discord.Interaction, current:str):
    data = []
    for hero_choice in hero_data_name_to_code.keys():
        if current.lower() in hero_choice.lower() and len(data)<4:
            data.append(app_commands.Choice(name=hero_choice, value=hero_choice))
    return data

@tree.command(name="analyse", description="Analyse a player's recent performance with a specific hero.")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(hero=hero_autocomplete)
@app_commands.autocomplete(server=server_autocomplete)
async def analyze(ctx:discord.Interaction, nickname:str, hero:str, server:str="global", darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Analyze deez nuts lmao')
    else:
        user_id = get_id_by_username(nickname, get_user_dict(server))
        server = get_server_name(server)
        try:
            await ctx.response.defer()
            image, picks, wins = create_hero_analysis_image(user_id, server, hero_data_name_to_code[hero.lower()], darkmode)
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'PNG')
                image_binary.seek(0)
                response_text = f'{nickname.capitalize()} ({server}) has played {picks} games with {hero.capitalize()} and has a {round(100*wins/picks)}% winrate with the hero.'
                await ctx.followup.send(response_text, file=discord.File(fp=image_binary, filename='image.png'))
        except Exception as e:
            print(e)
            await ctx.followup.send('That player has played too few matches with {}.'.format(hero.capitalize()))


@tree.command(name="trios", description="Analyse a player's recent performance with combinations of 3 heroes")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(server=server_autocomplete)
async def trios(ctx:discord.Interaction, nickname:str, server:str="global", darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Analyze deez nuts lmao')
    else:
        try:
            await ctx.response.defer()
            server = get_server_name(server)
            user_id = get_id_by_username(nickname, get_user_dict(server))
            image = create_trios_image(user_id, server, darkmode)
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'PNG')
                image_binary.seek(0)
                response_text = f'Trios for {nickname.capitalize()} ({server})'
                await ctx.followup.send(response_text, file=discord.File(fp=image_binary, filename='image.png'))
        except Exception as e:
            print(e)

@tree.command(name="bans", description="Analyse bans in the player's matches")
@app_commands.autocomplete(darkmode=darkmode_autocomplete)
@app_commands.autocomplete(server=server_autocomplete)
async def bans(ctx:discord.Interaction, nickname:str, server:str="global", darkmode:str="on"):
    if darkmode == "off":
        darkmode = False
    else:
        darkmode = True
    if (str(ctx.user.id) in poobrain_set) or (str(ctx.guild.id) in pooguild_set):
        await ctx.response.send_message('Ban deez nuts lmao')
    else:
        try:
            await ctx.response.defer()
            server = get_server_name(server)
            user_id = get_id_by_username(nickname, get_user_dict(server))
            image = create_ban_summary_image(user_id, server, darkmode)
            with io.BytesIO() as image_binary:
                image.save(image_binary, 'PNG')
                image_binary.seek(0)
                response_text = f'Ban data for {nickname.capitalize()} ({server})'
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
            image = create_legend_data_summary_image(darkmode)
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
            image, success = create_legend_data_image_one_hero(hero_data_name_to_code[hero.lower()], darkmode)
            if success:
                with io.BytesIO() as image_binary:
                    image.save(image_binary, 'PNG')
                    image_binary.seek(0)
                    await ctx.followup.send('', file=discord.File(fp=image_binary, filename='image.png'))
            else:
                await ctx.followup.send('Not enough games playerd with the hero.')
        except Exception as e:
            print(e)
            await ctx.followup.send('Not enough games playerd with the hero.')

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
