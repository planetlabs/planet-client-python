import time

import jwt
from jwt import PyJWTError

from planet.auth.auth_client import AuthClientException
from planet.auth.oidc.api_clients.jwks_api_client import JwksAPIClient


class TokenValidator():
    # Keys really don't change often... Maybe quarterly. In all but emergency
    # situations a new key would be published long before the old one is
    # removed from circulation.  We throttle key fetches so we don't
    # degenerate into DOS'ing the JWKS endpoint if presented with requests
    # using tokens with invalid keys
    min_jwks_fetch_interval = 300

    def __init__(self, jwks_client: JwksAPIClient):
        self._jwks_client = jwks_client
        self._keys_by_id = {}
        self._load_time = 0

    def _update(self):
        # TODO: bootstrap from cached values? the concern is large
        #   worker pools on disposable nodes generating load on churn.
        #   Only an issue if such nodes are performing token validation.
        jwks_keys = self._jwks_client.jwks_keys()
        new_keys_by_id = {}
        for json_key in jwks_keys:
            # new_keys_by_id[json_key['kid']] = json_key
            new_keys_by_id[json_key['kid']] = jwt.PyJWK(jwk_data=json_key)

        self._keys_by_id = new_keys_by_id
        self._load_time = int(time.time())

    def get_signing_key_by_id(self, key_id):
        key = self._keys_by_id.get(key_id)
        if (not key) and ((self._load_time + self.min_jwks_fetch_interval) <
                          int(time.time())):
            self._update()
            key = self._keys_by_id.get(key_id)
        if not key:
            raise AuthClientException(
                "Could not find signing key for key ID {}".format(key_id))

        return key

    @staticmethod
    def _get_trusted_algorithm(unverified_header):
        algorithm = unverified_header.get('alg')
        # Don't trust straight pass-through, since "none" is a valid
        # algorithm. Only trust specific algorithms.
        if not (algorithm and (algorithm.lower() == "rs256"
                               or algorithm.lower() == "rs512")):
            raise AuthClientException(
                "Unknown or unsupported token algorithm {}".format(algorithm))
        return algorithm

    @AuthClientException.recast(PyJWTError)
    def validate_token(self,
                       token_str,
                       issuer,
                       audience,
                       required_claims=None,
                       nonce=None):
        unverified_header = jwt.get_unverified_header(token_str)
        algorithm = self._get_trusted_algorithm(unverified_header)
        key_id = unverified_header.get('kid')
        signing_key = self.get_signing_key_by_id(key_id)
        validation_required_claims = ["aud", "exp", "iss"]
        if required_claims:
            validation_required_claims.extend(required_claims)
        if nonce:
            validation_required_claims.append("nonce")
        validated_claims = jwt.decode(  # Throws when invalid.
            token_str, signing_key.key, algorithms=[algorithm],
            issuer=issuer, audience=audience,
            options={"require": validation_required_claims,
                     "verify_aud": True,
                     "verify_exp": True,
                     "verify_iss": True,
                     "verify_signature": True}
        )
        if nonce:
            if nonce != validated_claims.get('nonce'):
                raise AuthClientException(
                    'Token nonce did not match expected value')
        return validated_claims

    def validate_id_token(self,
                          token_str,
                          issuer,
                          client_id,
                          required_claims=None,
                          nonce=None):
        """
        Validate a JWT this is a OIDC ID token. Steps over and
        above basic token validation are performed, as described in
        https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation
        """
        validated_claims = self.validate_token(token_str=token_str,
                                               issuer=issuer,
                                               audience=client_id,
                                               required_claims=required_claims,
                                               nonce=nonce)

        # If the aud contains multiple values, azp must be present.
        validated_azp = None
        if isinstance(validated_claims.get('aud'), list):
            validated_azp = validated_claims.get('azp')
            if not validated_azp:
                raise AuthClientException(
                    '"azp" claim mut be present when ID token contains'
                    ' multiple audiences.')

        # if the azp claim is present, it must equal the client ID.
        if validated_azp:
            if validated_azp != client_id:
                raise AuthClientException(
                    'ID token "azp" claim expected to match the client'
                    ' ID "{}", but was "{}"'.format(client_id, validated_azp))

        return validated_claims
