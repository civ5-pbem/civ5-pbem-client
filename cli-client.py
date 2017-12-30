#!/usr/bin/env python3
"""
cli-client.py
=============
Script to make full use of the civ5client package to play Civilization 5 in 
a play-by-email fashion in connection with a dedicated civ5-pbem-server.

Usage:
    cli-client.py init [--verbose]
    cli-client.py new-game <game-name> <game-description> <map-size> [--verbose]
    cli-client.py (list | list-civs) [--verbose]
    cli-client.py (info | join | leave | start | disable-validation) <game> [--verbose]
    cli-client.py (download | upload) <game> [--force] [--verbose]
    cli-client.py kick <game> <player> [--verbose]
    cli-client.py choose-civ <game> [<player>] <civilization> [--verbose]
    cli-client.py change-player-type <game> <player> <player-type> [--verbose]
    cli-client.py (-h | --help)
    cli-client.py --version

    <game> can be either a game id or reference number (first given by list)
    <player> can be either a player id or the player number in a game

Commands:
    -h --help               Show this
    --version               Show version
    --verbose               Prints out the contents of the http response
    --force                 Forces an attempt to perform an action without
                            clientside validation

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
import sys
import time

from docopt import docopt
from configparser import ConfigParser
import requests

import civ5client
from civ5client import account, saves, games, InvalidConfigurationError, ServerError
from civ5client.games import InvalidReferenceNumberError, WrongMoveError
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
        response = account.request_credentials(interface)
        json = response.json()
        content = response.content
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
        if opts['--verbose']:
            print(e.__class__, ":", e.args[0])
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
            content = response.content
            json = response.json()
        except ValueError:
            print("Error: Wrong map size. Check -h for possible")
            exit()
        else:
            print("Game started successfully with id", 
                  json['id'])

    if opts['list']:
        response = games.list_games(interface)
        content = response.content
        json = response.json
        for j in json:
            string = '{:3}) ID: {}\tName: {:12}\tHost: {:12}'.format(
                j['ref_number'], j['id'], j['name'], j['host'])
            game = games.Game(interface, j)
            if game.to_move():
                string += " <- Your move"
            print(string)

    if opts['list-civs']:
        response = games.get_civilizations(interface)
        content = response.content
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
        content = response.content
        json = response.json()
        pretty_print_game(game.json, json)

    if opts['join']:
        try:
            response = game.join()
            civ_json = games.get_civilizations(interface).json()
            content = response.content
            json = response.json()
            pretty_print_game(json, civ_json)
        except ServerError:
            print("Error: Failed to join game. Presumably you are already in it")
            exit()

    if opts['leave']:
        content = game.leave().content

    if opts['kick']:
        content = player.kick().content

    if opts['start']:
        content = game.start().content
        print("Game started. Please perform the first turn, save the game as",
              game.name, "and upload it with the upload command")

    if opts['disable-validation']:
        content = game.disable_validation().content

    if opts['change-player-type']:
        try:
            content = player.change_type(opts['<player-type>']).content
        except ValueError:
            print("Error: Wrong player type")

    if opts['choose-civ']:
        if not opts['<player>']:
            player = games.Player.from_id(game, game.find_own_player_id())
        try:
            content = player.choose_civilization(opts['<civilization>']).content
        except ValueError:
            print("Error: Wrong civilization. list-civs to list acceptable civs")

    if opts['download']:
        try:
            file_name, response = game.download(force=opts['--force'])
            print("Downloaded",file_name)
            print(("Please complete your turn by loading it in hotseat mode, "
                   "performing a turn, saving it in the menu so that the next "
                   "player can continue and uploading it to the server."))
        except OSError:
            print("Error: File with wanted name already exists")
        except WrongMoveError:
            print("Error: Not your move to download")

    if opts['upload']:
        try:
            if not saves.confirm_password(game):
                print("Warning: Password not set. You should download the save again and set it")
                if not yes_no_question(
                        ("Are you sure you want to continue and upload it "
                    "regardless?")):
                    exit()
            if game.is_validation_enabled() and not opts['--force']:
                valid = saves.validate_upload_file(game)
                if not valid:
                    print("Error: Turn not taken/invalid turn")
            file_name, response = game.upload()
            print("Uploaded and removed", file_name, "without errors")
        except MissingSaveFileError as e:
            print("Error: Save file", e.args[0], "not found. Please rename",
                  "the file if it exists under a different name")
        except WrongMoveError:
            print("Error: Not your move to upload")

    if opts['--verbose']:
        try:
            print("Response content:\n", content)
        except NameError:
            print("No content to print")

    with open("response_log", 'a') as log:
        time_str = time.strftime("%Y-%m-%d %H:%M:%S") + " >>> "
        log.write(time_str)
        log.write(" ".join(arg for arg in sys.argv))
        log.write("\n")
        log.write(str(content))
        log.write("\n")

except requests.exceptions.ConnectionError:
    print("Error: Failed to connect to server")
except InvalidReferenceNumberError:
    print("Error: No game or player with such reference number")
except ServerError as e:
    if opts['--verbose']:
        print("Server error:", e.args[0], "\n", e.args[1])
    else:
        print("Server error:", e.args[0])
