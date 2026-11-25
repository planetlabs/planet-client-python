"""CLI HTTP/auth sessions."""

from planet.http import Session


class CliSession(Session):
    """Session with CLI-specific auth and identifying header"""

    def __init__(self, click_ctx=None, plsdk_auth=None):
        _plsdk_auth = None
        _max_retries = None
        _max_retry_backoff = None
        _max_retry_jitter = None

        if click_ctx:
            _plsdk_auth = click_ctx.obj['PLSDK_AUTH']
            _max_retries = click_ctx.obj.get('MAX_RETRIES')
            _max_retry_backoff = click_ctx.obj.get('MAX_RETRY_BACKOFF')
            _max_retry_jitter = click_ctx.obj.get('MAX_RETRY_JITTER')

        if plsdk_auth:
            _plsdk_auth = plsdk_auth

        super().__init__(_plsdk_auth,
                         max_retries=_max_retries,
                         max_retry_backoff=_max_retry_backoff,
                         max_retry_jitter=_max_retry_jitter)
        self._client.headers.update({'X-Planet-App': 'python-cli'})
