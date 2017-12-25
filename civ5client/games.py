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
            'gameDescription':game_name,
            'mapSize':map_size}
    interface.post_request('/games/new-game', json)
