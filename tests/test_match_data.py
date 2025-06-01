import sys
import os
import json
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from match_data import *
from hero_data import *

with open("data/heronames.json", "r") as json_file:
    hero_list = HeroList(json.load(json_file))

with open("test_data.json", "r") as json_file:
    test_data = json.load(json_file)
    
match_data = test_data["result_body"]["battle_list"]

match_history = MatchHistory([Match(match, hero_list) for match in match_data])

def test_match():
    match = match_history.matches[0]
    assert match.get_own_mvp() == "c1153"
    assert match.get_own_first_pick() == ""
    assert match.get_first_pick() == "c1168"
    assert match.get_own_ban() == "c5110"
    assert match.get_enemy_ban() == "c5071"
    assert len(match.get_all_picks_codes()) == 10
    assert len(match.get_own_picks_codes()) == 5
    assert len(match.get_enemy_picks_codes()) == 5
    
    
# Match history

def test_match_history():
    assert sum(match_history.get_match_result_vector()) >= 0
    assert "c1153" in match_history.get_all_heroes_present_counts().keys()
    assert match_history.get_all_own_pick_counts_by_pick_order([0]).get("c2124") >= 0
    