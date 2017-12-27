#!/usr/bin/env python3
"""
cli-client.py
=============
Script to make full use of the civ5client package to play Civilization 5 in 
a play-by-email fashion in connection with a dedicated civ5-pbem-server.

Usage:
    cli-client.py init
    cli-client.py new-game <game-name> <game-description> <map-size>
    cli-client.py (list | list-civs)
    cli-client.py (info | join | leave | start | download | upload | disable-validation) <game>
    cli-client.py kick <game> <player>
    cli-client.py choose-civ <game> [<player>] <civilization>
    cli-client.py change-player-type <game> <player> <player-type>
    cli-client.py (-h | --help)
    cli-client.py --version

    <game> can be either a game id or reference number (first given by list)
    <player> can be either a player id or the player number in a game

Commands:
    -h --help               Show this
    --version               Show version

    init                    Checks configuration and completes it if incomplete. 
                            It is ran whenever any other command is used regardless.

    new-game                Sends a request to start a new game with a given name,
                            description and a chosen size.

    list                    Prints a list of existing games
    list-civs               Prints a list of allowed civs
        
    info                    Prints detailed information about a game
    join                    Requests to join a game
    leave                   Requests to leave a game
    kick                    Requests to kick a player
    start                   Requests to start a game

    download                Downloads a save (when it's your turn to move)
    upload                  Uploads and removes a save, performs the next turn

    choose-civ              Changes your own civilization. If <player> is
                            provided and you're the host, it allows you 
                            to change AI's civ

    change-player-type      Changes the type of a player (ai, human or closed)

    disable-validation      Turns off server-side validation for a turn,
                            meaning a save after multiple turns and moves can 
                            be uploaded. Meant for periods of local hotseat 
                            when all players are present to save time and get 
                            on with the game faster. Only host can do this.

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
import requests

import civ5client
from civ5client import account, saves, games, InvalidConfigurationError, ServerError
from civ5client.games import InvalidReferenceNumberError
from civ5client.saves import MissingSaveFileError

opts = docopt(__doc__, help=True, version=("civ5client command line interface "
                                           "beta"))

def yes_no_question(question):
    answer = input(question+" [y/n]: ")
    if len(answer) > 0 and answer[0] in ['y','Y']:
        return True
    else:
        return False

def pretty_print_game(game_json, civ_json):
    print("ID:", game_json['id'],
          "\nName:", game_json['name'],
          "\nHost:", game_json['host'],
          "\nDescription:", game_json['description'],
          "\nMap size:", game_json['mapSize'],
          "\nGame state:", game_json['gameState'],
          "\nTurn started:", game_json['lastMoveFinished'],
          "\nCurrent player:", game_json['currentlyMovingPlayer'],
          "\nPlayers:")
    for player in game_json['players']:
        civ = next(civ for civ in civ_json
                          if civ['code'] == player['civilization'])
        civ_string = civ['code']+" - "+civ['leader']+" - "+civ['name']
        print("\tID:", player['id'],
              "\n\t\tUser:", player['humanUserAccount'],
              "\n\t\tNumber:", player['playerNumber'],
              "\n\t\tCivilization:", civ_string,
              "\n\t\tPlayer Type:", player['playerType'])
    print("Number of city states:", game_json['numberOfCityStates'])

try:
    #
    # Registration and credentials
    #
    try:
        interface = civ5client.Interface.from_config()
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
                print("Error: Account already taken")
                exit()
            else:
                print("An email with the access token has been sent")
        access_token = input("Write the access token from the email: ")
        interface = civ5client.Interface(address, access_token)
        print("Saving interface credentials to config")
        interface.save_config()
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
    # Confirm we have a save directory path in config
    #
    try:
        saves.get_config_save_path()
    except InvalidConfigurationError:
        print("No save directory path in config; attempting to find it")
        try:
            path = saves.get_default_save_path()
        except saves.UnknownOperatingSystemError:
            path = input(("Unknown operating system. Please write the absolute"
                          " Civilizations 5 hotseat save directory path: "))
        print("Saving save directory path to config")
        saves.save_save_path_config(path)
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

    if opts['list']:
        json_list = games.list_games(interface)
        for json in json_list:
            string = '{:3}) ID: {}\tName: {:12}\tHost: {:12}'.format(
                json['ref_number'], json['id'], json['name'], json['host'])
            game = games.Game(interface, json)
            if game.to_move():
                string += " <- Your move"
            print(string)

    if opts['list-civs']:
        json = games.get_civilizations(interface).json()
        base_string = "{:8}\t{:8}\t{:8}"
        print(base_string.format("Code", "Name", "Leader"))
        for civ in json:
            print(base_string.format(civ['code'],
                                     civ['name'],
                                     civ['leader']))


    if opts['<game>']:
        game = games.Game.from_any(interface, opts['<game>'])
        if opts['<player>']:
            player = games.Player.from_any(game, opts['<player>'])

    if opts['info']:
        civ_json = games.get_civilizations(interface).json()
        pretty_print_game(game.json, civ_json)

    if opts['join']:
        try:
            response = game.join()
            civ_json = games.get_civilizations(interface).json()
            pretty_print_game(response.json(), civ_json)
        except ServerError:
            print("Error: Failed to join game. Presumably you are already in it")
            exit()

    if opts['leave']:
        game.leave()

    if opts['kick']:
        player.kick()

    if opts['start']:
        try:
            game.start()
        except ServerError:
            print("Error: Server error; game probably already started")

    if opts['disable-validation']:
        game.disable_validation()

    if opts['change-player-type']:
        try:
            player.change_type(opts['<player-type>'])
        except ValueError:
            print("Error: Wrong player type")

    if opts['choose-civ']:
        if opts['<player>']:
            player = games.Player.from_any(game, opts['<player>'])
        else:
            player = games.Player.from_id(game, game.find_own_player_id())
        try:
            player.choose_civilization(opts['<civilization>'])
        except ValueError:
            print("Error: Wrong civilization. list-civs to list acceptable civs")

    if opts['download']:
        try:
            file_name = game.download()
            print("Downloaded",file_name)
            print(("Please complete your turn by loading it in hotseat mode, "
                   "performing a turn, saving it in the menu so that the next "
                   "player can continue and uploading it to the server."))
        except OSError:
            print("Error: File with wanted name already exists")

    if opts['upload']:
        try:
            if not saves.confirm_password(game):
                print("Warning: Password not set. You should download the save again and set it")
                if not yes_no_question(
                        ("Are you sure you want to continue and upload it "
                    "regardless?")):
                    exit()
            file_name = game.upload()
            print("Uploaded and removed", file_name, "without errors")
        except MissingSaveFileError:
            print("Error: Save file ",game.name,".Civ5Save missing", sep="")

except requests.exceptions.ConnectionError:
    print("Error: Failed to connect to server")
    exit()
except InvalidReferenceNumberError:
    print("Error: No game or player with such reference number")
except ServerError as e:
    print("Server error:", e.args[0])
