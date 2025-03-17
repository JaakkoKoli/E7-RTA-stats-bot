import json

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
            return self.get_name_with_server() == user2.get_name_with_server()
        return self.get_name_with_server() == user2
    
    def __lt__(self, user2) -> bool:
        if isinstance(user2, User):
            return self.get_name_with_server() < user2.get_name_with_server()
        return self.get_name_with_server() < user2
        

class UserData:
    def __init__(self):
        self.users:list[User] = []
        self.index:dict = dict()
    
    def read_data(self, data:object, server:str) -> None:
        for user in data["users"]:
            self.users.append(User(int(user["nick_no"]), user["nick_nm"].lower(), int(user["rank"]), user["code"], server))
        self.users.sort()
    
    def create_search_index(self) -> None:
        start_chars = list({user.name[0] for user in self.users})
        start_chars.sort()
        index = dict()
        current_start_char = 0
        start_i = 0
        for i, user in enumerate(self.users):
            if user.name[0] != start_chars[current_start_char]:
                index[start_chars[current_start_char]] = [start_i, i]
                start_i = i
                current_start_char += 1
        index[start_chars[current_start_char]] = [start_i, len(self.users)-1]
        self.index = index
        
            
    def find_user(self, search_query:str) -> list[User]:
        if len(search_query) == 0:
            return []
        search_query = search_query.lower()
        search_area = self.index[search_query[0]]
        matches = []
        for user in self.users[search_area[0]:search_area[1]]:
            if search_query in user.name:
                matches.append(user)
        return matches
    
    def get_user(self, user_name:str, server:str) -> User:
        for user in self.users[self.index[user_name[0]][0]:self.index[user_name[0]][1]]:
            if user.name == user_name and user.server == server:
                return user
        return None
    
    def get_user_ids_as_list(self) -> list[int]:
        return [user.id for user in self.users]
    
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