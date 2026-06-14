import os
import urllib.parse
import requests

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")

def get_auth0_login_url(redirect_uri: str):
    params = {
        "response_type": "token",
        "client_id": AUTH0_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "audience": AUTH0_API_AUDIENCE,
        "scope": "openid profile email"
    }
    return f"https://{AUTH0_DOMAIN}/authorize?" + urllib.parse.urlencode(params)

