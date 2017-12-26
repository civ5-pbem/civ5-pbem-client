#!/usr/bin/env python3
"""
cli-client.py
=============
Script to make full use of the civ5client package to play Civilization 5 in 
a play-by-email fashion in connection with a dedicated civ5-pbem-server.

Usage:
    cli-client.py init
    cli-client.py new-game <game-name> <game-description> <map-size>
    cli-client.py (list-games | list-civilizations)
    cli-client.py (game-info | join-game) <game-id>
    cli-client.py change-player-type <game-id> <player-id> <player-type>
    cli-client.py kick <game-id> <player-id>
    cli-client.py (join | leave) <game-id>
    cli-client.py choose-civilization <game-id> [--player-id=<id>] <civilization>
    cli-client.py (-h | --help)
    cli-client.py --version

Commands:
    -h --help               Show this
    --version               Show version
    init                    Checks configuration and completes it if incomplete. 
                            It is ran whenever any other command is used regardless.
    new-game                Sends a request to start a new game with a given name,
                            description and a chosen size.
    list-games              Requests a list of games from the server and prints it
    game-info               Prints detailed information about a game with a given id
    join-game               Asks the server to join a game with a given id
    change-player-type      Changes the type of a player in a game

Map sizes:
    duel      max 2 players and 4 city states
    tiny      max 4 players and 8 city states
    small     max 6 players and 12 city states
    standard  max 8 players and 16 city states
    large     max 10 players and 20 city states
    huge      max 12 players and 24 city states

Player types:
    human
    ai
    closed
"""

from docopt import docopt
from configparser import ConfigParser
import requests

import civ5client
from civ5client import account, saves, games, InvalidConfigurationError, ServerError

opts = docopt(__doc__, help=True, version=("civ5client command line interface "
                                           "pre-alpha"))

config_file = 'config.ini'

def yes_no_question(question):
    answer = input(question+" [y/n]: ")
    if len(answer) > 0 and answer[0] in ['y','Y']:
        return True
    else:
        return False

def pretty_print_game(json):
    print("ID:", json['id'],
          "\nName:", json['name'],
          "\nHost:", json['host'],
          "\nDescription:", json['description'],
          "\nMap size:", json['mapSize'],
          "\nGame state:", json['gameState'],
          "\nPlayers:")
    for player in json['players']:
        print("\tID:", player['id'],
              "\n\t\tUser:", player['humanUserAccount'],
              "\n\t\tNumber:", player['playerNumber'],
              "\n\t\tCivilization:", player['civilization'],
              "\n\t\tPlayer Type:", player['playerType'])
    print("Number of city states:", json['numberOfCityStates'])

try:
    #
    # Registration and credentials
    #
    try:
        interface = civ5client.Interface.from_config(config_file)
    except InvalidConfigurationError:
        if not opts['init']:
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
        if opts['init']:
            print("Logged in as", credentials.get('username'),
                  "with email", credentials.get('email'))
    except:
        print(("Error: Failed to retrieve credentials. Either server "
               "is broken or configuration is wrong. Check server_address "
               "and access_token in config.ini, or remove it to configure "
               "again."))
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
            print("Attempting to send a new game request")
            response = games.start_new_game(interface,
                                 opts['<game-name>'],
                                 opts['<game-description>'],
                                 opts['<map-size>'].upper())
        except ValueError:
            print("Error: Wrong map size. Check -h for possible")
            exit()
        except ServerError:
            print("Error: Server error")
            exit()
        else:
            print("Game started successfully with id", 
                  response.json()['id'])

    if opts['list-games']:
        json = games.list_games(interface)
        for game in json:
            string = 'ID: {}\tName: {:12}\tHost: {:12}'.format(
                game['id'], game['name'], game['host'])
            print(string)

    if opts['game-info']:
        json = games.game_info(interface, opts['<game-id>'])
        pretty_print_game(json)

    if opts['join-game']:
        try:
            response = games.join_game(interface, opts['<game-id>'])
            pretty_print_game(response.json())
        except ServerError:
            print("Error: Failed to join game. Presumably you are already in it")
            exit()

    if opts['list-civilizations']:
        json = games.get_civilizations(interface).json()
        base_string = "{:8}\t{:8}\t{:8}"
        print(base_string.format("Code", "Name", "Leader"))
        for civ in json:
            print(base_string.format(civ['code'],
                                     civ['name'],
                                     civ['leader']))

    if opts['change-player-type']:
        games.change_player_type(interface,
                                opts['<game-id>'],
                                opts['<player-id>'],
                                opts['<player-type>'])

    if opts['choose-civilization']:
        games.choose_civilization(interface,
                                  opts['<game-id>'],
                                  opts['<civilization>'],
                                  player_id=opts['--player-id'])

    if opts['kick']:
        games.kick(interface,
                   opts['<game-id>'],
                   opts['<player-id>'])

    if opts['join']:
        games.join(interface,
                   opts['<game-id>'])
       
    if opts['leave']:
        games.leave(interface,
                    opts['<game-id>'])

except requests.exceptions.ConnectionError:
    print("Error: Failed to connect to server")
    exit()
