import click
import pathlib


from planet.constants import \
    ENV_AUTH_CLIENT_CONFIG_FILE, \
    ENV_AUTH_PROFILE, \
    ENV_AUTH_SCOPES, \
    ENV_AUTH_TOKEN_FILE


# TODO: rename simply profile, since it could be used for non-auth reasons?
def opt_auth_profile(function):
    function = click.option(
        '--auth-profile',
        # TODO: Present a choice based on scanned directories?
        #       We could look for ~/.planet/<profile>/
        #       To do this properly, we should probably have a planet.profile
        #       package or the like.
        # type=click.Choice(...),
        type=str,
        envvar=ENV_AUTH_PROFILE,
        help='Select the client profile to use.\nEnvironment variable: ' + ENV_AUTH_PROFILE,
        default='',  # 'default', # just construct our default paths inside ~/.planet, not ~/.planet/<profile>
        show_default=True,
        is_eager=True)(function)
    return function


def opt_auth_client_config_file(function):
    function = click.option(
        '--auth-client-config-file',
        type=click.Path(),
        envvar=ENV_AUTH_CLIENT_CONFIG_FILE,
        help='Auth client configuration file. The default will be constructed to '
             '~/.planet/<auth_profile>/auth_client.json\nEnvironment variable: ' + ENV_AUTH_CLIENT_CONFIG_FILE,
        default=None,
        show_default=True,
        callback=lambda ctx, param, value: pathlib.Path(value) if value else pathlib.Path.home().joinpath(".planet/{}/auth_client.json".format(ctx.params['auth_profile'])))(function) # noqa
    return function


def opt_open_browser(function):
    function = click.option(
        '--open-browser/--no-open-browser',
        help='Suppress the automatic opening of a browser window.',
        default=True,
        show_default=True)(function)
    return function


def opt_token_file(function):
    function = click.option(
        '--token-file',
        type=click.Path(),
        envvar=ENV_AUTH_TOKEN_FILE,
        help='Auth token file. The default will be constructed to '
             '~/.planet/<auth_profile>/token.json\nEnvironment variable: ' + ENV_AUTH_TOKEN_FILE,
        default=None,
        show_default=True,
        callback=lambda ctx, param, value: pathlib.Path(value) if value else pathlib.Path.home().joinpath(".planet/{}/token.json".format(ctx.params['auth_profile'])))(function) # noqa
    return function


def opt_token_scope(function):
    function = click.option(
        '--scope',
        multiple=True,
        type=str,
        envvar=ENV_AUTH_SCOPES,
        help='Token scopes to request. Specify multiple options to request multiple scopes. '
             'When set via environment variable, scopes should be white space delimited. '
             '\nEnvironment variable: ' + ENV_AUTH_SCOPES,
        default=None,
        show_default=True)(function)
    return function
