import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hero_data import *


def test_hero_popularity():
    hero_popularity = HeroPopularity()
    assert hero_popularity.get_popularity("test") == 0
    hero_popularity.increase_popularity("test")
    assert hero_popularity.get_popularity("test") == 1
    
with open("data/heronames.json", "r") as json_file:
    hero_list = HeroList(json.load(json_file))

def test_hero_list_get():
    assert hero_list.get_hero_by_name("krau") is not None
    assert hero_list.get_hero_by_name("nonexistent name") is None
    assert hero_list.get_hero_by_code("c1070") is not None
    assert hero_list.get_hero_by_code("nonexistent code") is None
    assert len(hero_list.get_hero_vector_dict()) == len(hero_list.hero_list)

def test_hero_list_find():
    assert len(hero_list.find_by_name("krau")) == 3
    assert len(hero_list.find_by_name("nonexistent name")) == 0

def test_find_up_to_n_most_popular_by_name():
    hero_popularity = HeroPopularity()
    hero_popularity.increase_popularity("c1070")
    assert hero_list.find_up_to_n_most_popular_by_name("krau", 5, hero_popularity)[0].code == "c1070"
    assert len(hero_list.find_up_to_n_most_popular_by_name("krau", 5, hero_popularity)) == 3