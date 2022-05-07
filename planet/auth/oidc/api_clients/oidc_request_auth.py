import jwt
import time
import uuid

from requests.auth import HTTPBasicAuth
"""
Some OIDC endpoints require client auth, and how auth is done can very
depending on how the OIDC provider is configured to handle the particular
client. See
https://developer.okta.com/docs/reference/api/oidc/#client-authentication-methods

This module provides some helper functions for wrangling the requests for
various OIDC client auth methods.  It is for the caller to decide the
appropriate use of these.
"""


def _prepare_oidc_client_jwt_payload(audience: str, client_id: str, ttl: int):
    # See
    # https://developer.okta.com/docs/reference/api/oidc/#token-claims-for-client-authentication-with-client-secret-or-private-key-jwt
    now = int(time.time())
    unsigned_jwt = {
        'iss': client_id,
        'sub': client_id,
        'aud': audience,
        'iat': now,
        'exp': now + ttl,
        'jti': str(uuid.uuid4())
    }
    return unsigned_jwt


def prepare_client_noauth_auth_payload(client_id: str):
    client_secret_auth_payload = {
        # FIXME: should just be part of the calls to methods that need it?
        'client_id': client_id,
    }
    return client_secret_auth_payload


def _prepare_oidc_assertion_auth_payload(signed_jwt):
    assertion_auth_payload = {
        'client_assertion_type':
        'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion': signed_jwt
    }
    return assertion_auth_payload


def prepare_client_secret_request_auth(client_id: str, client_secret: str):
    return HTTPBasicAuth(client_id, client_secret)


# This is not being used right now.
# def prepare_client_secret_auth_payload(client_id: str, client_secret: str):
#     client_secret_auth_payload = {
#         'client_id': client_id, 'client_secret': client_secret
#     }
#     return client_secret_auth_payload


def prepare_private_key_assertion_auth_payload(audience: str,
                                               client_id: str,
                                               private_key,
                                               ttl: int):
    unsigned_jwt = _prepare_oidc_client_jwt_payload(audience=audience,
                                                    client_id=client_id,
                                                    ttl=ttl)
    signed_jwt = jwt.encode(unsigned_jwt, private_key, algorithm="RS256")
    return _prepare_oidc_assertion_auth_payload(signed_jwt)


# Not used yet. See ClientCredentialsSharedKeyAuthClient.
# def prepare_shared_key_assertion_auth_payload(audience: str,
#                                               client_id: str,
#                                               shared_key,
#                                               ttl: int):
#     unsigned_jwt = _prepare_oidc_client_jwt_payload(audience=audience,
#                                                     client_id=client_id,
#                                                     ttl=ttl)
#     signed_jwt = jwt.encode(unsigned_jwt, shared_key, algorithm="HS256")
#     return _prepare_oidc_assertion_auth_payload(signed_jwt)
