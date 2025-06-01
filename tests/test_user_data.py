import sys
import os
import json
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from user_data import *

user_data = UserData()
with open(f"test_user_data.json", "r") as json_file:
    server_user_data = json.load(json_file)
    user_data.read_data(server_user_data, "global")
user_data.create_search_index()    

def test_user_data():
    assert len(user_data.find_user("----------test-----------")) == 0
    assert len(user_data.find_user("ahn")) > 0
    assert user_data.get_user("Heyst", "global") is not None
    assert user_data.get_user_by_id("60089368", "global").name == "heyst"
    user_data.change_user_name_by_id("60089368", "newname")
    assert user_data.get_user_by_id("60089368", "global").name == "newname"
    user_data.change_points_by_id("60089368", 100)
    assert user_data.get_user_by_id("60089368", "global").points == 100
    
    