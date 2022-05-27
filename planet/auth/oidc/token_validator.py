import time

import jwt
from jwt import PyJWTError

from planet.auth.auth_exception import AuthException
from planet.auth.oidc.api_clients.jwks_api_client import JwksApiClient


class TokenValidatorException(AuthException):

    def __init__(self, message=None, inner_exception=None):
        super().__init__(message, inner_exception)


class TokenValidator:

    # Keys really don't change often... Maybe quarterly. In all but
    # emergency situations a new key would be published long before the
    # old one is removed from circulation.  We throttle key fetches so we
    # don't degenerate into DOS'ing the JWKS endpoint if presented with
    # requests using tokens with invalid keys.  So, the default fetch
    # interval can be wide.
    # TODO: implement a max interval - need to push out removed keys.
    #       Add some fuzz, so we don't set up refresh storms?
    def __init__(self,
                 jwks_client: JwksApiClient,
                 min_jwks_fetch_interval=300):
        self._jwks_client = jwks_client
        self._keys_by_id = {}
        self._load_time = 0
        self.min_jwks_fetch_interval = min_jwks_fetch_interval

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
            raise TokenValidatorException(
                "Could not find signing key for key ID {}".format(key_id))

        return key

    @staticmethod
    def _get_trusted_algorithm(unverified_header):
        algorithm = unverified_header.get('alg')
        # Don't trust straight pass-through, since "none" is a valid
        # algorithm. Only trust specific algorithms.
        # TODO: or algorithm.lower() == "rs384"
        # TODO: or algorithm.lower() == "rs512"
        if not (algorithm and (algorithm.lower() == "rs256")):
            raise TokenValidatorException(
                "Unknown or unsupported token algorithm {}".format(algorithm))
        return algorithm

    # Note: "validate_token" DOES NOT force nonce validation. It's just
    #  JWT validation. Nonces are an application layer above. (See ID token
    #  validation below, which is OIDC ID token specific.
    # TODO: verify and document behaviors when multiple expected audiences
    #  are passed.
    @TokenValidatorException.recast(PyJWTError)
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
                raise TokenValidatorException(
                    'Token nonce did not match expected value')
        return validated_claims

    # TODO: should we error if the token has a nonce, and none was given to
    #       verify?
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
                raise TokenValidatorException(
                    '"azp" claim mut be present when ID token contains'
                    ' multiple audiences.')

        # if the azp claim is present, it must equal the client ID.
        if validated_azp:
            if validated_azp != client_id:
                raise TokenValidatorException(
                    'ID token "azp" claim expected to match the client'
                    ' ID "{}", but was "{}"'.format(client_id, validated_azp))

        return validated_claims
