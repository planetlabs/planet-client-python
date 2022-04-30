import importlib.resources
import sys

from planet.auth.auth_client import AuthClientConfig


def is_interactive_shell():
    return sys.stdin.isatty()


def tdata_resource_file_path(resource_file: str):
    file_path = importlib.resources.files('tests').joinpath("data/" +
                                                            resource_file)
    return file_path


def load_auth_client_config(named_config):
    file_path = tdata_resource_file_path(
        'auth_client_configs/{}.json'.format(named_config))
    return AuthClientConfig.from_file(file_path)
