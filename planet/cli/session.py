"""CLI HTTP/auth sessions."""

from planet.auth import AuthType
from planet.http import Session


class CliSession(Session):

    def __init__(self, auth: AuthType = None):
        super().__init__(auth)
        self._client.headers.update({'X-Planet-App': 'python-cli'})
