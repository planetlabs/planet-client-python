# Copyright 2017 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import click
import logging
import sys

from planet import api
from planet.api.__version__ import __version__
from planet.api.utils import write_planet_json
from .util import call_and_wrap

client_params = {}


def clientv1():
    return api.ClientV1(**client_params)


def configure_logging(verbosity):
    '''configure logging via verbosity level of between 0 and 2 corresponding
    to log levels warning, info and debug respectfully.'''
    log_level = max(logging.DEBUG, logging.WARNING - logging.DEBUG*verbosity)
    logging.basicConfig(
        stream=sys.stderr, level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    urllib3_logger = logging.getLogger(
        'requests.packages.urllib3')
    urllib3_logger.setLevel(log_level)

    # if debug level set then its nice to see the headers of the request
    if log_level == logging.DEBUG:
        try:
            import http.client as http_client
        except ImportError:
            # Python 2
            import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1


@click.group()
@click.pass_context
@click.option('-w', '--workers', default=4,
              help=('The number of concurrent downloads when requesting '
                    'multiple scenes. - Default 4'))
@click.option('-v', '--verbose', count=True, help='Specify verbosity')
@click.option('-k', '--api-key',
              help='Valid API key - or via ENV variable %s' % api.auth.ENV_KEY)
@click.option('-u', '--base-url', envvar='PL_API_BASE_URL',
              help='Change the base Planet API URL or ENV PL_API_BASE_URL'
                   ' - Default https://api.planet.com/')
@click.version_option(version=__version__, message='%(version)s')
def cli(context, verbose, api_key, base_url, workers):
    '''Planet API Client'''

    configure_logging(verbose)

    client_params.clear()
    client_params['api_key'] = api_key
    client_params['workers'] = workers
    if base_url:
        client_params['base_url'] = base_url


@cli.command('help')
@click.argument("command", default="")
@click.pass_context
def help(context, command):
    '''Get command help'''
    if command:
        cmd = cli.commands.get(command, None)
        if cmd:
            context.info_name = command
            click.echo(cmd.get_help(context))
        else:
            raise click.ClickException('no command: %s' % command)
    else:
        click.echo(cli.get_help(context))


@cli.command('init')
@click.option('--email', default=None, prompt=True, help=(
    'The email address associated with your Planet credentials.'
))
@click.option('--password', default=None, prompt=True, hide_input=True, help=(
    'Account password. Will not be saved.'
))
def init(email, password):
    '''Login using email/password'''
    response = call_and_wrap(clientv1().login, email, password)
    write_planet_json({'key': response['api_key']})
    click.echo('initialized')
