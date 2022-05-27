import click
import sys

from planet.auth import AuthException, FileBackedOidcCredential
from planet.auth import FileBackedPlanetLegacyApiKey

from planet.cli.options import \
    opt_auth_password, \
    opt_auth_username, \
    opt_open_browser, \
    opt_token_audience, \
    opt_token_scope
from planet.cli.util import recast_exceptions_to_click
from .io_helper import echo_json


# FIXME: Might we have global options for other output formats?
# FIXME: This is consistent with other CLI commands in the Planet Python SDK,
#        but adding JSON quotes for output like API keys or access tokens that
#        are simple strings may be problematic.  CLI commands like
#        "print-access-token" are useful for injecting these strings into
#        other flows (e.g. using it to grab tokens in a shell script for curl
#        or what-have-you). Forcing particular escaping may be annoying for
#        users.  (This is why tools like "jq" have "-r" options for raw
#        output.)
# FIXME: Handling of "pretty" option from CLI.
def print_obj(obj):
    echo_json(obj, pretty=True)


@click.group('auth', invoke_without_command=True)
@click.pass_context
def auth_cmd_group(ctx):
    '''
    Manage authentication and credentials.

    The auth command exists to interface with authentication services,
    and manage authentication credentials that are used for interacting with
    other services.  The interface is heavily influenced by the capabilities
    of OAuth/OIDC, but this command currently services multiple authentication
    mechanisms.

    Since the authentication command exists to prepare a runtime environment
    for calling other commands, and not just for interacting with auth
    services in a silo, some authentication command options are necessarily
    connected to the CLI base rather than the auth command or specific
    sub-commands.

    Central to how the auth command works is the auth profile.
    The auth profile controls how the CLI interacts with authentication
    services to obtain service tokens, as well specifying how those tokens
    are subsequently used to interact with other services.  Auth profiles may
    also be used to manage different client accounts.

    The auth profile also controls where authentication configuration
    files and authentication tokens are stored on disk.  When a given
    profile is selected, the ~/.planet/<profile> directory will be used in
    the user’s home directory.  Profile names will be down-cased to
    all lowercase. Within the currently active profile directory, auth
    credentials will be stored in a token.json file, and auth profile
    configuration will be stored in an auth_client.json file.  The contents
    and format of these files vary depending on the specific auth mechanism
    configured for the auth profile.  If present, auth_client.sops.json
    will take priority over auth_client.json, allowing clients that have
    secrets to securely store this information on disk using SOPS encryption.
    Similarly, a token.sops.json file will take priority over a token.json
    file.  SOPS is not the default fallback since the configuration of SOPS
    is outside the scope of Planet tooling.

    The following auth profiles are built in, and do not require any user
    configuration.  When a built in profile is used, it will be used to
    locate the token.json file, and it will configure how the CLI
    interacts with auth services, as well as how tokens obtained from those
    auth services are used to talk to other services.  When using
    built in auth profiles, any related auth_client.json configuration files
    will be ignored. (FIXME: might we want to allow user override of the
    default behavior for their environment?) The following built-in auth
    profiles exist:

    default - Selected the default authentication profile for the CLI.
    This is redundant with not specifying any value for the auth profile.
    The default auth profile will use Planet’s newer OAuth based mechanisms
    to log into the user’s Planet account using a web browser, obtain the
    user’s authorization, and save the resulting (short lived) access tokens
    to the profile directory.  The CLI will manage automatically refreshing
    these tokens as required in the background without any user interaction.
    OAuth mechanisms have been designed to allow a user to have control
    over the breadth of access granted to the user’s account.

    legacy - Select Planet legacy API mechanisms. Planet legacy API
    mechanisms utilize simple username / password based logins, and cache a
    long lived API key that has the full power of the user’s account.
    '''
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)


@auth_cmd_group.command('list-scopes')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_list_scopes(ctx):
    '''
    List available OAuth scopes.

    For authentication profiles that support OAuth scopes, this command
    queries the auth server for available scopes that may be requested.
    '''
    auth_client = ctx.obj['AUTH'].auth_client()
    available_scopes = auth_client.get_scopes()
    available_scopes.sort()
    if available_scopes:
        print_obj(available_scopes)
    else:
        print_obj([])


# TODO: Google deprecated the behavior of --no-launch-browser in their
#       gcloud cli, which is what we patterned our flag after. This was for
#       "security reasons". We need to understand what and why, and what a
#       solution is.
@auth_cmd_group.command('login')
@opt_token_scope
@opt_token_audience
@opt_open_browser
@opt_auth_password
@opt_auth_username
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_token_login(ctx, scope, audience, open_browser, username, password):
    '''
    Perform an initial login, obtain user authorization, and save access
    tokens for the selected authentication profile.  The specific process
    and supported options depends on the auth profile selected.
    '''
    auth_client = ctx.obj['AUTH'].auth_client()
    token = auth_client.login(requested_scopes=scope,
                              requested_audiences=audience,
                              allow_open_browser=open_browser,
                              username=username,
                              password=password)
    token.set_path(ctx.obj['AUTH'].token_file_path())
    token.save()


