import click
import pathlib


from planet.cx.commands.cli.constants import \
    ENV_AUTH_CLIENT_CONFIG_FILE, \
    ENV_AUTH_PASSWORD, \
    ENV_AUTH_PROFILE, \
    ENV_AUTH_SCOPES, \
    ENV_AUTH_TOKEN_FILE, \
    ENV_AUTH_USERNAME, \
    ENV_FOO_ID, \
    ENV_FOO_SERVICE_URL, \
    ENV_LOGLEVEL


# TODO: rename simply profile, since it could be used for non-auth reasons?
def opt_auth_profile(function):
    function = click.option(
        '--auth-profile',
        # TODO: Present a choice based on scanned directories?
        #       We could look for ~/.planet/<profile>/
        # TODO: we need a notion of built-in profiles. "default" and "legacy" are needed for the CLI.
        # type=click.Choice(...),
        type=str,
        envvar=ENV_AUTH_PROFILE,
        help='Select the client profile to use. Profiles are defined by creating a subdirectory'
             ' ~/.planet/. Additionally, the built in profiles "default" and "legacy" are understood.'
             '\nEnvironment variable: ' + ENV_AUTH_PROFILE,
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


def opt_auth_password(function):
    function = click.option(
        '--password',
        type=str,
        envvar=ENV_AUTH_PASSWORD,
        help='Password used for authentication. May not be used by all authentication mechanisms.'
             '\nEnvironment variable: ' + ENV_AUTH_PASSWORD,
        default=None,
        show_default=True)(function)
    return function


def opt_auth_username(function):
    function = click.option(
        '--username', '--email',
        type=str,
        envvar=ENV_AUTH_USERNAME,
        help='Username used for authentication.  May not be used by all authentication mechanisms.'
             '\nEnvironment variable: ' + ENV_AUTH_USERNAME,
        default=None,
        show_default=True)(function)
    return function


def opt_foo_id_required(function):
    function = click.option(
        '--foo-id',
        type=str, envvar=ENV_FOO_ID,
        help='Specify the id of a foo.',
        required=True)(function)
    return function


def opt_foo_service_url(function):
    function = click.option(
        '--foo-service-url',
        type=str,
        envvar=ENV_FOO_SERVICE_URL,
        help='Specify the URL for the foo service endpoint.'
             '\nEnvironment variable: ' + ENV_FOO_SERVICE_URL,
        default='http://localhost:8081',
        show_default=True)(function)
    return function


def opt_loglevel(function):
    function = click.option(
        '-l', '--loglevel',
        envvar=ENV_LOGLEVEL,
        help='Set the log level.\nEnvironment variable: ' + ENV_LOGLEVEL,
        type=click.Choice(['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], case_sensitive=False),
        default='INFO',
        show_default=True)(function)
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
