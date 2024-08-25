"""CLI HTTP/auth sessions."""

from planet.auth import Auth
from planet.http import Session


class CliSession(Session):
    """Session with CLI-specific auth and identifying header"""

    def __init__(self, ctx):
        super().__init__(ctx.obj['PLSDK_AUTH'])
        self._client.headers.update({'X-Planet-App': 'python-cli'})
