# FIXME: Rename? This isn't strictly only an "OIDC" Auth CLI interface
#        anymore. It works with any auth provider that provided an
#        AuthClient interface. But, this is a heavily OIDC influenced
#        interface.  Should we split oidc and legacy into sub-commands?
import click
import sys

from planet.auth.auth_client import AuthClientException
from planet.auth.oidc.oidc_token import FileBackedOidcToken
from planet.auth.planet_legacy.legacy_api_key import \
    FileBackedPlanetLegacyAPIKey

from planet.cx.commands.cli.options import \
    opt_auth_password, \
    opt_auth_username, \
    opt_open_browser, \
    opt_token_scope
from planet.cx.commands.cli.util import recast_exceptions_to_click


@click.group('auth',
             invoke_without_command=True,
             help='Commands to manage Planet auth tokens')
@click.pass_context
def oidc_token_group(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)


@oidc_token_group.command('list-scopes',
                          help='List well known scopes that may be requested.')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_list_scopes(ctx):
    auth_client = ctx.obj['AUTH'].auth_client()
    available_scopes = auth_client.get_scopes()
    available_scopes.sort()
    print('Available scopes:')
    if available_scopes:
        print('\t' + '\n\t'.join(available_scopes))
    else:
        print('\tNo scopes found')
        sys.exit(1)


# TODO: Google deprecated the behavior of --no-launch-browser in their
#       gcloud cli, which is what we patterned our flag after. This was for
#       "security reasons". We need to understand what and why, and what a
#       solution is.
@oidc_token_group.command(
    'login',
    help='Perform a new login and save the tokens. Not all authentication'
    ' mechanisms support all options.')
@opt_token_scope
@opt_open_browser
@opt_auth_password
@opt_auth_username
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_token_login(ctx, scope, open_browser, username, password):
    auth_client = ctx.obj['AUTH'].auth_client()
    token = auth_client.login(requested_scopes=scope,
                              allow_open_browser=open_browser,
                              username=username,
                              password=password)
    token.set_path(ctx.obj['AUTH'].token_file_path())
    token.save()


@oidc_token_group.command('print-access-token',
                          help='Print the current access token.')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_print_access_token(ctx):
    # FIXME: this will only work for OIDC auth mechanisms. Maybe that's OK.
    saved_token = FileBackedOidcToken(None, ctx.obj['AUTH'].token_file_path())
    print(saved_token.access_token())


@oidc_token_group.command(
    'print-api-key',
    help='Print API key associated with the current auth profile.')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_print_api_key(ctx):
    # FIXME: this will only work for legacy auth mechanisms. Maybe that's OK.
    saved_token = FileBackedPlanetLegacyAPIKey(
        None, ctx.obj['AUTH'].token_file_path())
    print(saved_token.legacy_api_key())


@oidc_token_group.command(
    'refresh',
    help='Obtain a new token using the saved refresh token. It is possible'
    ' to request a refresh token with scopes that are different than'
    ' what is currently possessed, but you will never be granted'
    ' more scopes than what the user has authorized.  This functionality'
    ' is only supported for authentication mechanisms that support'
    ' the concepts of separate (short lived) access tokens and '
    ' (long lived) refresh tokens.')
@opt_token_scope
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_token_refresh(ctx, scope):
    saved_token = FileBackedOidcToken(None, ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    if not saved_token.refresh_token():
        raise Exception('No refresh_token found in ' + str(saved_token.path()))

    saved_token.set_data(
        auth_client.refresh(saved_token.refresh_token(), scope).data())
    saved_token.save()


@oidc_token_group.command(
    'validate-access-token',
    help='Validate the access token associated with the current profile')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_validate_access_token(ctx):
    saved_token = FileBackedOidcToken(None, ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    validation_json = auth_client.validate_access_token(
        saved_token.access_token())

    if not validation_json or not validation_json.get('active'):
        print("INVALID")
        sys.exit(1)
    # print("OK")
    print(validation_json)


@oidc_token_group.command(
    'validate-id-token',
    help='Validate the ID token associated with the current profile')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_validate_id_token(ctx):
    saved_token = FileBackedOidcToken(None, ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    validation_json = auth_client.validate_id_token(saved_token.id_token())

    if not validation_json or not validation_json.get('active'):
        print("INVALID")
        sys.exit(1)
    # print("OK")
    print(validation_json)


@oidc_token_group.command(
    'validate-id-token-local',
    help='Validate the ID token associated with the current profile locally.')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_validate_id_token_local(ctx):
    saved_token = FileBackedOidcToken(None, ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    # Throws on error.
    validation_json = auth_client.validate_id_token_local(
        saved_token.id_token())
    # print("OK")
    print(validation_json)


@oidc_token_group.command(
    'validate-refresh-token',
    help='Validate the refresh token associated with the current profile')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_validate_refresh_token(ctx):
    saved_token = FileBackedOidcToken(None, ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    validation_json = auth_client.validate_refresh_token(
        saved_token.refresh_token())

    if not validation_json or not validation_json.get('active'):
        print("INVALID")
        sys.exit(1)
    # print("OK")
    print(validation_json)


@oidc_token_group.command(
    'revoke-access-token',
    help='Revoke the access token associated with the current profile')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_revoke_access_token(ctx):
    saved_token = FileBackedOidcToken(None, ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    auth_client.revoke_access_token(saved_token.access_token())


@oidc_token_group.command(
    'revoke-refresh-token',
    help='Revoke the refresh token associated with the current profile')
@click.pass_context
@recast_exceptions_to_click(AuthClientException, FileNotFoundError)
def do_revoke_refresh_token(ctx):
    saved_token = FileBackedOidcToken(None, ctx.obj['AUTH'].token_file_path())
    auth_client = ctx.obj['AUTH'].auth_client()
    saved_token.load()
    auth_client.revoke_refresh_token(saved_token.refresh_token())
