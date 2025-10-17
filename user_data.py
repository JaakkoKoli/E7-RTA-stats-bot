import json
import requests
from match_data import *

class User:
    def __init__(self, id:int, name:str, level:int, profile_hero_code:str, server:str):
        self.id = id
        self.name = name
        self.level = level
        self.server = server
        self.profile_hero_code = profile_hero_code
        self.points:int = 0

    def get_name_with_server(self, divider:str="#") -> str:
        return f"{self.name}{divider}{self.server}"
    
    def get_data_as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "server": self.server,
            "profile_hero_code": self.profile_hero_code,
            "points": self.points
        }
    
    def __eq__(self, user2) -> bool:
        if isinstance(user2, User):
            return self.name == user2.name
        return self.name == user2
    
    def __lt__(self, user2) -> bool:
        if isinstance(user2, User):
            return self.name < user2.name
        return self.name < user2
    
    def get_match_data(self, hero_list) -> requests.Response:
        response = requests.post(f"https://epic7.gg.onstove.com/gameApi/getBattleList?nick_no={self.id}&world_code=world_{self.server}&lang=en&season_code=", json={})
        matches = MatchHistory([])
        if response.status_code == 200:
            match_list = response.json()["result_body"]["battle_list"]
            matches = MatchHistory([Match(match, hero_list) for match in match_list])
        return matches
        

class UserData:
    def __init__(self):
        self.users:list[User] = []
        self.index:dict = dict()
    
    def read_data(self, data:object, server:str) -> None:
        for user in data["users"]:
            self.users.append(User(int(user["nick_no"]), user["nick_nm"].lower(), int(user["rank"]), user["code"], server))
        self.users.sort()
    
    def recursive_create_index(self, n:int, start_i:int=0, depth:int=0, max_size:int=20) -> dict:
        start_chars = list({user.name.lower()[depth] for user in self.users[start_i:(start_i+n)] if len(user.name)>depth})
        start_chars.sort()
        index = dict()
        current_start_char = 0
        current_size = 0
        index[" "] = [start_i, n]
        for user in self.users[start_i:(start_i+n)]:
            success = False
            while not success:
                if len(user.name)<=depth:
                    start_i += current_size + 1
                    current_size = 0
                    success = True
                elif user.name.lower()[depth] != start_chars[current_start_char]:
                    if current_size > 0:
                        if current_size <= max_size:
                            index[start_chars[current_start_char]] = [start_i, current_size]
                        else:
                            index[start_chars[current_start_char]] = self.recursive_create_index(current_size, start_i, depth+1, max_size)
                    start_i += current_size
                    current_start_char += 1
                    current_size = 0
                else:
                    success = True
                    current_size += 1
        if current_size <= max_size:
            index[start_chars[current_start_char]] = [start_i, current_size]
        else:
            index[start_chars[current_start_char]] = self.recursive_create_index(current_size, start_i, depth+1, max_size)
        return index
    
    def create_search_index(self) -> None:
        self.index = self.recursive_create_index(n=len(self.users))        
    
    def find_user(self, search_query:str) -> list[User]:
        if len(search_query) == 0:
            return []
        search_query = search_query.lower()
        if search_query[0] not in self.index.keys():
            return [] 
        ind = self.index[search_query[0]]
        if len(search_query) > 1 and type(ind) != list:
            i = 1
            while len(search_query)>i:
                ind = ind.get(search_query[i], [])
                if type(ind) == list: 
                    break
                i += 1
        if type(ind) == list:
            if len(ind) == 0:
                return []
            return self.users[ind[0]:(ind[0]+ind[1])]
        return self.users[ind[" "][0]:(ind[" "][0]+ind[" "][1])]
    
    def get_user(self, user_name:str, server:str) -> User:
        user_name = user_name.lower()
        if user_name[0] not in self.index.keys():
            return None
        for user in self.users[self.index[user_name[0]][0]:self.index[user_name[0]][1]]:
            if user.name == user_name and user.server == server:
                return user
        return None
    
    def get_user_by_id(self, user_id:str, server:str) -> User:
        return self.users[self.get_user_ids_and_server_as_list().index(f"{user_id}#{server}")]
    
    def get_user_ids_as_list(self) -> list[int]:
        return [user.id for user in self.users]
    
    def get_user_ids_and_server_as_list(self) -> list[int]:
        return [f"{user.id}#{user.server}" for user in self.users]
    
    def get_user_names_as_list(self) -> list[str]:
        return [user.name for user in self.users]
    
    def change_user_name_by_id(self, user_id:int, new_name:str) -> None:
        self.users[self.get_user_ids_as_list().index(int(user_id))].name = new_name
    
    def change_points_by_id(self, user_id:int, points:int) -> None:
        self.users[self.get_user_ids_as_list().index(int(user_id))].points = points
    
    def load_points(self, data:dict) -> None:
        for user_id in data.keys():
            self.change_points_by_id(user_id, data[user_id])
            
class Points:
    def __init__(self):
        self.points:dict = {}
        
    def load_points(self) -> None:
        with open("data/points.json", "r") as json_file:
            self.points = json.load(json_file)
            
    def save_points(self) -> None:
        with open("data/points.json", "w") as json_file:
            json.dump(self.points, json_file, indent=4)