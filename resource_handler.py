from hero_data import *
import os
from datetime import datetime, timedelta
from PIL import Image
import numpy as np
import requests

class ResourceHandler:
    def __init__(self, image_location:str="hero_images/", data_location:str="data/"):
        self.image_location:str = image_location
        self.data_location:str = data_location
        self.hero_list = self.read_hero_list()
        self.image_codes = self.get_current_hero_image_codes()
        self.download_all_missing_hero_images()
        self.image_codes = self.get_current_hero_image_codes()
        self.update_timestamp = datetime.now()
        

    def read_hero_list(self) -> HeroList:
        with open(f"{self.data_location}heronames.json", "r") as json_file:
            return HeroList(json.load(json_file))
        
    def get_hero_image(self, hero_code:str) -> Image:
        if hero_code not in self.image_codes and self.twelve_hours_from_last_update():
            if self.download_hero_list():
                self.hero_list = self.get_hero_list()
                if self.download_hero_image(hero_code):
                    self.image_codes = self.get_current_hero_image_codes()
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
        response = requests.get(f"https://static.smilegatemegaport.com/event/live/epic7/guide/images/hero/{hero_code}_s.png")
        if response.status_code == 200:
            with open(f"{self.image_location}{hero_code}.png", "wb") as file:
                file.write(response.content)
            return True
        return False
    
    def download_hero_list(self) -> None:
        response = requests.get("http://static.smilegatemegaport.com/gameRecord/epic7/epic7_hero.json")
        if response.status_code == 200:
            with open(f"{self.data_location}heronames.json", "w") as file:
                json.dump(response.json()["en"], file)
            return True
        return False
    
    def get_current_hero_image_codes(self) -> list[str]:
        return [f.split(".")[0] for f in os.listdir(self.image_location) if os.path.isfile(os.path.join(self.image_location, f))]
    
    def twelve_hours_from_last_update(self) -> bool:
        return datetime.now() - self.update_timestamp >= timedelta(hours=12)