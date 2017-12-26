"""
This module contains game initialization & listing related actions.
"""

from enum import Enum

from civ5client import account

allowed_sizes = ['DUEL', 'TINY', 'SMALL', 'STANDARD', 'LARGE', 'HUGE']
allowed_player_types = ['HUMAN', 'AI', 'CLOSED']

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

def get_own_player_id(interface, game_id):
    """Finds player-id in a game of the account connected to the interface."""
    username = account.request_credentials(interface)['username']
    game_json = game_info(interface, game_id)
    return next(player for player in game_json['players'] 
        if player['humanUserAccount'] == username)['id']

def join_game(interface, game_id):
    """Sends a request to join a game and returns the response."""
    return interface.post_request('/games/'+game_id+'/join')

def change_player_type(interface, game_id, player_id, player_type):
    """Sends a request to change the type of a player (human, ai or closed)."""
    player_type = player_type.upper()
    if player_type not in allowed_player_types:
        raise ValueError("Wrong player type")
    json = {'playerType':player_type}
    return interface.post_request("/games/"+game_id+
                                  "/players/"+player_id+
                                  "/change-player-type", json)

def get_civilizations(interface):
    """Returns a get request to get info about acceptable civilizations."""
    return interface.get_request("/civilizations")

def list_civilizations(interface):
    """Retrieves a list of acceptable civilizations from the server."""
    json = get_civilizations(interface).json()
    output = []
    for civ in json:
        output.append(civ['code'])
    return output

def choose_civilization(interface, game_id, civilization, player_id=None):
    allowed_civilizations = list_civilizations(interface)
    civilization = civilization.upper()
    if civilization not in allowed_civilizations:
        raise ValueError("Civilization not allowed")
    if player_id is None:
        player_id = get_own_player_id(interface, game_id)
    json = {'civilization':civilization}
    return interface.post_request("/games/"+game_id+
                                  "/players/"+player_id+
                                  "/choose-civilization", json)

def kick(interface, game_id, player_id):
    return interface.post_request("/games/"+game_id+
                                  "/players/"+player_id+
                                  "/kick")

def join(interface, game_id):
    return interface.post_request("/games/"+game_id+"/join")

def leave(interface, game_id):
    return interface.post_request("/games/"+game_id+"/leave")

