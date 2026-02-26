from hero_data import *
from user_data import *
from search_history import *
import os
from datetime import datetime, timedelta
from PIL import Image
import numpy as np
import requests

class ResourceHandler:
    def __init__(self, image_location:str="hero_images/", data_location:str="data/"):
        self.image_location:str = image_location
        self.data_location:str = data_location
        self.download_hero_list()
        self.hero_list = self.read_hero_list()
        self.image_codes = self.get_current_hero_image_codes()
        self.download_all_missing_hero_images()
        self.image_codes = self.get_current_hero_image_codes()
        self.update_timestamp = datetime.now()
        self.user_data = UserData()
        self.points = Points()
        self.hero_popularity = HeroPopularity()
        self.search_history = SearchHistory()


    def read_hero_list(self) -> None:
        with open(f"{self.data_location}heronames.json", "r") as json_file:
            self.hero_list = HeroList(json.load(json_file))

    def get_hero_image(self, hero_code:str) -> Image:
        if hero_code not in self.image_codes and self.twelve_hours_from_last_update():
            if self.download_hero_list():
                self.read_hero_list()
                if self.download_hero_image(hero_code):
                    self.image_codes = self.get_current_hero_image_codes()
            self.update_timestamp = datetime.now()
        try:
            return Image.open(f"{self.image_location}{hero_code}.png").convert("RGBA")
        except Exception as e:
            width, height = 112, 112
            image_array = np.zeros((height, width, 3), dtype=np.uint8)
            return Image.fromarray(image_array)

    def download_all_missing_hero_images(self) -> None:
        for hero_code in self.hero_list.hero_code_list:
            if hero_code not in self.image_codes:
                self.download_hero_image(hero_code)

    def download_hero_image(self, hero_code:str) -> bool:
        response = requests.get(f"https://static-pubcomm.onstove.com/event/live/epic7/guide/images/hero/{hero_code}_s.png")
        if response.status_code == 200:
            with open(f"{self.image_location}{hero_code}.png", "wb") as file:
                file.write(response.content)
            return True
        return False

    def download_hero_list(self) -> None:
        response = requests.get("https://static-pubcomm.onstove.com/gameRecord/epic7/epic7_hero.json")
        if response.status_code == 200:
            with open(f"{self.data_location}heronames.json", "w") as file:
                json.dump(response.json()["en"], file)
            return True
        return False

    def get_current_hero_image_codes(self) -> list[str]:
        return [f.split(".")[0] for f in os.listdir(self.image_location) if os.path.isfile(os.path.join(self.image_location, f))]

    def read_userdata(self):
        self.user_data = UserData()
        self.points = Points()
        self.points.load_points()
        for server in ["global", "asia", "jpn", "kor", "eu"]:
            with open(f"data/epic7_user_world_{server}.json", "r") as json_file:
                server_user_data = json.load(json_file)
                self.user_data.read_data(server_user_data, server)
        self.user_data.create_search_index()
        self.user_data.load_points(self.points.points)
    
    def download_userdata(self) -> None:
        for server in ["global", "asia", "jpn", "kor", "eu"]:
            response = requests.get(f"https://static-pubcomm.onstove.com/gameRecord/epic7/epic7_user_world_{server}.json")
            if response.status_code == 200:
                with open(f"data/epic7_user_world_{server}.json", "w") as file:
                    json.dump(response.json(), file)
            else:
                print(f"Failed to download file epic7_user_world_{server}.json")

    def read_hero_popularity(self) -> None:
        self.hero_popularity = HeroPopularity()
        if os.path.isfile("data/hero_popularity.json"):
            self.hero_popularity.load_popularity()
            
    def read_search_history(self) -> None:
        self.search_history = SearchHistory()
        if os.path.exists("data/search_history.json"):
            self.search_history.load_search_history()

    def initialise_data(self) -> None:
        self.download_hero_list()
        self.read_hero_list()
        self.read_hero_popularity()
        self.download_userdata()
        self.read_userdata()
        self.read_search_history()
        self.read_hero_popularity()

    def twelve_hours_from_last_update(self) -> bool:
        return datetime.now() - self.update_timestamp >= timedelta(hours=12)