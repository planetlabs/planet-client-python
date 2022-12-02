"""CLI HTTP/auth sessions."""

from planet.auth import Auth
from planet.http import Session


class CliSession(Session):
    """Session with CLI-specific auth and identifying header"""

    def __init__(self):
        super().__init__(Auth.from_file())
        self._client.headers.update({'X-Planet-App': 'python-cli'})
