"""
civ5client
==========
Package to interact with civ5-pbem-server by http requests.
"""

from configparser import ConfigParser
from urllib.parse import urlparse, urlunparse, urljoin
import requests

class InvalidConfigurationError(Exception):
    """Raised when configuration is insufficient."""

def parse_address(address):
    """Turns a possibly invalid address string into an acceptable url.""" 
    p = urlparse(address)
    netloc = p.netloc or p.path
    out_address = urlunparse(
        ('http',netloc,"","","",""))
    return out_address

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
    def from_config(cls, config_file_name):
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

    def save_config(self, config_file_name):
        """Saves the Interface information in a config file."""
        config = ConfigParser()
        config.read(config_file_name)
        if not config.has_section('Interface Settings'):
            config.add_section('Interface Settings')
        config['Interface Settings']['server_address'] = self.server_address
        config['Interface Settings']['access_token'] = self.access_token
        with open(config_file_name, 'w') as config_file:
            config.write(config_file)

    def get_request(self, path):
        ###TODO: headers? data? anything? No real activities to perform for now
        return requests.get(
            urljoin(self.server_address, path), 
            headers={"Access-Token":self.access_token})
    
    def post_request(self, path, json):
        return requests.post(
            urljoin(self.server_address, path),
            json=json,
            headers={"Access-Token":self.access_token})
    

