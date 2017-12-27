"""
This module contains savefile download/upload related actions.
"""

from configparser import ConfigParser
from sys import platform
import glob
import re
import os
from os.path import expanduser

from civ5client import ServerError, InvalidConfigurationError, config_file_name, save_parser

class UnknownOperatingSystemError(Exception):
    """
    Raised when OS-centric behaviour is required yet unknown for current
    operating system.
    """

class MissingSaveFileError(Exception):
    """Raised when a save file is missing for upload."""

def get_default_save_path():
    """Returns the default save path for the user based on the os."""
    # TODO: Confirm it's working, especially on windows
    if platform.startswith("linux"):
        save_dir = "~/.local/share/Aspyr/Sid Meier's Civilization 5/Saves/hotseat/"
    elif platform == "darwin":
        save_dir = "~/Documents/Aspyr/Sid Meier's Civilization 5/Saves/hotseat/"
    elif platform == "win32":
        save_dir = "~\\My Games\\Sid Meier's Civilization 5\\Saves\\hotseat"
    else:
        raise UnknownOperatingSystemError
    return expanduser(save_dir)

def get_config_save_path():
    """Returns the save path from config."""
    config = ConfigParser()
    config.read(config_file_name)
    if (config.has_section('Saves')
            and config.has_option('Saves', 'save_path')):
        path = config['Saves']['save_path']
        if not path.endswith("/"):
            path = path + "/"
        return path
    else:
        raise InvalidConfigurationError

def save_save_path_config(path):
    """Writes save path location to a selected config file."""
    config = ConfigParser()
    config.read(config_file_name)
    if not config.has_section('Saves'):
        config.add_section('Saves')
    config['Saves']['save_path'] = path
    with open(config_file_name, 'w') as config_file:
        config.write(config_file)

def download_save(game):
    """
    Downloads a game savefile from the server and saves it into the
    civilization 5 save directory from config. 
    Returns the name of the file.
    """
    file_name = "temp_save.Civ5Save"
    with open(file_name, 'wb') as file_:
        response = game.interface.get_request("/games/"+game.id+"/save-game",
                                 stream=True)
        for chunk in response.iter_content():
            file_.write(chunk)
    turn, current, password_list, dead = save_parser.parse_file(file_name)

    final_name = game.name+" "+str(turn)+".Civ5Save"
    path = get_config_save_path()+final_name
    os.rename(file_name, path) # May throw OSError if already exists on windows
    return path

def confirm_password(game, file_name):
    """
    Checks if password had been set to warn the user in case he might have
    forgot.
    """
    turn, current, password_list, dead = save_parser.parse_file(file_name)
    if password_list[game.find_own_player_number-1]:
        return True
    return False

def validate_upload_file(game, file_name):
    """
    Checks if a savefile is valid for upload to a specific game end point, 
    i.e. if the turn had been made and password set.
    """
    turn, current, password_list, dead = save_parser.parse_file(file_name)
    current += 1 # Correction for 0 vs 1 indexing

    turn_server = game.get_turn() # TODO SERVERSIDE: SHOULD RETURN CURRENT TURN
    current_server = game.currently_moving_player_number()
    last_player_number = game.last_human_player_number()

    # Whether the turn had been correctly done
    turn_error_message = "Turn number mismatch; complete turn"
    if last_player_number == current_server:
        if turn != turn_server+1:
            return False, turn_error_message
        if current != 0:
            return False, turn_error_message
    elif turn != turn_server or current != current_server+1:
        return False, turn_error_message

    return True, ""

def select_upload_file(game):
    """Chooses the file to upload."""
    # TODO: actually be reasonable when more than 1 correct game.name*.Civ5Save exists
    path = get_config_save_path()
    l = glob.glob(path+game.name+"*.Civ5Save")
    if not l:
        raise MissingSaveFileError
    return l[0]

def upload_save(game):
    """
    Uploads a savefile from the civilization 5 save directory corresponding to
    the game (i.e. starting with the name of the game) and removes the file.
    Returns the name of the removed file.
    """
    file_name = select_upload_file(game)
    files = {'file':open(file_name, 'rb')}
    request = game.interface.post_request("/games/"+game.id+"/finish-turn",
                                          files=files)
    os.remove(file_name)
    return file_name
