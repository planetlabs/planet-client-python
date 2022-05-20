import click

from planet.auth import Profile
from planet.auth.constants import \
    ENV_AUTH_CLIENT_CONFIG_FILE, \
    ENV_AUTH_PASSWORD, \
    ENV_AUTH_PROFILE, \
    ENV_AUTH_SCOPES, \
    ENV_AUTH_TOKEN_FILE, \
    ENV_AUTH_USERNAME, \
    TOKEN_FILE_SOPS, \
    TOKEN_FILE_PLAIN, \
    AUTH_CONFIG_FILE_SOPS, \
    AUTH_CONFIG_FILE_PLAIN
from planet.cx.commands.cli.constants import \
    ENV_FOO_ID, \
    ENV_FOO_SERVICE_URL, \
    ENV_LOGLEVEL


# TODO: rename simply profile, since it could be used for non-auth reasons?
def opt_auth_profile(function):
    function = click.option(
        '--auth-profile',
        # TODO: Present a choice based on scanned directories?
        #       We could look for ~/.planet/<profile>/
        # type=click.Choice(...),
        type=str,
        envvar=ENV_AUTH_PROFILE,
        help='Select the client profile to use. Profiles are defined by'
        ' creating a subdirectory ~/.planet/. Additionally, the built in'
        ' profiles "default" and "legacy" are understood.  The auth profile'
        ' controls how the software interacts with Planet authentication'
        ' services, as well as how it authenticates to other Planet APIs',
        default='',
        show_envvar=True,
        show_default=True,
        is_eager=True)(function)
    return function


def opt_auth_client_config_file(function):
    function = click.option(
        '--auth-client-config-file',
        type=click.Path(),
        envvar=ENV_AUTH_CLIENT_CONFIG_FILE,
        help='Auth client configuration file. The default will be'
        ' constructed to ~/.planet/<auth_profile>/{} or'
        ' ~/.planet/<auth_profile>/{}'.format(AUTH_CONFIG_FILE_SOPS,
                                              AUTH_CONFIG_FILE_PLAIN),
        default=None,
        show_envvar=True,
        show_default=True,
        callback=lambda ctx,
        param,
        value: Profile.get_profile_file_path_with_priority(
            [AUTH_CONFIG_FILE_SOPS, AUTH_CONFIG_FILE_PLAIN],
            ctx.params['auth_profile'],
            value))(function)
    return function


def opt_auth_password(function):
    function = click.option(
        '--password',
        type=str,
        envvar=ENV_AUTH_PASSWORD,
        help='Password used for authentication. May not be used by all'
        ' authentication mechanisms.',
        default=None,
        show_envvar=True,
        show_default=True)(function)
    return function


def opt_auth_username(function):
    function = click.option(
        '--username',
        '--email',
        type=str,
        envvar=ENV_AUTH_USERNAME,
        help='Username used for authentication.  May not be used by all'
        ' authentication mechanisms.',
        default=None,
        show_envvar=True,
        show_default=True)(function)
    return function


def opt_foo_id_required(function):
    function = click.option('--foo-id',
                            type=str,
                            envvar=ENV_FOO_ID,
                            show_envvar=True,
                            help='Specify the id of a foo.',
                            required=True)(function)
    return function


def opt_foo_service_url(function):
    function = click.option(
        '--foo-service-url',
        type=str,
        envvar=ENV_FOO_SERVICE_URL,
        help='Specify the URL for the foo service endpoint.',
        default='http://localhost:8081',
        show_envvar=True,
        show_default=True)(function)
    return function


def opt_loglevel(function):
    function = click.option(
        '-l',
        '--loglevel',
        envvar=ENV_LOGLEVEL,
        help='Set the log level.',
        type=click.Choice(['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                          case_sensitive=False),
        default='INFO',
        show_envvar=True,
        show_default=True)(function)
    return function


def opt_okta_tenant(function):
    function = click.option('--okta-tenant',
                            type=str,
                            envvar='PL_OKTA_TENANT',
                            help='Specify the URL of the okta tenant.'
                            '\nEnvironment variable: PL_OKTA_TENANT',
                            default='https://account-next.planet.com',
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
        help='Auth token file. The default will be constructed to'
        ' ~/.planet/<auth_profile>/{} or ~/.planet/<auth_profile>/{}'.format(
            TOKEN_FILE_SOPS, TOKEN_FILE_PLAIN),
        default=None,
        show_envvar=True,
        show_default=True,
        callback=lambda ctx,
        param,
        value: Profile.get_profile_file_path_with_priority(
            [TOKEN_FILE_SOPS, TOKEN_FILE_PLAIN],
            ctx.params['auth_profile'],
            value))(function)
    return function


def opt_token_scope(function):
    function = click.option(
        '--scope',
        multiple=True,
        type=str,
        envvar=ENV_AUTH_SCOPES,
        help='Token scopes to request. Specify multiple options to request'
        ' multiple scopes. When set via environment variable, scopes'
        ' should be white space delimited. Default value is determined'
        ' by the selected auth profile.',
        default=None,
        show_envvar=True,
        show_default=True)(function)
    return function
