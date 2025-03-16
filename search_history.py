import json

class SearchHistory:
    
    def __init__(self):
        self.history:dict[str: list[str]] = dict()
        
    def get_user_history(self, user_id:str) -> list[str]:
        return self.history.get(str(user_id), [])
    
    def add_search_query(self, user_id:str, search_query:str) -> None:
        user_id = str(user_id)
        history = self.get_user_history(user_id)
        if len(history) < 3:
            self.history[user_id] = [search_query] + history
        else:
            self.history[user_id] = [search_query] + history[1:]
    
    def save_search_history(self) -> None:
        with open("data/search_history.json", "w") as json_file:
            json.dump(self.history, json_file, indent=4)
            
    def load_search_history(self) -> None:
        try:
            with open("data/search_history.json", "r") as json_file:
                self.history = json.load(json_file)
        except:
            print("File search_history.json not found")