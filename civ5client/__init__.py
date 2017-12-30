"""
civ5client
==========
Package to interact with civ5-pbem-server by http requests.
"""
import time

from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse, urljoin
import requests

config_file_name = "config.ini"
log_file_name = "response_log.txt"

class InvalidConfigurationError(Exception):
    """Raised when configuration is insufficient."""

class ServerError(Exception):
    """Raised when something goes wrong on the server."""

def parse_address(address):
    """Turns a possibly invalid address string into an acceptable url.""" 
    p = urlparse(address)
    netloc = p.netloc or p.path
    out_address = urlunparse(
        ('http',netloc,"","","",""))
    return out_address

def log_response(log_file, response, stream=False):
    """Writes down the request sent and response received in a log file."""
    with open(log_file, 'a') as log:
        time_str = "Request at " + time.strftime("%Y-%m-%d %H:%M:%S")
        log.write(time_str)
        log.write('\n')
        request = response.request
        log.write("sent to " + str(request.url))
        log.write('\n')
        if not stream:
            log.write("received response: " + str(response.content))
        else:
            log.write("received a long stream response")
        log.write('\n\n')

class Interface():
    """
    Class describing a correct server url together with an access token
    to communicate with it. All client-server interactions aside from
    registration require it.
    """

    def __init__(self, server_address, access_token):
        self.server_address = server_address # must be complete url with http:
        self.access_token = access_token

    @classmethod
    def from_config(cls):
        """Creates an Interface based on a config file."""
        config = ConfigParser()
        config.read(config_file_name)
        if (config.has_section('Interface Settings')
                and config.has_option('Interface Settings', 'server_address')
                and config.has_option('Interface Settings', 'access_token')):
            server_address = config['Interface Settings']['server_address']
            access_token = config['Interface Settings']['access_token']
            return cls(server_address, access_token) 
        else:
            raise InvalidConfigurationError

    def save_config(self):
        """Saves the Interface information in a config file."""
        config = ConfigParser()
        config.read(config_file_name)
        if not config.has_section('Interface Settings'):
            config.add_section('Interface Settings')
        config['Interface Settings']['server_address'] = self.server_address
        config['Interface Settings']['access_token'] = self.access_token
        with open(config_file_name, 'w') as config_file:
            config.write(config_file)

    def get_request(self, path, stream=False, log=True):
        ###TODO: headers? data? anything? No real activities to perform for now
        response = requests.get(
            urljoin(self.server_address, path), 
            headers={"Access-Token":self.access_token},
            stream=stream)
        if log:
            log_response(log_file_name, response, stream=stream)
        if response.status_code != 200:
            message = response.status_code
            json = response.json()
            if 'message' in json:
                message = json['message']
            raise ServerError( message, response.content)
        return response
    
    def post_request(self, path, json=None, files=None, log=True):
        response = requests.post(
            urljoin(self.server_address, path),
            json=json,
            files=files,
            headers={"Access-Token":self.access_token})
        if log:
            log_response(log_file_name, response)
        if response.status_code != 200:
            message = response.status_code
            json = response.json()
            if 'message' in json:
                message = json['message']
            raise ServerError(message, response.content)
        return response
