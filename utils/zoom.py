import os
import time
from urllib.parse import urljoin
from functools import wraps

import requests


class ZoomClientError(Exception):
    """Base exception for Zoom client errors."""

    pass


class ZoomAPIError(ZoomClientError):
    """Exception for Zoom API errors."""

    def __init__(self, status_code, message):
        super().__init__(f"Error {status_code}: {message}")
        self.status_code = status_code
        self.message = message


def api_call(func):
    """Decorator to handle API call errors."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # pass through `params` to the API call, ensuring they are not `None`
        if 'params' in kwargs and kwargs['params'] is None:
            kwargs['params'] = {}

        response = func(*args, **kwargs)
        if not isinstance(response, requests.Response):
            raise ZoomClientError(
                f"Function `{func.__name__}` must return a `requests.Response` object."
            )
        if response.status_code != 200:
            try:
                error_message = response.json().get("message", "Unknown error")
            except ValueError:  # Response is not JSON
                error_message = response.text
            raise ZoomAPIError(response.status_code, error_message)
        try:
            return response.json()
        except ValueError:
            raise ZoomClientError("Response is not JSON formatted.")

    return wrapper


class ZoomClient:
    BASE_URL = "https://api.zoom.us/v2/"
    AUTH_URL = "https://zoom.us/oauth/"

    def __init__(self, account_id, client_id, client_secret) -> None:
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None
        self._token_expiry = None  # Track token expiration time

    def _is_token_expired(self):
        """Check if the current token has expired."""
        return self._token_expiry and time.time() >= self._token_expiry

    def _refresh_token(self):
        """Refresh the access token if expired."""
        data = {
            "grant_type": "account_credentials",
            "account_id": self.account_id,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(urljoin(self.AUTH_URL, "token"), data=data)
        response.raise_for_status()  # Ensure we handle request failures
        token_data = response.json()
        self._access_token = token_data["access_token"]
        # Set the token expiry time (current time + expires_in)
        self._token_expiry = time.time() + token_data["expires_in"]

    @property
    def access_token(self):
        """Return a valid access token, refreshing if expired."""
        if self._access_token is None or self._is_token_expired():
            self._refresh_token()  # Refresh the token
        return self._access_token

    @property
    def auth_header(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    @api_call
    def get_recordings(self, params=None):
        url = urljoin(self.BASE_URL, "users/me/recordings")
        return requests.get(url, headers=self.auth_header, params=params)

    @api_call
    def get_meeting_recordings(self, meeting_uuid, params=None):
        url = urljoin(self.BASE_URL, f"meetings/{meeting_uuid}/recordings")
        return requests.get(url, headers=self.auth_header, params=params)

    def download_participant_audio_files(self, meeting_uuid, path='tmp'):
        # keep track of number of occurrences so don't have same filename if a name is repeated
        names = {}
        os.makedirs(path, exist_ok=True)
        response = self.get_meeting_recordings(meeting_uuid)
        for data in response['participant_audio_files']:
            name = data['file_name'].split('-')[-1].strip()
            if name in names:
                names[name] += 1
            else:
                names[name] = 1
            filename = name + (f"_{names[name]}" if names[name] > 1 else '')
            
            url = data['download_url']
            r = requests.get(url, headers=self.auth_header)
            with open(f'{path}/{filename}.m4a', 'wb') as f:
                f.write(r.content)
