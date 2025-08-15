"""CLI HTTP/auth sessions."""

from planet.http import Session
from planet.cli.auth import init_cli_auth_ctx_jit

class CliSession(Session):
    """Session with CLI-specific auth and identifying header"""

    def __init__(self, click_ctx=None, plsdk_auth=None):
        if plsdk_auth:
            _plsdk_auth = plsdk_auth
        else:
            if click_ctx:
                init_cli_auth_ctx_jit(click_ctx)
                _pksdk_auth = click_ctx.obj['PLSDK_AUTH']
            else:
                _plsdk_auth = None

        super().__init__(_plsdk_auth)
        self._client.headers.update({'X-Planet-App': 'python-cli'})
