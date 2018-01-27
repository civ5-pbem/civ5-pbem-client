"""
This module contains savefile download/upload related actions.
"""

from configparser import ConfigParser
from sys import platform
import glob
import re
import shutil
import os
from os.path import expanduser

from progress.bar import Bar

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
        save_dir = "~\\Documents\\My Games\\Sid Meier's Civilization 5\\Saves\\hotseat"
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
        if not path.endswith("/") and platform != "win32":
            path = path + "/"
        elif not path.endswith("\\") and platform == "win32":
            path = path + "\\"
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

def download_save(game, bar=False):
    """
    Downloads a game savefile from the server and saves it into the
    civilization 5 save directory from config. 
    Returns the name of the file.
    """
    file_name = "temp_save.Civ5Save"
    with open(file_name, 'wb') as file_:
        response = game.interface.get_request("/games/"+game.id+"/save-game",
                                 stream=True)
        if bar:
            file_length = int(response.headers['Content-Length'])
            bar = Bar('Downloading', max=100)
            one_percent = int(file_length/100)
            i = 0
        for chunk in response.iter_content():
            file_.write(chunk)
            if bar:
                i += 1
                if i >= one_percent:
                    bar.next()
                    i = 0
        if bar:
            bar.finish()
    final_name = game.name+" "+str(game.turn)+".Civ5Save"
    path = get_config_save_path()+final_name
    shutil.move(file_name, path) # May throw OSError if already exists on windows
    return path, response

# Unfinished
def check_kills(game, file_name=None):
    """
    Compares the game status on the server and in the save and checks if
    anyone died on the current turn."""
    if file_name is None:
        file_name = select_upload_file(game)

def validate_upload_file(game, file_name=None):
    """
    Checks if a savefile is valid for upload to a specific game end point, 
    i.e. if the turn had been made.
    """
    if file_name is None:
        file_name = select_upload_file(game)
    save = save_parser.parse_file(file_name)

    turn_server = game.turn
    current_server = game.currently_moving_player_number()
    last_player_server = game.last_human_player_number()
    first_player_server = game.first_human_player_number()
    
    # Whether the turn had been correctly done
    if last_player_server == current_server:
        if save['turn'] != turn_server+1:
            return False
        if save['current'] != save['first_player']:
            return False
    elif save['turn'] != turn_server or save['current']+1 <= current_server:
        return False

    return True

def select_upload_file(game):
    """Chooses the file to upload and returns its path."""
    path = get_config_save_path()
    desired_name_bulk = path+game.name
    if game.json['gameState'] == 'WAITING_FOR_FIRST_MOVE':
        desired_name = desired_name_bulk + ".Civ5Save"
    else:
        desired_name = desired_name_bulk + " " + str(game.turn) + ".Civ5Save"
    l = glob.glob(desired_name)
    if not l:
        raise MissingSaveFileError(desired_name)
    return l[0]

def confirm_password(game, file_name=None):
    """Checks if the user set his password."""
    if file_name is None:
        file_name = select_upload_file(game)
    password_list = save_parser.parse_file(file_name)['password_list']
    if password_list[game.find_own_player_number()-1]:
        return True
    return False

def upload_save(game, file_name=None):
    """
    Uploads a savefile from the civilization 5 save directory corresponding to
    the game (i.e. starting with the name of the game) and removes the file.
    Returns the name of the removed file.
    """
    if file_name is None:
        file_name = select_upload_file(game)
    files = {'file':open(file_name, 'rb')}
    response = game.interface.post_request("/games/"+game.id+"/finish-turn",
                                           files=files)
    config = ConfigParser()
    config.read(config_file_name)
    if (config.has_section('Saves')
            and config.has_option('Saves', 'delete_saves')):
        if config['Saves']['delete_saves'].lower() == 'true':
            os.remove(file_name)
    return file_name, response
