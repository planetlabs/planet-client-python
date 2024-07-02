"""CLI HTTP/auth sessions."""

from planet.auth import Auth
from planet.http import Session


class CliSession(Session):
    """Session with CLI-specific auth and identifying header"""

    def __init__(self):
        token_auth = Auth.from_keyring() or Auth.from_file()
        super().__init__(token_auth)
        self._client.headers.update({'X-Planet-App': 'python-cli'})
