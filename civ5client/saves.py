"""
This module contains savefile download/upload related actions.
"""

from configparser import ConfigParser
from sys import platform
from os.path import expanduser

from civ5client import InvalidConfigurationError

class UnknownOperatingSystemError(Exception):
    """
    Raised when OS-centric behaviour is required yet unknown for current
    operating system.
    """

def get_default_save_path():
    """Returns the default save path for the user based on the os."""
    # TODO: Confirm it's working, especially on windows
    if platform.startswith("linux"):
        save_dir = "~/.local/share/Aspyr/Sid Meier's Civilization 5/Saves"
    elif platform == "darwin":
        save_dir = "~/Documents/Aspyr/Sid Meier's Civilization 5/Saves"
    elif platform == "win32":
        save_dir = "~/My Games/Sid Meier's Civilization 5/Saves"
    else:
        raise UnknownOperatingSystemError
    return expanduser(save_dir)

def get_config_save_path(config_file_name):
    """Returns the save path from config."""
    config = ConfigParser()
    config.read(config_file_name)
    if (config.has_section('Saves')
            and config.has_option('Saves', 'save_path')):
        return config['Saves']['save_path']
    else:
        raise InvalidConfigurationError

def save_save_path_config(config_file_name, path):
    """Writes save path location to a selected config file."""
    config = ConfigParser()
    config.read(config_file_name)
    if not config.has_section('Saves'):
        config.add_section('Saves')
    config['Saves']['save_path'] = path
    with open(config_file_name, 'w') as config_file:
        config.write(config_file)
