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
    cli-client.py info <game> [--verbose]
    cli-client.py (join | leave | start | disable-validation) <game>
    cli-client.py (download | upload) <game> [--force] 
    cli-client.py kick <game> <player> 
    cli-client.py choose-civ <game> <player> <civilization> 
    cli-client.py choose-civ <game> <civilization> 
    cli-client.py change-player-type <game> <player> <player-type> 
    cli-client.py (-h | --help)
    cli-client.py --version

    <game> can be either a game id or reference number (first given by list)
    <player> can be either a player id or the player number in a game

Commands:
    -h --help               Show this
    --version               Show version
    --force                 Forces an attempt to perform an action without
                            clientside validation
    --verbose, -v           Prints more information

    init                    Checks configuration and completes it if incomplete. 
                            It is ran whenever any other command is used regardless.

    new-game                Sends a request to start a new game with a given name,
                            description and a chosen size.

    list                    Prints a list of existing games
    list-civs               Prints a list of allowed civs
        
    info                    Prints information about a game

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
import sys
import time
import traceback

from docopt import docopt
from configparser import ConfigParser
import requests

import civ5client
from civ5client import account, saves, games, InvalidConfigurationError, ServerError, config_file_name
from civ5client.games import InvalidReferenceNumberError, WrongMoveError, InvalidIdError
from civ5client.saves import MissingSaveFileError

opts = docopt(__doc__, help=True, version=("civ5client command line interface "
                                           "v0.1.0"))

def yes_no_question(question):
    answer = input(question+" [y/n]: ")
    if len(answer) > 0 and answer[0] in ['y','Y']:
        return True
    else:
        return False

