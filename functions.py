import requests
import pandas as pd
import json
from PIL import Image
import numpy as np

def get_new_userdata(server:str) -> None:
    response = requests.get(
        f"https://static.smilegatemegaport.com/gameRecord/epic7/epic7_user_world_{server}.json"
    )
    if response.status_code == 200:
        with open(f"data/epic7_user_world_{server}.json", "w") as file:
            json.dump(response.json(), file)
        print(f"File saved successfully as epic7_user_world_{server}.json")
    else:
        print("Failed to download file")


def update_userdata_for_all_servers() -> None:
    for server in ["asia", "eu", "global", "jpn", "kor"]:
        get_new_userdata(server)


def save_image_from_url(url:str, file_path:str) -> None:
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Image saved successfully as {file_path}")
    else:
        print("Failed to download image")


def get_new_heroname_json() -> None:
    response = requests.get(
        "http://static.smilegatemegaport.com/gameRecord/epic7/epic7_hero.json"
    )
    if response.status_code == 200:
        with open("data/heronames.json", "w") as file:
            json.dump(response.json()["en"], file)
    else:
        print("Failed to download file heronames.json")


def get_herocodes() -> list[str]:
    heroname_df = pd.read_json("data/heronames.json")
    herocodes = []

    for x in range(len(heroname_df)):
        herocodes.append([heroname_df.iloc[x]["code"]][0])
    return herocodes


def download_all_data() -> None:
    get_new_heroname_json()
    update_userdata_for_all_servers()

    herocodes = get_herocodes()

    for i, herocode in enumerate(herocodes):
        image_url = "https://static.smilegatemegaport.com/event/live/epic7/guide/images/hero/{}_s.png".format(
            herocode
        )
        save_image_from_url(image_url, "hero_images/{}.png".format(herocode))
        print("{}/{}".format(i, len(herocodes)))


def get_top_100_players():
    res = []
    try:
        for i in range(10):
            response = requests.post(
            f"https://epic7.onstove.com/gg/gameApi/getWorldUserRankingDetail?season_code=pvp_rta_ss16&world_code=all&current_page={i+1}&lang=en"
            )
            if response.status_code == 200:
                res += [response.json()]
    except:
        print("error in get top 100")
    return res


def is_server(string:str) -> bool:
    return string.lower() in ["global", "europe", "eu", "japan", "jpn", "asia", "korea", "kor"]

def get_server_name(server:str) -> str:
    server = server.lower()
    if server == "europe" or server == "eu":
        return "eu"
    elif server == "japan" or server == "jpn":
        return "jpn"
    elif server == "asia":
        return "asia"
    elif server == "korea" or server == "kor":
        return "kor"
    else:
        return "global"

def clean(string:str) -> str:
    return string.replace("'","").replace("[","").replace("]","")

def init_hero_data_code_to_name() -> dict:
    heroname_df = pd.read_json("data/heronames.json")
    heronames = dict()

    for x in range(len(heroname_df)):
        heronames[heroname_df.iloc[x]["code"]] = heroname_df.iloc[x]["name"]

    return heronames


def init_hero_data_name_to_code() -> dict:
    heroname_df = pd.read_json("data/heronames.json")
    heronames = dict()

    for x in range(len(heroname_df)):
        heronames[heroname_df.iloc[x]["name"].lower()] = heroname_df.iloc[x]["code"]

    return heronames

def get_hero_img(hero_code:str) -> Image:
    try:
        return Image.open(f"hero_images/{hero_code}.png").convert("RGBA")
    except Exception as e:
        print(e)
        width, height = 112, 112
        image_array = np.zeros((height, width, 3), dtype=np.uint8)
        return Image.fromarray(image_array)
    
def get_match_data_by_username(username:str, server:str) -> requests.Response:
    server = get_server_name(server)
    user_dict = create_dict_with_nickName_key_by_server(server)
    url = "https://epic7.gg.onstove.com/gameApi/getBattleList?nick_no={}&world_code=world_{}&lang=en&season_code=".format(
        get_id_by_username(username, user_dict), server
    )
    payload = {}
    response = requests.post(url, json=payload)

    return response

def get_match_data_by_user_id(user_id:str, server:str) -> requests.Response:
    server = get_server_name(server)
    url = "https://epic7.gg.onstove.com/gameApi/getBattleList?nick_no={}&world_code=world_{}&lang=en&season_code=".format(user_id, server)
    payload = {}
    response = requests.post(url, json=payload)

    return response


def create_dict_with_nickNo_key_by_server(server:str="global") -> dict:
    fileName = "data/epic7_user_world_{}.json".format(server)
    uid_df = pd.read_json(fileName)
    users = dict()
    for x in range(len(uid_df)):
        u = dict(uid_df.iloc[x]["users"])
        users[u["nick_no"]] = u["nick_nm"].lower()

    return users


def create_dict_with_nickName_key_by_server(server:str="global", min_rank:int=60) -> dict:
    filename = "data/epic7_user_world_{}.json".format(server)
    uid_df = pd.read_json(filename)
    users = dict()
    for x in range(len(uid_df)):
        u = dict(uid_df.iloc[x]["users"])
        if int(u["rank"]) >= min_rank:
            users[u["nick_nm"].lower()] = u["nick_no"]

    return users


def get_id_by_username(username:str, players_db:dict) -> str:
    user_id = players_db.get(username.lower(), None)

    if user_id is None:
        return None
    else:
        return user_id


def get_username_by_id(user_id:str, players_db:dict) -> str:
    username = players_db.get(user_id, None)

    if user_id is None:
        return None
    else:
        return username.lower()

def find_username(query:str, players_db:dict) -> str:
    return list(filter(lambda username: query.lower() in username.lower(), players_db.keys()))

def is_server(string:str) -> bool:
    return string.lower() in [
        "global",
        "europe",
        "eu",
        "japan",
        "jpn",
        "asia",
        "korea",
        "kor",
    ]


def get_server_name(server:str) -> str:
    server = server.lower()
    if server == "europe" or server == "eu":
        return "eu"
    elif server == "japan" or server == "jpn":
        return "jpn"
    elif server == "asia":
        return "asia"
    elif server == "korea" or server == "kor":
        return "kor"
    else:
        return "global"

# Creates a winrate graph where the value at each point consists of a weighted average of the past ones
def create_winrate_graph(win_vector:list[int]) -> np.ndarray:
    n = len(win_vector)
    win_vector = np.flip(win_vector)
    if n < 40:
        if n > 0:
            return [np.mean(win_vector[0:x]) for x in range(n)]
        else:
            return np.zeros(100)
    res = np.zeros(n)
    
    div = 1
    for i in range(n):
        wr = 0
        for i2 in range(i):
            wr += (i2+1)*win_vector[i2]/div
        res[i] = wr
        div += i+1
    return np.convolve(res[30:], [0.333]*3, mode="valid")
