import click
import functools
import logging
import pathlib
from typing import Union

from planet.auth.auth_client import AuthClient, AuthClientConfig
from planet.cli.constants import \
    DEFAULT_OIDC_AUTH_CLIENT_CONFIG, \
    LEGACY_AUTH_CLIENT_CONFIG


logger = logging.getLogger(__name__)


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
    if profile:
        if profile.lower() == 'default':
            logger.debug('Using built-in "default" auth client configuration')
            return AuthClient.from_config(DEFAULT_OIDC_AUTH_CLIENT_CONFIG)
        if profile.lower() == 'legacy':
            logger.debug('Using built-in "legacy" auth client configuration')
            return AuthClient.from_config(LEGACY_AUTH_CLIENT_CONFIG)

    if not auth_client_config_file:
        # FIXME: this construction logic is redundant with code in options.py
        auth_config_path = pathlib.Path.home().joinpath(".planet/{}/auth_client.json".format(profile))
    else:
        auth_config_path = pathlib.Path(auth_client_config_file)

    if auth_config_path.exists():
        logger.debug('Using auth client configuration from "{}"'.format(str(auth_config_path)))
        client_config = AuthClientConfig.from_file(auth_client_config_file)
    else:
        logger.debug('Auth configuration file "{}" not found.'
                     '  Using built-in default auth client configuration'
                     .format(str(auth_config_path)))
        client_config = DEFAULT_OIDC_AUTH_CLIENT_CONFIG

    return AuthClient.from_config(client_config)
