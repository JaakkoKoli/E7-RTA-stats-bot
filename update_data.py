import requests
import pandas as pd
import json

def save_image_from_url(url:str, file_path:str) -> None:
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Image saved successfully as {file_path}")
    else:
        print("Failed to download image")

def get_new_heroname_json() -> None:
    response = requests.get("http://static.smilegatemegaport.com/gameRecord/epic7/epic7_hero.json")
    if response.status_code == 200:
        with open("data/heronames.json", 'w') as file:
            json.dump(response.json()["en"], file)
        print(f"File saved successfully as heroname.json")
    else:
        print("Failed to download file")


def get_herocodes() -> list[str]:
    heroname_df = pd.read_json('heronames.json')
    herocodes = []

    for x in range(len(heroname_df)):
        herocodes.append([heroname_df.iloc[x]["code"]][0])
    return herocodes

def get_new_userdata(server:str) -> None:
    response = requests.get(f"https://static.smilegatemegaport.com/gameRecord/epic7/epic7_user_world_{server}.json")
    if response.status_code == 200:
        with open(f"data/epic7_user_world_{server}.json", 'w') as file:
            json.dump(response.json(), file)
        print(f"File saved successfully as epic7_user_world_{server}.json")
    else:
        print("Failed to download file")