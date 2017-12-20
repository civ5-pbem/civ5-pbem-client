#!/usr/bin/env python3
from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse, urljoin
import requests

config = ConfigParser()
config.read('config.ini')

interface_section = 'Interface Settings'
changed_config = False

if not config.has_section(interface_section):
    config.add_section(interface_section)

if config.has_option(interface_section, 'server_address'):
    server_address = config[interface_section]['server_address']
else:
    print("No server in config.ini")
    server_address = input("Write the server address: ")
    config[interface_section]['server_address'] = server_address
    changed_config = True

p = urlparse(server_address)
netloc = p.netloc or p.path
server_address = urlunparse(
    ('http',netloc,"","","",""))

if config.has_option(interface_section, 'email'):
    email = config[interface_section]['email']
else:
    email = input("Write the email address for civ5-pbem: ")
    config[interface_section]['email'] = email
    changed_config = True
    
if config.has_option(interface_section, 'username'):
    username = config[interface_section]['username']
else:
    username = input("Choose a username: ")
    config[interface_section]['username'] = email
    changed_config = True

if config.has_option(interface_section, 'access_token'):
    access_token = config[interface_section]['access_token']
else:
    print("No access token in config")
    register_inp = input("Register new account for "+email+"? [y/n]: ")
    if len(register_inp) > 0 and register_inp[0] == 'y':
        try:
            register_request = requests.post(
                urljoin(server_address,"/user-accounts/register"),
                json={'email':email, 'username':username})
            if register_request.status_code == 200:
                print("Account registration request sent. Check email for token")
            else:
                print("Account taken")
        except requests.exceptions.ConnectionError:
            print("Failed to connect to server")
            exit()
    access_token = input("Write the access token from your email: ")
    config[interface_section]['access_token'] = access_token
    changed_config = True

try:
    account_request = requests.get(
        urljoin(server_address,"/user-accounts/current"), headers={"Access-Token":access_token})
    if account_request.json()['email'] == email:
        print("Credentials are correct")
    else:
        print("Credentials are incorrect. Check config.ini for discrepancies")
        exit()
except requests.exceptions.ConnectionError:
    print("Failed to connect to server")
    exit()

if changed_config:
    print("Saving changes to 'config.ini'")
    with open("config.ini", "w") as configfile:
        config.write(configfile)