@auth_cmd_group.command('print-access-token')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_print_access_token(ctx):
    '''
    Show the OAuth access token used by the currently selected authentication
    profile. Auth profiles that do not use OAuth will not support this
    command.
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    print_obj(saved_token.access_token())


@auth_cmd_group.command('print-api-key')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_print_api_key(ctx):
    '''
    Show the API Key used by the currently selected authentication profile.
    Auth profiles that do not use API keys will not support this command.
    '''
    saved_token = FileBackedPlanetLegacyApiKey(
        None, ctx.obj['AUTH'].token_file_path())
    print_obj(saved_token.legacy_api_key())


@auth_cmd_group.command('refresh')
@opt_token_scope
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_token_refresh(ctx, scope):
    '''
    Obtain a new token using the saved refresh token.

    It is possible to request a refresh token with scopes that are different
    than what is currently possessed, but you will never be granted
    more scopes than what the user has authorized.  This functionality
    is only supported for authentication mechanisms that support
    the concepts of separate (short lived) access tokens and
    (long lived) refresh tokens.
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    if not saved_token.refresh_token():
        raise Exception('No refresh_token found in ' + str(saved_token.path()))

    saved_token.set_data(
        auth_client.refresh(saved_token.refresh_token(), scope).data())
    saved_token.save()


@auth_cmd_group.command('validate-access-token')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_validate_access_token(ctx):
    '''
    Validate the access token associated with the current profile.
    This functionality is only available for OAuth based auth profiles.
    Validation is performed by calling out to the auth provider's
    token introspection network service.
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    validation_json = auth_client.validate_access_token(
        saved_token.access_token())

    if not validation_json or not validation_json.get('active'):
        print_obj("INVALID")
        sys.exit(1)
    # print_obj("OK")
    print_obj(validation_json)


# XXX Garbage for investigation.  This doesn't belong in the client. Access
# tokens are technically opaque to us. If we want to plumb a general purpose
# token util command, that maybe doesn't belong here in this "auth_cmd", which
# is geared towards API client use cases.  That probably calls for a
# differently focused 'token' command group
# TODO: migrate to 'token validate-local' or the like
@auth_cmd_group.command('validate-access-token-local')
@click.pass_context
@opt_token_audience
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_validate_access_token_local(ctx, audience):
    '''
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    # Throws on error.
    validation_json = auth_client.validate_access_token_local(
        access_token=saved_token.access_token(), required_audience=audience)
    print_obj(validation_json)


@auth_cmd_group.command('validate-id-token')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_validate_id_token(ctx):
    '''
    Validate the ID token associated with the current profile.
    This functionality is only available for OAuth based auth profiles.
    Validation is performed by calling out to the auth provider's
    token introspection network service.
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    validation_json = auth_client.validate_id_token(saved_token.id_token())

    if not validation_json or not validation_json.get('active'):
        print_obj("INVALID")
        sys.exit(1)
    # print_obj("OK")
    print_obj(validation_json)


@auth_cmd_group.command('validate-id-token-local')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_validate_id_token_local(ctx):
    '''
    Validate the ID token associated with the current profile.
    This functionality is only available for OAuth based auth profiles.
    This command validates the ID token locally, checking the token signature
    and claims against expected values.  While validation is performed
    locally, network access is still required to obtain the signing keys
    from the auth provider.
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    # Throws on error.
    validation_json = auth_client.validate_id_token_local(
        saved_token.id_token())
    # print_obj("OK")
    print_obj(validation_json)


@auth_cmd_group.command('validate-refresh-token')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_validate_refresh_token(ctx):
    '''
    Validate the refresh token associated with the current profile.
    This functionality is only available for OAuth based auth profiles.
    Validation is performed by calling out to the auth provider's
    token introspection network service.
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    validation_json = auth_client.validate_refresh_token(
        saved_token.refresh_token())

    if not validation_json or not validation_json.get('active'):
        print_obj("INVALID")
        sys.exit(1)
    # print_obj("OK")
    print_obj(validation_json)


@auth_cmd_group.command('revoke-access-token')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_revoke_access_token(ctx):
    '''
    Revoke the access token associated with the current profile.

    Revoking the access token does not revoke the refresh token, which will
    remain powerful.

    It should be noted that while this command revokes the access token with
    the auth services, access tokens are bearer tokens, and may still be
    accepted by some service endpoints.  Generally, it should be the case only
    less sensitive endpoints accept such tokens. High value services
    (such as admin services) will double verify tokens - insuring that they
    pass local validation, and checking with the auth provider that they have
    not been revoked.
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    auth_client.revoke_access_token(saved_token.access_token())


@auth_cmd_group.command('revoke-refresh-token')
@click.pass_context
@recast_exceptions_to_click(AuthException, FileNotFoundError)
def do_revoke_refresh_token(ctx):
    '''
    Revoke the refresh token associated with the current profile.

    After the refresh token has been revoked, it will be necessary to login
    again to access other services.  Revoking the refresh token does not
    revoke the current access token, which may remain potent until its
    natural expiration time if not also revoked.
    '''
    saved_token = FileBackedOidcCredential(None,
                                           ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    auth_client.revoke_refresh_token(saved_token.refresh_token())
