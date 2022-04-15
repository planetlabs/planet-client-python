import base64
import hashlib
import secrets

_DEFAULT_LENGTH = 96


def generate_nonce(length):
    return ''.join([str(secrets.randbelow(10)) for i in range(length)])


def create_challenge(v):
    code_challenge = hashlib.sha256(v.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')
    return code_challenge


def create_verifier(length=_DEFAULT_LENGTH):
    code_verifier = secrets.token_urlsafe(length)
    return code_verifier


def create_pkce_challenge_verifier_pair(length=_DEFAULT_LENGTH):
    v = create_verifier(length)
    c = create_challenge(v)
    return v, c
