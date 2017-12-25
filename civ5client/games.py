"""
This module contains game initialization & listing related actions.
"""

from enum import Enum

allowed_sizes = ['DUEL', 'TINY', 'SMALL', 'STANDARD', 'LARGE', 'HUGE']

def start_new_game(interface, game_name, game_description, map_size):
    """Sends a request to start a new game."""
    if map_size not in allowed_sizes:
        raise ValueError("Wrong map size")
    json = {'gameName':game_name,
            'gameDescription':game_description,
            'mapSize':map_size}
    return interface.post_request('/games/new-game', json)

def list_games(interface):
    """
    Sends a request to retrieve a list of games to join/currently played and 
    outputs the response json.
    """
    return interface.get_request('/games/').json()

def game_info(interface, game_id):
    """Sends a request for detailed info about a game and prints out the json."""
    return interface.get_request('/games/'+game_id).json()

def join_game(interface, game_id):
    """Sends a request to join a game."""
    return interface.post_request('/games/'+game_id+'/join')
