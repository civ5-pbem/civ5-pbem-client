#!/usr/bin/env python3
from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse, urljoin
import requests

import civ5client
from civ5client import account

config_file = 'config.ini'

def yes_no_question(question):
    answer = input(question+" [y/n]: ")
    if len(answer) > 0 and answer[0] in ['y','Y']:
        return True
    else:
        return False

#
# Registration and credentials
#

try:
    interface = civ5client.Interface.from_config(config_file)
except civ5client.InvalidConfigurationError:
    print("Invalid or missing config; creating new one")
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
    print("Saving config")
    interface.save_config(config_file)
try:
    credentials = interface.request_credentials()
    print("Signed in as", credentials.get('email'))
except:
    print("Error: Failed to retrieve credentials")
    exit()
