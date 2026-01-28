import json

class HeroPopularity:
    def __init__(self):
        self.hero_popularity:dict = {}
        
    def load_popularity(self) -> None:
        with open("data/hero_popularity.json", "r") as json_file:
            self.hero_popularity = json.load(json_file)
            
    def save_popularity(self) -> None:
        with open("data/hero_popularity.json", "w") as json_file:
            json.dump(self.hero_popularity, json_file, indent=4)
    
    def get_popularity(self, hero_code:str) -> int:
        return self.hero_popularity.get(hero_code, 0)
    
    def increase_popularity(self, hero_code:str) -> None:
        self.hero_popularity[hero_code] = self.hero_popularity.get(hero_code, 0) + 1
            
class Hero:
    def __init__(self, code, name, grade, element, role):
        self.code = code
        self.name = name
        self.grade = grade
        self.element = element
        self.role = role
        
class HeroList:
    def __init__(self, data:dict):
        self.hero_list:list[Hero] = []
        self.read_data(data)
        self.hero_code_list = [hero.code for hero in self.hero_list]
        self.hero_name_list = [hero.name.lower() for hero in self.hero_list]
        self.hero_code_dict = self.create_hero_code_dict()
        self.hero_name_dict = self.create_hero_name_dict()
    
    def read_data(self, data:dict) -> None:
        for hero in data:
            self.hero_list.append(Hero(hero["code"], hero["name"], hero["grade"], hero["attribute_cd"], hero["job_cd"]))
            
    def create_hero_code_dict(self) -> dict:
        hero_code_dict = {}
        for i, hero in enumerate(self.hero_list):
            hero_code_dict[hero.code] = i
        return hero_code_dict
    
    def create_hero_name_dict(self) -> dict:
        hero_name_dict = {}
        for i, hero in enumerate(self.hero_list):
            hero_name_dict[hero.name.lower()] = i
        return hero_name_dict
    
    def get_hero_by_code(self, code:str) -> Hero:
        i = self.hero_code_dict.get(code, None)
        if i is None:
            return None
        else:
            return self.hero_list[i]
    
    def get_hero_by_name(self, name:str) -> Hero:
        i = self.hero_name_dict.get(name.lower(), None)
        if i is None:
            return None
        else:    
            return self.hero_list[i]
    
    def find_by_name(self, search_query:str) -> list[Hero]:
        search_result = []
        search_query = search_query.lower()
        for name in self.hero_name_list:
            if search_query in name:
                search_result.append(self.get_hero_by_name(name))
        return search_result
    
    def find_up_to_n_most_popular_by_name(self, search_query:str, n:int, popularity:HeroPopularity) -> list[Hero]:
        search_result = self.find_by_name(search_query)
        if len(search_result) <= n:
            return search_result
        search_popularity = []
        for i, hero in enumerate(search_result):
            search_popularity.append((popularity.get_popularity(hero.code), i))
        search_popularity.sort(key=lambda x: x[0], reverse=True)
        return [search_result[x[1]] for x in search_popularity[:n]]
        
    def get_hero_vector_dict(self):
        hero_dict = {}
        for i, hero_code in enumerate(self.hero_code_list):
            hero_dict[hero_code] = i
        return hero_dict