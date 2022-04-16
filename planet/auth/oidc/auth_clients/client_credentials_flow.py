from requests.auth import AuthBase
from typing import Tuple, Optional

from cryptography.hazmat.primitives import serialization

from planet.auth.auth_client import AuthClientException
from planet.auth.oidc.api_clients.oidc_request_auth import prepare_client_secret_request_auth, \
    prepare_private_key_assertion_auth_payload
from planet.auth.oidc.auth_client import OidcAuthClientConfig, OidcAuthClient
from planet.auth.oidc.oidc_token import FileBackedOidcToken


class ClientCredentialsClientSecretClientConfig(OidcAuthClientConfig):
    def __init__(self, client_secret, **kwargs):
        super().__init__(**kwargs)
        self.client_secret = client_secret


class ClientCredentialsClientSecretAuthClient(OidcAuthClient):
    def __init__(self, client_config: ClientCredentialsClientSecretClientConfig):
        super().__init__(client_config)
        self._ccauth_client_config = client_config

    def _client_auth_enricher(self, raw_payload: dict, audience: str) -> Tuple[dict, Optional[AuthBase]]:
        # FIXME: how to decide when to use client_secret basic auth vs client secret post?
        # FIXME: test, is putting the client id in the auth header and the payload overconstrained?
        #        Is that the job of this class, or the helper to fix?
        #        So ugly we are getting into the business of the api clients.
        # FIXME: should removing a redundant client_id be the job of the helper?
        # FIXME: clean up the calling conventions of the helper functions to match their actual use.
        return raw_payload, prepare_client_secret_request_auth(self._ccauth_client_config.client_id,
                                                               self._ccauth_client_config.client_secret)

    def login(self, requested_scopes=None, allow_open_browser=False):
        if not requested_scopes:
            requested_scopes = self._ccauth_client_config.default_request_scopes

        return FileBackedOidcToken(
            self._token_client().get_token_from_client_credentials_secret(
                self._ccauth_client_config.client_id,
                self._ccauth_client_config.client_secret,
                requested_scopes)
        )


class ClientCredentialsPubKeyClientConfig(OidcAuthClientConfig):
    def __init__(self,
                 client_privkey=None,
                 client_privkey_file=None,
                 client_privkey_password=None,
                 **kwargs):
        super().__init__(**kwargs)

        if client_privkey and type(client_privkey) is str:
            self.client_privkey = client_privkey.encode()
        else:
            self.client_privkey = client_privkey

        self.client_privkey_file = client_privkey_file
        self.client_privkey_password = client_privkey_password


class ClientCredentialsPubKeyAuthClient(OidcAuthClient):
    def __init__(self, client_config: ClientCredentialsPubKeyClientConfig):
        super().__init__(client_config)
        self._pubkey_client_config = client_config
        self._private_key_data = None

    def _load_private_key(self):
        # TODO: also handle loading of JWK keys? Fork based on filename or detect?
        # import jwt
        # priv_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_dict))

        if self._pubkey_client_config.client_privkey:
            priv_key = serialization.load_pem_private_key(
                self._pubkey_client_config.client_privkey,
                password=self._pubkey_client_config.client_privkey_password)
            if not priv_key:
                raise AuthClientException('Unable to load private key literal from configuration')
        else:
            if not self._pubkey_client_config.client_privkey_file:
                raise AuthClientException(
                    'Private key must be configured for public key auth client credentials flow.')
            with open(self._pubkey_client_config.client_privkey_file, "rb") as key_file:
                priv_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=self._pubkey_client_config.client_privkey_password)
                if not priv_key:
                    raise AuthClientException('Unable to load private key from file "{}"'.format(
                        self._pubkey_client_config.client_privkey_file))
        self._private_key_data = priv_key

    def _private_key(self):
        if not self._private_key_data:
            self._load_private_key()
        return self._private_key_data

    def _client_auth_enricher(self, raw_payload: dict, audience: str) -> Tuple[dict, Optional[AuthBase]]:
        # FIXME: test, is putting the client id in the auth header and the payload overconstrained?
        #        Is that the job of this class, or the helper to fix?
        #        So ugly we are getting into the business of the api clients.
        # FIXME: should removing a redundant client_id be the job of the helper?
        # FIXME: make the payload union part of the helper?
        auth_assertion_payload = prepare_private_key_assertion_auth_payload(
            audience=audience,
            client_id=self._pubkey_client_config.client_id,
            private_key=self._private_key(),
            ttl=300)
        # enriched_payload = raw_payload | auth_assertion_payload  # Python >= 3.9
        enriched_payload = {**raw_payload, **auth_assertion_payload}  # Python >= 3.5
        return enriched_payload, None

    def login(self, requested_scopes=None, allow_open_browser=False):
        if not requested_scopes:
            requested_scopes = self._pubkey_client_config.default_request_scopes

        return FileBackedOidcToken(
            # FIXME: change get_token_from_client_credentials_pubkey to use enrichment.
            self._token_client().get_token_from_client_credentials_pubkey(
                self._pubkey_client_config.client_id,
                self._private_key(),
                requested_scopes)
        )


# TODO: No implementation yet.
class ClientCredentialsSharedKeyClientConfig(OidcAuthClientConfig):
    def __init__(self, shared_key, **kwargs):
        super().__init__(**kwargs)
        self.shared_key = shared_key
        raise Exception('No implementation')


class ClientCredentialsSharedKeyAuthClient(OidcAuthClient):
    def __init__(self, client_config: ClientCredentialsSharedKeyClientConfig):
        super().__init__(client_config)
        self._sharedkey_client_config = client_config

    def _client_auth_enricher(self, raw_payload: dict, audience: str) -> Tuple[dict, Optional[AuthBase]]:
        raise Exception('No implementation')

    def login(self, requested_scopes=None, allow_open_browser=False):
        raise Exception('No implementation')
