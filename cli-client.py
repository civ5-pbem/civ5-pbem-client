#!/usr/bin/env python3
"""
This script allows to make full use of the civ5client package
through the command line. It is (TODO: not yet) able to:
    register an account
    list existing games
    start a new game
    respond to invites
    download/upload a save to the server to perform a turn
"""

from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse, urljoin
import requests

import civ5client
from civ5client import account, saves, InvalidConfigurationError



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
        print("Configured as", credentials.get('email'))
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
except requests.exceptions.ConnectionError:
    print("Error: Failed to connect to server")
    exit()
