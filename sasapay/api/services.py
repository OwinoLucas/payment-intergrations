import requests
import json
from requests.auth import HTTPBasicAuth
from django.conf import settings


def get_sasapay_token():
    
    url = "https://sandbox.sasapay.app/api/v1/auth/token/"
    params = {"grant_type": "client_credentials"}

    # Perform authenticated request
    response = requests.get(
        url,
        auth=HTTPBasicAuth(settings.CLIENT_ID, settings.CLIENT_SECRET),
        params=params
    )

    if response.status_code != 200:
        return {
            "payload": params,
            "access_token": None,
            "expires_in": None,
            "error": f"Failed to get token (status {response.status_code})",
        }

    data = response.json()
    access_token = data.get("access_token")
    expires_in = data.get("expires_in")

    return {
        "payload": params,
        "access_token": access_token,
        "expires_in": expires_in,
    }
