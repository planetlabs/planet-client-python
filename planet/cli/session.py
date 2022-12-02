"""CLI HTTP/auth sessions."""

from planet.auth import AuthType
from planet.http import Session
from typing import Optional


class CliSession(Session):

    def __init__(self, auth: Optional[AuthType] = None):
        super().__init__(auth)
        self._client.headers.update({'X-Planet-App': 'python-cli'})
