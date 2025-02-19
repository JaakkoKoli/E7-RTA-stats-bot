import requests
import json

def get_new_userdata(server:str) -> None:
    response = requests.get(f"https://static.smilegatemegaport.com/gameRecord/epic7/epic7_user_world_{server}.json")
    if response.status_code == 200:
        with open(f"epic7_user_world_{server}.json", 'w') as file:
            json.dump(response.json(), file)
        print(f"File saved successfully as epic7_user_world_{server}.json")
    else:
        print("Failed to download file")

for server in ["asia","eu","global","jpn","kor"]:
    get_new_userdata(server)