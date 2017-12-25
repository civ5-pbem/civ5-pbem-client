#!/usr/bin/env python3
"""
Script to make full use of the civ5client package to play Civilizations 5 in 
a play-by-email fashion in connection with a dedicated civ5-pbem-server.

Usage:
    cli-client.py init
    cli-client.py new-game <game-name> <game-description> <map-size>
    cli-client.py (-h | --help)
    cli-client.py --version

Commands:
    -h --help   Show this
    --version   Show version
    init        Checks configuration and completes it if incomplete. 
                It is ran whenever any other command is used regardless.
    new-game    Sends out a request to start a new game with a given name,
                description and a chosen size.

Map sizes:
    duel      max 2 players and 4 city states
    tiny      max 4 players and 8 city states
    small     max 6 players and 12 city states
    standard  max 8 players and 16 city states
    large     max 10 players and 20 city states
    huge      max 12 players and 24 city states
"""

from docopt import docopt
from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse, urljoin
import requests

import civ5client
from civ5client import account, saves, games, InvalidConfigurationError

opts = docopt(__doc__, help=True, version=("civ5client command line interface "
                                           "pre-alpha"))

config_file = 'config.ini'

def yes_no_question(question):
    answer = input(question+" [y/n]: ")
    if len(answer) > 0 and answer[0] in ['y','Y']:
        return True
    else:
        return False

try:
    #
    # Registration and credentials
    #
    try:
        interface = civ5client.Interface.from_config(config_file)
    except InvalidConfigurationError:
        print("Missing or invalid config; creating new one")
        address = input("Write the server address: ")
        address = civ5client.parse_address(address)
        registered = yes_no_question(("Do you have an access token (i.e. an"
                                      " account) already?"))
        if not registered:
            username = input("Please choose your username: ")
            email = input("Please write you email: ")
            print("Registering account")
            try:
                account.register_account(address, username, email)
            except account.AccountTakenError:
                # TODO: Should be a loop asking for different emails
                print("Error: Email already taken")
                exit()
            else:
                print("An email with the access token has been sent")
        access_token = input("Write the access token from the email: ")
        interface = civ5client.Interface(address, access_token)
        print("Saving interface credentials to config")
        interface.save_config(config_file)
    try:
        credentials = account.request_credentials(interface)
        print("Logged in as", credentials.get('username'),
              "with email", credentials.get('email'))
    except:
        print("Error: Failed to retrieve credentials")
        exit()
    #
    # Retrieve Civ 5 save directory path
    #
    try:
        path = saves.get_config_save_path(config_file)
    except InvalidConfigurationError:
        print("No save directory path in config; attempting to find it")
        try:
            path = saves.get_default_save_path()
        except saves.UnknownOperatingSystemError:
            path = input(("Unknown operating system. Please write the absolute"
                          " Civilizations 5 directory path: "))
        print("Saving save directory path to config")
        saves.save_save_path_config(config_file, path)
    #
    # Commands
    #
    if opts['new-game']:
        try:
            print("Sending a new game request")
            games.start_new_game(interface,
                                 opts['<game-name>'],
                                 opts['<game-description>'],
                                 opts['<map-size>'].upper())
        except ValueError:
            print("Error: Wrong map size. Check -h for possible")
            exit()
except requests.exceptions.ConnectionError:
    print("Error: Failed to connect to server")
    exit()
