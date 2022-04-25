from planet.auth.oidc.api_clients.api_client import OIDCAPIClient, OIDCAPIClientException


class DiscoveryAPIException(OIDCAPIClientException):
    def __init__(self, message=None, raw_response=None):
        super().__init__(message, raw_response)


class DiscoveryAPIClient(OIDCAPIClient):
    def __init__(self, discovery_uri=None, auth_server=None):
        super().__init__(discovery_uri if discovery_uri else auth_server + '/.well-known/openid-configuration')
        self._oidc_discovery = None

    def do_discovery(self):
        self._oidc_discovery = self._checked_get_json_response(None, None)

    def do_discovery_jit(self):
        if not self._oidc_discovery:
            self.do_discovery()

    def discovery(self):
        self.do_discovery_jit()
        return self._oidc_discovery