def pretty_print_game(game_json, civ_json, short=False):
    if not short:
        print("ID:", game_json['id'],
              "\nName:", game_json['name'],
              "\nHost:", game_json['host'],
              "\nDescription:", game_json['description'],
              "\nMap size:", game_json['mapSize'],
              "\nGame state:", game_json['gameState'],
              "\nTurn started:", game_json['lastMoveFinished'],
              "\nTurn number:", game_json['turnNumber'],
              "\nCurrent player:", game_json['currentlyMovingPlayer'],
              "\nSave file validation:", game_json['isSaveGameValidationEnabled'],
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
    else:
        print("Name:", game_json['name'],
              "\nHost:", game_json['host'],
              "\nDescription:", game_json['description'],
              "\nTurn number:", game_json['turnNumber'],
              "\nCurrent player:", game_json['currentlyMovingPlayer'])

try:
    #
    # Initial config
    #
    config = ConfigParser()
    config.read(config_file_name)
    if not config.has_section('Client Settings'):
        config.add_section('Client Settings')
    if (not config.has_option('Client Settings', 'log_name')
            or not config.has_option('Client Settings', 'log_responses')):
        if not opts['init']:
            print("Missing or incomplete config; attempting to fix")
        config['Client Settings']['log_name'] = "log.txt"
        config['Client Settings']['log_responses'] = "False"
        config.write(open(config_file_name, 'w'))
    log_name = config['Client Settings']['log_name']
    #
    # Registration and credentials
    #
    try:
        interface = civ5client.Interface.from_config()
    except InvalidConfigurationError:
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
                raise
            else:
                print("An email with the access token has been sent")
        access_token = input("Write the access token from the email: ")
        interface = civ5client.Interface(address, access_token)
        print("Saving interface credentials to config")
        interface.save_config()
    try:
        response = account.request_credentials(interface)
        json = response.json()
        if opts['init']:
            print("Logged in as", json['username'],
                  "with email", json['email'])
    except requests.exceptions.ConnectionError:
        raise
    except Exception as e:
        print(("Error: Failed to retrieve credentials. Either server "
               "is broken or configuration is wrong. Check server_address "
               "and access_token in config.ini, or remove it to configure "
               "again."))
    #
    # Confirm we have a save directory path in config
    #
    try:
        saves.get_config_save_path()
    except InvalidConfigurationError:
        print("No save directory path in config; attempting to find it")
        try:
            path = saves.get_default_save_path()
            print("Assuming", path)
            if not yes_no_question("Can you confirm the above directory is ok?"):
                path = input("Write the correct directory path: ")
        except saves.UnknownOperatingSystemError:
            path = input(("Unknown operating system. Please write the absolute"
                          " Civilizations 5 hotseat save directory path: "))
        print("Saving save directory path to config")
        saves.save_save_path_config(path)
    # If no delete_saves option found, create it and make it True
    if not config.has_option('Saves', 'delete_saves'):
        config['Saves']['delete_saves'] = 'True'
        config.write(open(config_file_name, 'w'))
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
            json = response.json()
        except ValueError:
            print("Error: Wrong map size. Check -h for possible")
            exit()
        else:
            print("Game started successfully with id", 
                  json['id'])

    if opts['list']:
        json, response = games.list_games(interface)
        for j in json:
            string = '{:3}) ID: {}\tName: {:12}\tHost: {:12}'.format(
                j['ref_number'], j['id'], j['name'], j['host'])
            game = games.Game(interface, j)
            if game.to_move():
                string += " <- Your move"
            print(string)

    if opts['list-civs']:
        response = games.get_civilizations(interface)
        json = response.json()
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
        response = games.get_civilizations(interface)
        json = response.json()
        short = not opts['--verbose']
        pretty_print_game(game.json, json, short=short)

    if opts['join']:
        try:
            response = game.join()
            civ_json = games.get_civilizations(interface).json()
            json = response.json()
            pretty_print_game(json, civ_json)
        except ServerError:
            print("Error: Failed to join game. Presumably you are already in it")
            raise

    if opts['leave']:
        game.leave()

    if opts['kick']:
        player.kick()

    if opts['start']:
        game.start()
        print("Game started. Please perform the first turn, save the game as",
              game.name, "and upload it with the upload command")

    if opts['disable-validation']:
        game.disable_validation()

    if opts['change-player-type']:
        try:
            player.change_type(opts['<player-type>'])
        except ValueError:
            print("Error: Wrong player type")

    if opts['choose-civ']:
        if not opts['<player>']:
            player = games.Player.from_id(game, game.find_own_player_id())
        try:
            player.choose_civilization(opts['<civilization>'])
        except ValueError:
            print("Error: Wrong civilization. list-civs to list acceptable civs")

    if opts['download']:
        try:
            file_name, response = game.download(force=opts['--force'], bar=True)
            print("Downloaded",file_name)
            print(("Please complete your turn by loading it in hotseat mode, "
                   "performing a turn, saving it in the menu so that the next "
                   "player can continue and uploading it to the server."))
        except OSError:
            print("Error: File with wanted name already exists")
            raise
        except WrongMoveError:
            print("Error: Not your move to download")

    if opts['upload']:
        try:
            if not opts['--force'] and not saves.confirm_password(game):
                print("Warning: Password not set. You should download the save again and set it")
                if not yes_no_question(
                        ("Are you sure you want to continue and upload it "
                    "regardless?")):
                    exit()
            if game.is_validation_enabled() and not opts['--force']:
                valid = saves.validate_upload_file(game)
                if not valid:
                    print(("Error: Turn not taken/invalid turn. If it's a "
                           "client error, try --force"))
                print("Save valid. Proceeding to upload")
            file_name, response = game.upload(bar=True)
            if config['Saves']['delete_saves'].lower() == 'true':
                print("Uploaded and removed", file_name, "without errors")
            else:
                print("Uploaded", file_name, "without errors")
        except MissingSaveFileError as e:
            print("Error: Save file", e.args[0], "not found. Please rename",
                  "the file if it exists under a different name")
            raise
        except WrongMoveError:
            print("Error: Not your move to upload")

except requests.exceptions.ConnectionError:
    print("Error: Failed to connect to server")
    traceback.print_exc(file=open(log_name,'a'))
except InvalidReferenceNumberError:
    print("Error: No game or player with such reference number")
except InvalidIdError:
    print("Error: No game or player with such an id")
except ServerError as e:
    print("Server error:", e.args[0])
    print("For contents of the response, please enable response logging in the"
          " config and try again.")
    traceback.print_exc(file=open(log_name,'a'))
except:
    traceback.print_exc(file=open(log_name,'a'))
    raise
