import os
import sys
from pathlib import Path

from planet.auth.auth_client import AuthClientConfig


def is_interactive_shell():
    return sys.stdin.isatty()


def tdata_resource_file_path(resource_file: str):
    # Why is this blowing up here but not in my other project?
    # file_path = importlib.resources.files('tests').joinpath("data/" +
    #                                                        resource_file)
    here = Path(os.path.abspath(os.path.dirname(__file__)))
    test_data_path = here / 'data'
    file_path = test_data_path / resource_file
    return file_path


def load_auth_client_config(named_config):
    file_path = tdata_resource_file_path(
        'auth_client_configs/{}.json'.format(named_config))
    return AuthClientConfig.from_file(file_path)
