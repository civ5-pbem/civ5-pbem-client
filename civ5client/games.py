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
    json = interface.get_request('/games/').json()
    for i in range(len(json)):
        json[i]['ref_number'] = i + 1
    return json

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

class Game():
    def __init__(self, interface, json):
        self.interface = interface
        self.json = json
        self.id = json['id']
        
    @classmethod
    def from_number(cls, interface, ref_number):
        game_list = list_games(interface)
        game_json = next(game for game in game_list
            if game['ref_number'] == ref_number)
        return cls(interface, game_json)

    @classmethod
    def from_id(cls, interface, game_id):
        game_list = list_games(interface)
        game_json = next(game for game in game_list
            if game['id'] == game_id)
        return cls(interface, game_json)

    @classmethod
    def from_any(cls, interface, value):
        """
        Initializes from a game ref number or id, and decides which was used 
        as an argument.
        """
        try:
            number = int(value)
            return cls.from_number(interface, number)
        except ValueError:
            player_id = value
            return cls.from_id(interface, player_id)

    def info(self):
        """Returns game json."""
        return self.json

    def find_own_player_id(self):
        """Finds player-id connected to the interface."""
        username = account.request_credentials(interface)['username']
        return next(player for player in self.json['players'] 
            if player['humanUserAccount'] == username)['id']

    def join(self):
        """Requests to join the game with the current account."""
        return self.interface.post_request(
            '/games/'+self.id+'/join')

    def leave(self):
        """Requests to leave a game with the current account."""
        return interface.post_request("/games/"+self.id+"/leave")

class Player():
    def __init__(self, game, json):
        self.interface = game.interface
        self.game = game
        self.json = json
        self.id = json['id']

    @classmethod
    def from_number(cls, game, number):
        return cls(game, next(player for player in game.json['players']
            if player['playerNumber'] == number))

    @classmethod
    def from_id(cls, game, player_id):
        return cls(next(player for player in game.json['players']
            if player['playerNumber'] == number))

    @classmethod
    def from_any(cls, game, value):
        """
        Initializes from a player number or id, and decides which was used as
        an argument.
        """
        try:
            number = int(value)
            return cls.from_number(game, number)
        except ValueError:
            player_id = value
            return cls.from_id(game, player_id)
    
    def change_type(self, player_type):
        """Requests to change type of player."""
        player_type = player_type.upper()
        if player_type not in allowed_player_types:
            raise ValueError("Wrong player type")
        json = {'playerType':player_type}
        return self.interface.post_request("/games/"+self.game.id+
                                           "/players/"+self.id+
                                           "/change-player-type", json)

    def choose_civilization(self, civilzation):
        allowed_civs = list_civilizations(interface)
        civilization = civilization.upper()
        if civilization not in allowed_civs:
            raise ValueError("Civilization not allowed")
        json = {'civilization':civilization}
        return self.interface.post_request("/games/"+self.game.id+
                                           "/players/"+self.id+
                                           "/choose-civilization", json)

    def kick(self):
        return self.interface.post_request("/games/"+self.game.id+
                                           "/players/"+player.id+
                                           "/kick")
