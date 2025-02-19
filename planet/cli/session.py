"""CLI HTTP/auth sessions."""

from planet.http import Session


class CliSession(Session):
    """Session with CLI-specific auth and identifying header"""

    def __init__(self, click_ctx=None, plsdk_auth=None):
        if click_ctx:
            _plsdk_auth = click_ctx.obj['PLSDK_AUTH']
        else:
            _plsdk_auth = None

        if plsdk_auth:
            _plsdk_auth = plsdk_auth

        super().__init__(_plsdk_auth)
        self._client.headers.update({'X-Planet-App': 'python-cli'})
