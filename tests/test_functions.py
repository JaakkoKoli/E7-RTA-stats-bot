import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from functions import create_winrate_graph

def test_create_winrate_graph():
    assert len(create_winrate_graph([0.5]*100)) == 68
    assert len(create_winrate_graph([0.5]*30)) == 30
    assert len(create_winrate_graph([])) == 100