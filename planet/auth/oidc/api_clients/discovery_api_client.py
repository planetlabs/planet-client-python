from planet.auth.oidc.api_clients.api_client import OidcApiClient

# class DiscoveryApiException(OidcApiClientException):
#
#    def __init__(self, message=None, raw_response=None):
#        super().__init__(message, raw_response)


class DiscoveryApiClient(OidcApiClient):

    # TODO: Revisit of this is where I should cache. I did work
    #       on the JWKS client after this, and I think it is more mature.
    def __init__(self, discovery_uri=None, auth_server=None):
        if discovery_uri:
            d_uri = discovery_uri
        else:
            if auth_server.endswith('/'):
                d_uri = auth_server + '.well-known/openid-configuration'
            else:
                d_uri = auth_server + '/.well-known/openid-configuration'
        super().__init__(d_uri)
        self._oidc_discovery = None

    def do_discovery(self):
        self._oidc_discovery = self._checked_get_json_response(None, None)

    def do_discovery_jit(self):
        if not self._oidc_discovery:
            self.do_discovery()

    def discovery(self):
        self.do_discovery_jit()
        return self._oidc_discovery
