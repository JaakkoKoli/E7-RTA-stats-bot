import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from search_history import *

search_history = SearchHistory()

def test_search_history():
    assert len(search_history.get_user_history("test_id")) == 0
    search_history.add_search_query("test_id", "query1")
    search_history.add_search_query("test_id", "query2")
    search_history.add_search_query("test_id", "query3")
    search_history.add_search_query("test_id", "query4")
    assert sum([query in search_history.get_user_history("test_id") for query in ["query2", "query3", "query4"]]) == 3
    assert search_history.get_user_history("test_id")[0] == "query4"
    search_history.add_search_query("test_id", "query3")
    assert search_history.get_user_history("test_id")[0] == "query3"