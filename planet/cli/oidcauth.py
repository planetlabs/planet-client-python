import click
import sys

from planet.auth.oidc.api_clients.api_client import OIDCAPIClientException
from planet.auth.oidc.oidc_token import FileBackedOidcToken

from planet.cx.commands.cli.options import \
    opt_auth_profile, \
    opt_auth_client_config_file, \
    opt_open_browser, \
    opt_token_file, \
    opt_token_scope
from planet.cx.commands.cli.util import get_auth_client, recast_exceptions_to_click

# TODO: per erik, tell the user we are going to launch a browser.
#       tell them "if there no browser works, tell them alternatives".
#       provide feedback on success / Failure of auth.


@click.group(
    'token',
    invoke_without_command=True,
    help='Commands to manage Planet OIDC auth tokens')
@click.pass_context
def oidc_token_group(context):
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        sys.exit(0)


# TODO: is it better to have these auth arguments on each command, or on the parent?
@oidc_token_group.command(
    'list-scopes',
    help='List well known token scopes that may be requested')
@opt_auth_client_config_file
@opt_auth_profile
@recast_exceptions_to_click(OIDCAPIClientException)
def do_list_scopes(auth_profile, auth_client_config_file):
    auth_client = get_auth_client(auth_profile, auth_client_config_file)
    available_scopes = auth_client.get_scopes()
    available_scopes.sort()
    print('Available token scopes:')
    if available_scopes:
        print('\t' + '\n\t'.join(available_scopes))
    else:
        print('\tNo scopes found')
        sys.exit(1)


# TODO: Google deprecated the behavior of --no-launch-browser in their gcloud cli,
#       which is what we patterned our flag after.  This was for security reasons. We
#       need to understand what and why, and what a solution is.
@oidc_token_group.command(
    'login',
    help='Perform a new login and save the tokens')
@opt_token_file
@opt_token_scope
@opt_open_browser
@opt_auth_client_config_file
@opt_auth_profile
@recast_exceptions_to_click(OIDCAPIClientException)
def do_token_login(token_file, auth_client_config_file, scope, auth_profile, open_browser):
    auth_client = get_auth_client(auth_profile, auth_client_config_file)
    token = auth_client.login(requested_scopes=scope, allow_open_browser=open_browser)
    token.set_path(token_file)
    token.save()


@oidc_token_group.command(
    'print-access-token',
    help='Print the current access token')
@opt_token_file
@opt_auth_profile
def do_print_access_token(token_file, auth_profile):
    saved_token = FileBackedOidcToken(None, token_file)
    print(saved_token.access_token())


@oidc_token_group.command(
    'refresh',
    help='Obtain a new token using the saved refresh token. It is possible'
         ' to request a refresh token with scopes that are different than'
         ' what is currently possessed, but you will never be granted'
         ' more scopes than what the user has authorized.')
@opt_token_file
@opt_token_scope
@opt_auth_client_config_file
@opt_auth_profile
@recast_exceptions_to_click(OIDCAPIClientException)
def do_token_refresh(token_file, auth_client_config_file, scope, auth_profile):
    saved_token = FileBackedOidcToken(None, token_file)
    saved_token.load()
    if not saved_token.refresh_token():
        raise Exception('No refresh_token found in ' + str(saved_token.path()))

    auth_client = get_auth_client(auth_profile, auth_client_config_file)
    saved_token.set_data(auth_client.refresh(saved_token.refresh_token(), scope).data())
    saved_token.save()


@oidc_token_group.command(
    'validate-access-token',
    help='Validate the access token associated with the current auth profile')
@opt_token_file
@opt_auth_client_config_file
@opt_auth_profile
@recast_exceptions_to_click(OIDCAPIClientException)
def do_validate_access_token(token_file, auth_client_config_file, auth_profile):
    saved_token = FileBackedOidcToken(None, token_file)
    saved_token.load()
    auth_client = get_auth_client(auth_profile, auth_client_config_file)
    validation_json = auth_client.validate_access_token(saved_token.access_token())

    if not validation_json or not validation_json.get('active'):
        print("INVALID")
        sys.exit(1)
    # print("OK")
    print(validation_json)


@oidc_token_group.command(
    'validate-id-token',
    help='Validate the ID token associated with the current auth profile')
@opt_token_file
@opt_auth_client_config_file
@opt_auth_profile
@recast_exceptions_to_click(OIDCAPIClientException)
def do_validate_id_token(token_file, auth_client_config_file, auth_profile):
    saved_token = FileBackedOidcToken(None, token_file)
    saved_token.load()
    auth_client = get_auth_client(auth_profile, auth_client_config_file)
    validation_json = auth_client.validate_id_token(saved_token.id_token())

    if not validation_json or not validation_json.get('active'):
        print("INVALID")
        sys.exit(1)
    # print("OK")
    print(validation_json)


@oidc_token_group.command(
    'validate-refresh-token',
    help='Validate the refresh token associated with the current auth profile')
@opt_token_file
@opt_auth_client_config_file
@opt_auth_profile
@recast_exceptions_to_click(OIDCAPIClientException)
def do_validate_refresh_token(token_file, auth_client_config_file, auth_profile):
    saved_token = FileBackedOidcToken(None, token_file)
    saved_token.load()
    auth_client = get_auth_client(auth_profile, auth_client_config_file)
    validation_json = auth_client.validate_refresh_token(saved_token.refresh_token())

    if not validation_json or not validation_json.get('active'):
        print("INVALID")
        sys.exit(1)
    # print("OK")
    print(validation_json)


@oidc_token_group.command(
    'revoke-access-token',
    help='Revoke the access token associated with the current auth profile')
@opt_token_file
@opt_auth_client_config_file
@opt_auth_profile
@recast_exceptions_to_click(OIDCAPIClientException)
def do_revoke_access_token(token_file, auth_client_config_file, auth_profile):
    saved_token = FileBackedOidcToken(None, token_file)
    saved_token.load()
    auth_client = get_auth_client(auth_profile, auth_client_config_file)
    auth_client.revoke_access_token(saved_token.access_token())


@oidc_token_group.command(
    'revoke-refresh-token',
    help='Revoke the refresh token associated with the current auth profile')
@opt_token_file
@opt_auth_client_config_file
@opt_auth_profile
@recast_exceptions_to_click(OIDCAPIClientException)
def do_revoke_refresh_token(token_file, auth_client_config_file, auth_profile):
    saved_token = FileBackedOidcToken(None, token_file)
    saved_token.load()
    auth_client = get_auth_client(auth_profile, auth_client_config_file)
    auth_client.revoke_refresh_token(saved_token.refresh_token())
