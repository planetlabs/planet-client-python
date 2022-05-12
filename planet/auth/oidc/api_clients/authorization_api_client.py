import getpass
import http.server
import importlib.resources as pkg_resources
import logging

from http import HTTPStatus
from urllib.parse import urlparse, parse_qs, urlencode
from webbrowser import open_new

import planet.auth.oidc.util as oidc_util
from planet.auth.oidc import resources
from planet.auth.oidc.api_clients.api_client import OidcApiClientException

logger = logging.getLogger(__name__)
DEFAULT_REDIRECT_LISTEN_PORT = 80
AUTH_TIMEOUT = 60


class AuthorizationApiException(OidcApiClientException):

    def __init__(self, message=None, raw_response=None):
        super().__init__(message, raw_response)


class _OidcPKCESigninCallbackHandler(http.server.BaseHTTPRequestHandler):
    """
    HTTP Server callbacks to handle OAuth redirects.
    This handler expects to be invoked as a callback after user
    authentication. When called after successful login, the request will
    contain an auth code that can be used to obtain tokens. Parsing of the
    results is not handled here. It is the caller's responsibility.  All the
    callback does is pass the request along.
    """

    def __init__(self, request, address, server, do_logging=False):
        self._do_logging = do_logging
        super().__init__(request, address, server)

    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.server.callback_raw_request_path = self.path
        self.wfile.write(
            bytes(pkg_resources.read_text(resources, 'planet_redirect.html'),
                  'utf-8'))

    def log_message(self, format, *args):
        # do nothing to disable logging.  We let the caller control this so
        # they can hush the HTTP server logging regardless of the global log
        # level.
        if self._do_logging:
            return super().log_message(format, *args)
        return


def _parse_authcode_from_callback(raw_request_path, expected_state):
    if not raw_request_path:
        raise AuthorizationApiException("Authorization callback was empty")

    logger.debug("Parsing callback request from authorization server" +
                 raw_request_path)

    parsed_query_string = parse_qs(urlparse(raw_request_path).query)

    error_code = parsed_query_string.get('error')
    if error_code:
        # TODO: Can we unify this error parsing with that in the
        #       oidc api_client baseclass?
        error_description = parsed_query_string.get('error_description') or [
            'no error description'
        ]
        raise AuthorizationApiException(
            'Authorization error: {}: {}'.format(error_code[0],
                                                 error_description[0]),
            raw_request_path)

    state_array = parsed_query_string.get('state')
    state = None

    if state_array:
        state = state_array[0]
    if state != expected_state:
        raise AuthorizationApiException(
            'Callback state did not match expected value. Expected: {},'
            ' Received: {}'.format(expected_state, state),
            raw_request_path)

    auth_code_array = parsed_query_string.get('code')
    auth_code = None
    if auth_code_array:
        auth_code = auth_code_array[0]
    if not auth_code:
        raise AuthorizationApiException(
            'Failed to understand authorization callback. Callback request'
            ' did not include an authorization code or a recognized error.'
            ' Raw callback request: ' + raw_request_path,
            raw_request_path)

    return auth_code


# Not a child class of OidcApiClient since we do not directly call the
# authorization API. Rather, interaction with the authorization server is via
# a browser to accommodate user interaction flows.
class AuthorizationApiClient():

    def __init__(self, authorization_uri=None):
        self._authorization_uri = authorization_uri

    @staticmethod
    def _prep_pkce_auth_payload(client_id,
                                redirect_uri,
                                requested_scopes,
                                pkce_code_challenge):
        data = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'state': oidc_util.generate_nonce(8),
            'nonce': oidc_util.generate_nonce(32),
            'code_challenge': pkce_code_challenge,
            'code_challenge_method': 'S256'
        }
        if requested_scopes:
            data['scope'] = ' '.join(requested_scopes)

        return data

    def authcode_from_pkce_flow_with_browser_with_callback_listener(
            self, client_id, redirect_uri, requested_scopes,
            pkce_code_challenge):
        data = self._prep_pkce_auth_payload(client_id,
                                            redirect_uri,
                                            requested_scopes,
                                            pkce_code_challenge)
        auth_request_uri = self._authorization_uri + '?' + urlencode(data)

        # HTTP server to catch the callback redirect from the browser
        # auth process
        logger.debug(
            'Setting up listener for auth callback handler with URI "{}"'.
            format(redirect_uri))
        parsed_redirect_url = urlparse(redirect_uri)
        listen_port = parsed_redirect_url.port if parsed_redirect_url.port else DEFAULT_REDIRECT_LISTEN_PORT  # noqa
        if parsed_redirect_url.hostname.lower(
        ) != 'localhost' and parsed_redirect_url.hostname != '127.0.0.1':
            raise AuthorizationApiException(
                'Unexpected hostname in auth redirect URI. Expected'
                ' localhost URI, but received "{}"'.format(redirect_uri))

        # Only bind to loopback! See
        # https://datatracker.ietf.org/doc/html/rfc8252#section-8.3
        http_server = http.server.HTTPServer(
            ('localhost', listen_port),
            lambda request,
            address,
            server: _OidcPKCESigninCallbackHandler(
                request,
                address,
                server,
                do_logging=(logger.root.level <= logging.DEBUG)))
        http_server.timeout = AUTH_TIMEOUT

        # Don't kick off the browser until we are satisfied that the callback
        # handler is up and listening. UX team wanted this on the console
        print('Opening browser for authorization and listening locally for'
              ' callback.\nIf this fails, retry with "no browser"'
              ' option enabled.\n')
        logger.debug('Opening browser with authorization URL : "{}"\n'.format(
            auth_request_uri))
        open_new(auth_request_uri)

        # Do we ever need to loop for multiple callbacks?
        # (No, this should never be needed.)
        http_server.handle_request()

        if hasattr(http_server, 'callback_raw_request_path'):
            return _parse_authcode_from_callback(
                http_server.callback_raw_request_path, data['state'])
        else:
            raise AuthorizationApiException(
                'Unknown error obtaining login tokens.'
                ' No callback data was received.')

    def authcode_from_pkce_flow_without_browser_without_callback_listener(
            self, client_id, redirect_uri, requested_scopes,
            pkce_code_challenge):
        # 1) Display URL for user to paste into browser.
        # 2) Wait for them to copy-paste the auth code URL.
        # X) The process of catching the redirect from the auth and parsing
        #    out the auth code is out of band of this code.
        data = self._prep_pkce_auth_payload(client_id,
                                            redirect_uri,
                                            requested_scopes,
                                            pkce_code_challenge)
        auth_request_uri = self._authorization_uri + '?' + urlencode(data)
        print("Please go to the following URL to proceed with login.\n"
              "After successful login, please provide the resulting"
              " authentication code.\n"
              "\n\t{}\n\n".format(auth_request_uri))
        return getpass.getpass(prompt='Authentication code: ')
