import pathlib
import cryptography.hazmat.primitives.serialization as crypto_serialization
from requests.auth import AuthBase
from typing import Tuple, Optional

from planet.auth.auth_client import AuthClientException, \
    AuthClientConfigException
from planet.auth.oidc.api_clients.oidc_request_auth import \
    prepare_client_secret_request_auth, \
    prepare_private_key_assertion_auth_payload
from planet.auth.oidc.auth_client import OidcAuthClientConfig, OidcAuthClient
from planet.auth.oidc.oidc_credential import FileBackedOidcCredential
from planet.auth.oidc.request_authenticator import \
    RefreshOrReloginOidcTokenRequestAuthenticator


class ClientCredentialsClientSecretClientConfig(OidcAuthClientConfig):

    def __init__(self, client_secret, **kwargs):
        super().__init__(**kwargs)
        self.client_secret = client_secret


class ClientCredentialsClientSecretAuthClient(OidcAuthClient):

    def __init__(self,
                 client_config: ClientCredentialsClientSecretClientConfig):
        super().__init__(client_config)
        self._ccauth_client_config = client_config

    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        return raw_payload, prepare_client_secret_request_auth(
            self._ccauth_client_config.client_id,
            self._ccauth_client_config.client_secret)

    def login(self, requested_scopes=None, allow_open_browser=False, **kwargs):
        if not requested_scopes:
            requested_scopes = \
                self._ccauth_client_config.default_request_scopes

        return FileBackedOidcCredential(
            self._token_client().get_token_from_client_credentials_secret(
                self._ccauth_client_config.client_id,
                self._ccauth_client_config.client_secret,
                requested_scopes))

    def default_request_authenticator(
        self, credential_file_path: pathlib.Path
    ) -> RefreshOrReloginOidcTokenRequestAuthenticator:
        return RefreshOrReloginOidcTokenRequestAuthenticator(
            credential_file=FileBackedOidcCredential(
                credential_file=credential_file_path),
            auth_client=self)


class ClientCredentialsPubKeyClientConfig(OidcAuthClientConfig):

    def __init__(self,
                 client_privkey=None,
                 client_privkey_file=None,
                 client_privkey_password=None,
                 **kwargs):
        super().__init__(**kwargs)
        self._private_key_data = None
        self.client_privkey_file = client_privkey_file

        if client_privkey and type(client_privkey) is str:
            self.client_privkey = client_privkey.encode()
        else:
            self.client_privkey = client_privkey

        if client_privkey_password and type(client_privkey_password) is str:
            self.client_privkey_password = client_privkey_password.encode()
        else:
            self.client_privkey_password = client_privkey_password

    # Recast is to catches bad passwords. Too broad? # noqa
    @AuthClientConfigException.recast(TypeError, ValueError)
    def _load_private_key(self):
        # TODO: also handle loading of JWK keys? Fork based on filename
        #       or detect?
        # import jwt
        # priv_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_dict))

        if self.client_privkey:
            priv_key = crypto_serialization.load_pem_private_key(
                self.client_privkey, password=self.client_privkey_password)
            if not priv_key:
                raise AuthClientConfigException(
                    'Unable to load private key literal from configuration')
        else:
            if not self.client_privkey_file:
                raise AuthClientConfigException(
                    'Private key must be configured for public key auth'
                    ' client credentials flow.')
            with open(self.client_privkey_file, "rb") as key_file:
                priv_key = crypto_serialization.load_pem_private_key(
                    key_file.read(), password=self.client_privkey_password)
                if not priv_key:
                    raise AuthClientConfigException(
                        'Unable to load private key from file "{}"'.format(
                            self.client_privkey_file))
        self._private_key_data = priv_key

    def private_key_data(self):
        # TODO: handle key refresh if the file has changed?
        if not self._private_key_data:
            self._load_private_key()
        return self._private_key_data


class ClientCredentialsPubKeyAuthClient(OidcAuthClient):

    def __init__(self, client_config: ClientCredentialsPubKeyClientConfig):
        super().__init__(client_config)
        self._pubkey_client_config = client_config

    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        auth_assertion_payload = prepare_private_key_assertion_auth_payload(
            audience=audience,
            client_id=self._pubkey_client_config.client_id,
            private_key=self._pubkey_client_config.private_key_data(),
            ttl=300)
        enriched_payload = {**raw_payload, **auth_assertion_payload}
        return enriched_payload, None

    def login(self, requested_scopes=None, allow_open_browser=False, **kwargs):
        if not requested_scopes:
            requested_scopes = \
                self._pubkey_client_config.default_request_scopes

        return FileBackedOidcCredential(
            # FIXME: change get_token_from_client_credentials_pubkey to
            #        use enrichment.
            self._token_client().get_token_from_client_credentials_pubkey(
                self._pubkey_client_config.client_id,
                self._pubkey_client_config.private_key_data(),
                requested_scopes))

    def default_request_authenticator(
        self, credential_file_path: pathlib.Path
    ) -> RefreshOrReloginOidcTokenRequestAuthenticator:
        return RefreshOrReloginOidcTokenRequestAuthenticator(
            credential_file=FileBackedOidcCredential(
                credential_file=credential_file_path),
            auth_client=self)


# TODO: No implementation yet.
class ClientCredentialsSharedKeyClientConfig(OidcAuthClientConfig):

    def __init__(self, shared_key, **kwargs):
        super().__init__(**kwargs)
        self.shared_key = shared_key


class ClientCredentialsSharedKeyAuthClient(OidcAuthClient):

    def __init__(self, client_config: ClientCredentialsSharedKeyClientConfig):
        super().__init__(client_config)
        self._sharedkey_client_config = client_config

    def _client_auth_enricher(
            self, raw_payload: dict,
            audience: str) -> Tuple[dict, Optional[AuthBase]]:
        raise AuthClientException('No implementation')
        # when we have an implementation, see
        # prepare_shared_key_assertion_auth_payload in oidc_request_auth

    def login(self, requested_scopes=None, allow_open_browser=False, **kwargs):
        raise AuthClientException('No implementation')

    def default_request_authenticator(
        self, credential_file_path: pathlib.Path
    ) -> RefreshOrReloginOidcTokenRequestAuthenticator:
        return RefreshOrReloginOidcTokenRequestAuthenticator(
            credential_file=FileBackedOidcCredential(
                credential_file=credential_file_path),
            auth_client=self)
