import jwt
import time
import uuid
from tests.util import load_rsa_signing_key

TEST_DEFAULT_TTL = 60
TEST_MOCK_API_KEY = 'PLAK_MockApiKey'


class TestTokenBuilder:

    OIDC_ISSUER = 'unit_test_fake_issuer'
    # OIDC_ISSUER = 'https://blackhole.unittest.planet.com/oauth'
    OIDC_ACCESS_TOKEN_AUDIENCE = 'unit_test_access_audience'
    OIDC_ID_TOKEN_CLIENT_ID = ''

    def __init__(self,
                 signing_key_file,
                 signing_key_id=None,
                 signing_key_algorithm="RS256"):
        self.signing_key_file = signing_key_file
        self.signing_key = load_rsa_signing_key(signing_key_file)
        self.signing_key_id = signing_key_id
        self.signing_key_algorithm = signing_key_algorithm

    def construct_oidc_access_token(self,
                                    ttl=TEST_DEFAULT_TTL,
                                    extra_claims=None):
        # Build a fake JWT access token.  For test purposes, it doesn't matter
        # that it cannot be used anywhere.
        now = int(time.time())
        unsigned_jwt = {
            'iss': self.OIDC_ISSUER,
            'sub': 'unit_test_access_token_subject',
            'aud': self.OIDC_ACCESS_TOKEN_AUDIENCE,
            'iat': now,
            'exp': now + ttl,
            'jti': str(uuid.uuid4()),
            "scp": ["offline_access", "planet", "openid", "profile"],
        }
        if extra_claims:
            # Note: this is clobbering of the claims above!  might be fine
            # for this test class, but be warned if you copy-paste somewhere.
            unsigned_jwt.update(extra_claims)

        headers = {}
        if self.signing_key_id:
            headers['kid'] = self.signing_key_id

        signed_jwt = jwt.encode(unsigned_jwt,
                                self.signing_key,
                                algorithm=self.signing_key_algorithm,
                                headers=headers)
        return signed_jwt

    def construct_oidc_id_token(self,
                                client_id,
                                ttl=TEST_DEFAULT_TTL,
                                extra_claims=None):
        # Build a fake JWT ID token.  For test purposes, it doesn't matter
        # that it cannot be used anywhere.
        now = int(time.time())
        unsigned_jwt = {
            'iss': self.OIDC_ISSUER,
            'sub': client_id,
            'aud': client_id,
            'iat': now,
            'exp': now + ttl,
            'jti': str(uuid.uuid4())
        }
        if extra_claims:
            # Note: this is clobbering of the claims above!  might be fine
            # for this test class, but be warned if you copy-paste somewhere.
            unsigned_jwt.update(extra_claims)

        headers = {}
        if self.signing_key_id:
            headers['kid'] = self.signing_key_id

        signed_jwt = jwt.encode(unsigned_jwt,
                                self.signing_key,
                                algorithm=self.signing_key_algorithm,
                                headers=headers)
        return signed_jwt

    def generate_legacy_token(self,
                              api_key=TEST_MOCK_API_KEY,
                              ttl=TEST_DEFAULT_TTL):
        now = int(time.time())

        unsigned_jwt = {
            "program_id": 7,
            "token_type": "auth",
            "role_level": 9999,
            "organization_id": 99,
            "user_id": 999999,
            "plan_template_id": None,
            "membership_id": 123456,
            "organization_name": "Planet",
            "2fa": False,
            "exp": now + ttl,
            "user_name": "Test User",
            "email": "test.user@planet.com"
        }
        if api_key:
            unsigned_jwt['api_key'] = api_key

        signed_jwt = jwt.encode(unsigned_jwt,
                                self.signing_key,
                                algorithm=self.signing_key_algorithm)
        return signed_jwt
