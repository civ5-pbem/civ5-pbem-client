"""
This module contains game initialization & listing related actions.
"""

from enum import Enum

from civ5client import account, saves

allowed_sizes = ['DUEL', 'TINY', 'SMALL', 'STANDARD', 'LARGE', 'HUGE']
allowed_player_types = ['HUMAN', 'AI', 'CLOSED']

class InvalidReferenceNumberError(Exception):
    """
    Raised when user tries to retrieve a game or player with a non-existant
    ref_number.
    """

class InvalidNameError(Exception):
    """
    Raised when user tries to retrieve a game or player with a non-existent
    name.
    """

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
        self.name = json['name']
        
    @classmethod
    def from_number(cls, interface, ref_number):
        game_list = list_games(interface)
        try:
            game_json = next(game for game in game_list
                if game['ref_number'] == ref_number)
        except StopIteration:
            raise InvalidReferenceNumberError
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
        username = account.request_credentials(self.interface)['username']
        return Player.from_name(self, username).id

    def find_own_player_number(self):
        """Returns the number of the currently moving player."""
        return Player.from_name(self, username).number

    def to_move(self, can_host=True):
        """
        Returns whether the player connected to the interface is supposed to do
        the next move.
        """
        username = account.request_credentials(self.interface)['username']
        if self.json['currentlyMovingPlayer'] == username:
            return True 
        elif (self.json['host'] == username 
              and self.json['gameState'] == 'WAITING_FOR_FIRST_MOVE'
              and can_host):
            return True
        else:
            return False
    
    def currently_moving_player_number(self):
        """Returns the number of the currently moving player."""
        return Player.from_name(self, self.json['currentlyMovingPlayer']).number

    def last_human_player_number(self):
        """
        Returns the number of the last human player on the list of
        players, so the one after whom the turn number goes up.
        """
        i = 0
        for player in self.json['players']:
            if player['playerType'] == 'HUMAN':
                i = player['playerNumber']
        return i

    def number_of_human_players(self):
        """Returns the number of human players."""
        i = 0
        for player in self.json['players']:
            if player['playerType'] == 'HUMAN':
                i += 1
        return i


    def join(self):
        """Requests to join the game with the current account."""
        return self.interface.post_request(
            '/games/'+self.id+'/join')

    def leave(self):
        """Requests to leave a game with the current account."""
        return self.interface.post_request("/games/"+self.id+"/leave")
    
    def start(self):
        """Requests to start a game."""
        return self.interface.post_request("/games/"+self.id+"/start")

    def download(self):
        """Downloads the save if it's your turn."""
        if self.to_move(can_host=False):
            return saves.download_save(self)

    def upload(self):
        """Uploads the save and finishes the turn."""
        if self.to_move():
            return saves.upload_save(self)

class Player():
    def __init__(self, game, json):
        self.interface = game.interface
        self.game = game
        self.json = json
        self.id = json['id']
        self.number = json['playerNumber']

    # TODO: Unused
    @classmethod
    def from_name(cls, game, name):
        try:
            return cls(game, next(player for player in game.json['players']
                if player['humanUserAccount'] == name))
        except StopIteration:
            raise InvalidNameError

    @classmethod
    def from_number(cls, game, number):
        try:
            return cls(game, next(player for player in game.json['players']
                if player['playerNumber'] == number))
        except StopIteration:
            raise InvalidReferenceNumberError

    @classmethod
    def from_id(cls, game, player_id):
        return cls(game, next(player for player in game.json['players']
            if player['id'] == player_id))

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

    def choose_civilization(self, civilization):
        allowed_civs = list_civilizations(self.interface)
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
