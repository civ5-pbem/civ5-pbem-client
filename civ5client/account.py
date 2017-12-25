"""
This module contians account related actions, such as registration.
"""

from urllib.parse import urlparse, urlunparse, urljoin
import requests

class AccountTakenError(Exception):
    """Raised when attempting to register a taken account."""

def register_account(server_address, username, email):
    """Sends a registration request with a given email and username."""
    register_request = requests.post(
        urljoin(server_address,"/user-accounts/register"),
        json={'email':email, 'username':username})
    if register_request.status_code != 200:
        # TODO: A non-200 code could mean a lot of things
        raise AccountTakenError

def request_credentials(interface):
    """Requests credentials given by a specific Interface, i.e.
    related to a specific access token on a server.
    """
    request = interface.get_request("/user-accounts/current")
    return request.json()
