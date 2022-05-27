import asyncio

import cryptography.hazmat.primitives.serialization as crypto_serialization
import os
import socket
from pathlib import Path

from contextlib import closing

from planet.auth.auth_client import AuthClientConfig


def is_cicd() -> bool:
    # CI - GitHub
    # CI_COMMIT_SHA - GitLab
    return bool(os.getenv('CI') or os.getenv('CI_COMMIT_SHA'))


def tdata_resource_file_path(resource_file: str):
    # Why is this blowing up here but not in my other project?
    # file_path = importlib.resources.files('tests').joinpath("data/" +
    #                                                        resource_file)
    here = Path(os.path.abspath(os.path.dirname(__file__)))
    test_data_path = here / 'data'
    file_path = test_data_path / resource_file
    return file_path


def load_auth_client_config(named_config):
    sops_path = tdata_resource_file_path(
        'auth_client_configs/{}.sops.json'.format(named_config))
    clear_path = tdata_resource_file_path(
        'auth_client_configs/{}.json'.format(named_config))
    if sops_path.exists():
        conf_path = sops_path
    else:
        conf_path = clear_path
    return AuthClientConfig.from_file(conf_path)


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def load_rsa_private_key(key_file_path, password=None):
    with open(key_file_path, "rb") as key_file:
        if password:
            encoded_password = password.encode()
        else:
            encoded_password = None

        priv_key = crypto_serialization.load_pem_private_key(
            key_file.read(), password=encoded_password)
        if not priv_key:
            raise Exception(
                "Could not load private key from {}".format(key_file_path))

    return priv_key


def background(f):
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        loop = asyncio.get_event_loop()
        if callable(f):
            return loop.run_in_executor(None, f, *args, **kwargs)
        else:
            raise TypeError('Task must be a callable')

    return wrapped
