import json
import time
import unittest
from unittest.mock import MagicMock

from planet.auth.auth_client import AuthClientException
from planet.auth.oidc.api_clients.jwks_api_client import JwksAPIClient
from planet.auth.oidc.token_validator import TokenValidator
from tests.unit.auth.util import TestTokenBuilder
from tests.util import tdata_resource_file_path

TEST_JWKS_ENDPOINT = 'https://blackhole.unittest.planet.com/oauth/jwks'


class TestTokenValidator(unittest.TestCase):
    token_builder_1 = None
    token_builder_2 = None
    jwks_response = None
    MIN_JWKS_FETCH_INTERVAL = 8

    @staticmethod
    def load_test_keypair(keypair_name):
        public_key_file = tdata_resource_file_path(
            'keys/{}_pub_jwk.json'.format(keypair_name))
        signing_key_file = tdata_resource_file_path(
            'keys/{}_priv_nopassword.test_pem'.format(keypair_name))

        with open(public_key_file, 'r') as file_r:
            pubkey_data = json.load(file_r)

        signing_key_id = pubkey_data['kid']
        signing_key_algorithm = pubkey_data['alg']
        token_builder = TestTokenBuilder(signing_key_file,
                                         signing_key_id,
                                         signing_key_algorithm)
        return pubkey_data, token_builder

    @classmethod
    def setUpClass(cls):
        pubkey_jwk_1, token_builder_1 = cls.load_test_keypair('keypair1')
        pubkey_jwk_2, token_builder_2 = cls.load_test_keypair('keypair2')
        # Monkey patch token builder 3 to use an algorithm different from what
        # is in the key files.
        pubkey_jwk_3, token_builder_3 = cls.load_test_keypair('keypair1')
        token_builder_3.signing_key_algorithm = 'RS512'

        cls.token_builder_1 = token_builder_1
        cls.token_builder_2 = token_builder_2
        cls.token_builder_3 = token_builder_3

        # key 2 is unknown to our mock jwks endpoint
        cls.jwks_response = {"keys": [pubkey_jwk_1]}

    def setUp(self):
        mock_jwks_client = JwksAPIClient(jwks_uri=TEST_JWKS_ENDPOINT)
        mock_jwks_client.jwks = MagicMock(return_value=self.jwks_response)
        self.under_test_1 = TokenValidator(jwks_client=mock_jwks_client)
        self.under_test_2 = TokenValidator(
            jwks_client=mock_jwks_client,
            min_jwks_fetch_interval=self.MIN_JWKS_FETCH_INTERVAL)

    def test_valid_access_token(self):
        under_test = self.under_test_1
        access_token = self.token_builder_1.construct_oidc_access_token()
        validated_claims = under_test.validate_token(
            access_token,
            issuer=self.token_builder_1.OIDC_ISSUER,
            audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE)
        self.assertEqual('unit_test_access_token_subject',
                         validated_claims['sub'])

    def test_access_token_unknown_signing_key(self):
        under_test = self.under_test_1
        access_token = self.token_builder_2.construct_oidc_access_token()
        with self.assertRaises(AuthClientException):
            under_test.validate_token(
                access_token,
                issuer=self.token_builder_2.OIDC_ISSUER,
                audience=self.token_builder_2.OIDC_ACCESS_TOKEN_AUDIENCE)

    def test_access_token_issuer_mismatch(self):
        under_test = self.under_test_1
        access_token = self.token_builder_1.construct_oidc_access_token()
        with self.assertRaises(AuthClientException):
            under_test.validate_token(
                access_token,
                issuer=self.token_builder_1.OIDC_ISSUER + "_make_it_mismatch",
                audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE)

    def test_access_token_incorrect_audience(self):
        under_test = self.under_test_1
        access_token = self.token_builder_1.construct_oidc_access_token()
        with self.assertRaises(AuthClientException):
            under_test.validate_token(
                access_token,
                issuer=self.token_builder_1.OIDC_ISSUER,
                audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE +
                "_make_it_mismatch")

    def test_access_token_expired(self):
        under_test = self.under_test_1
        access_token = self.token_builder_1.construct_oidc_access_token(ttl=3)
        time.sleep(5)
        with self.assertRaises(AuthClientException):
            under_test.validate_token(
                access_token,
                issuer=self.token_builder_1.OIDC_ISSUER,
                audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE)

    def test_access_token_missing_claim(self):
        under_test = self.under_test_1
        access_token = self.token_builder_1.construct_oidc_access_token()
        with self.assertRaises(AuthClientException):
            under_test.validate_token(
                access_token,
                issuer=self.token_builder_1.OIDC_ISSUER,
                audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE,
                required_claims=['missing_claim_1', 'missing_claim_2'])

    def test_id_token_nonce(self):
        under_test = self.under_test_1
        id_token_with_nonce = self.token_builder_1.construct_oidc_id_token(
            client_id='test_client_id', extra_claims={'nonce': '12345'})
        id_token_without_nonce = self.token_builder_1.construct_oidc_id_token(
            client_id='test_client_id')

        under_test.validate_id_token(id_token_with_nonce,
                                     issuer=self.token_builder_1.OIDC_ISSUER,
                                     client_id='test_client_id',
                                     nonce='12345')
        with self.assertRaises(AuthClientException):
            under_test.validate_id_token(
                id_token_with_nonce,
                issuer=self.token_builder_1.OIDC_ISSUER,
                client_id='test_client_id',
                nonce='67890')

        # TODO: See comments in the class.  Unsure if we should make missing
        #  nonce check's fatal when there is a nonce.  It would be very strict.
        under_test.validate_id_token(id_token_with_nonce,
                                     issuer=self.token_builder_1.OIDC_ISSUER,
                                     client_id='test_client_id',
                                     nonce=None)

        with self.assertRaises(AuthClientException):
            under_test.validate_id_token(
                id_token_without_nonce,
                issuer=self.token_builder_1.OIDC_ISSUER,
                client_id='test_client_id',
                nonce='12345')
        under_test.validate_id_token(id_token_with_nonce,
                                     issuer=self.token_builder_1.OIDC_ISSUER,
                                     client_id='test_client_id')

    def test_validate_id_token_multiple_audiences(self):
        under_test = self.under_test_1
        # Happy path, azp contains expected value when multiple
        # audience claims are present
        id_token = self.token_builder_1.construct_oidc_id_token(
            client_id='test_client_id',
            extra_claims={
                'aud':
                ['test_client_id', 'extra_audience_1', 'extra_audience_2'],
                'azp': 'test_client_id'
            })
        validated_claims = under_test.validate_id_token(
            id_token,
            issuer=self.token_builder_1.OIDC_ISSUER,
            client_id='test_client_id')
        self.assertEqual('test_client_id', validated_claims['sub'])

        # azp claim is missing when multiple audiences are present.
        id_token = self.token_builder_1.construct_oidc_id_token(
            client_id='test_client_id',
            extra_claims={
                'aud':
                ['test_client_id', 'extra_audience_1', 'extra_audience_2']
            })
        with self.assertRaises(AuthClientException):
            under_test.validate_id_token(
                id_token,
                issuer=self.token_builder_1.OIDC_ISSUER,
                client_id='test_client_id')

        # azp claim doesn't contain expected value when multiple audiences
        # are present
        id_token = self.token_builder_1.construct_oidc_id_token(
            client_id='test_client_id',
            extra_claims={
                'aud':
                ['test_client_id', 'extra_audience_1', 'extra_audience_2'],
                'azp': 'mismatch_azp'
            })
        with self.assertRaises(AuthClientException):
            under_test.validate_id_token(
                id_token,
                issuer=self.token_builder_1.OIDC_ISSUER,
                client_id='test_client_id')

    def test_min_jwks_fetch_interval(self):
        under_test = self.under_test_2
        token_known_signer = \
            self.token_builder_1.construct_oidc_access_token()
        token_unknown_signer = \
            self.token_builder_2.construct_oidc_access_token()

        # t0 - initial state
        self.assertEqual(0, under_test._jwks_client.jwks.call_count)

        # t1 - key miss loads keys
        with self.assertRaises(AuthClientException):
            under_test.validate_token(
                token_unknown_signer,
                issuer=self.token_builder_2.OIDC_ISSUER,
                audience=self.token_builder_2.OIDC_ACCESS_TOKEN_AUDIENCE)
        self.assertEqual(1, under_test._jwks_client.jwks.call_count)

        # t2 - key hit should pull from hot cache.
        under_test.validate_token(
            token_known_signer,
            issuer=self.token_builder_1.OIDC_ISSUER,
            audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE)
        self.assertEqual(1, under_test._jwks_client.jwks.call_count)

        # t3 - Repeated key hits and misses inside the fetch interval should
        # not trigger a reload of the jwks verification keys
        for n in range(5):
            with self.assertRaises(AuthClientException):
                under_test.validate_token(
                    token_unknown_signer,
                    issuer=self.token_builder_2.OIDC_ISSUER,
                    audience=self.token_builder_2.OIDC_ACCESS_TOKEN_AUDIENCE)
            under_test.validate_token(
                token_known_signer,
                issuer=self.token_builder_1.OIDC_ISSUER,
                audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE)

        self.assertEqual(1, under_test._jwks_client.jwks.call_count)

        # t4 - after the interval has passed, a we should reload for any
        # request.  If a miss comes in before the next interval, it should not
        # trigger a reload.  Also, it's not automatic, it's on demand.
        time.sleep(self.MIN_JWKS_FETCH_INTERVAL + 2)
        self.assertEqual(1, under_test._jwks_client.jwks.call_count)
        under_test.validate_token(
            token_known_signer,
            issuer=self.token_builder_1.OIDC_ISSUER,
            audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE)
        with self.assertRaises(AuthClientException):
            under_test.validate_token(
                token_unknown_signer,
                issuer=self.token_builder_2.OIDC_ISSUER,
                audience=self.token_builder_2.OIDC_ACCESS_TOKEN_AUDIENCE)
        self.assertEqual(2, under_test._jwks_client.jwks.call_count)

    def test_bad_algorithm(self):
        under_test = self.under_test_1
        test_token = self.token_builder_3.construct_oidc_access_token()
        with self.assertRaises(AuthClientException):
            under_test.validate_token(
                test_token,
                issuer=self.token_builder_1.OIDC_ISSUER,
                audience=self.token_builder_1.OIDC_ACCESS_TOKEN_AUDIENCE)

    # def test_max_jwks_age(self):
    #     # Feature not implemented.
    #     assert 0
