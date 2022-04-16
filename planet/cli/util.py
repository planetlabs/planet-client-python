import click
import functools
import pathlib
from typing import Union

from planet.auth.auth_client import AuthClient, AuthClientConfig
from planet.cx.commands.cli.constants import DEFAULT_OIDC_CLIENT_CONFIG


def recast_exceptions_to_click(*exceptions, **params):
    if not exceptions:
        exceptions = (Exception,)
    # params.get('some_arg', 'default')

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                raise click.ClickException(str(e))
        return wrapper
    return decorator


def get_auth_client(profile: str, auth_client_config_file: Union[str, pathlib.PurePath]) -> AuthClient:
    if not auth_client_config_file:
        # FIXME: this construction logic is redundant with code in options.py
        auth_config_path = pathlib.Path.home().joinpath(".planet/{}/token.json".format(profile))
    else:
        auth_config_path = pathlib.Path(auth_client_config_file)

    if auth_config_path.exists():
        client_config = AuthClientConfig.from_file(auth_client_config_file)
    else:
        client_config = DEFAULT_OIDC_CLIENT_CONFIG

    return AuthClient.from_config(client_config)
