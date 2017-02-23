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
from itertools import chain
import json

from .cli import (
    cli,
    clientv1
)
from .opts import (
    asset_type_option,
    filter_opts,
    limit_option,
    pretty,
    search_request_opts,
    sort_order
)
from .util import (
    filter_from_opts,
    call_and_wrap,
    echo_json_response,
    read,
    request_from_opts,
)
from planet.api.utils import (
    handle_interrupt,
    monitor_stats,
    write_planet_json
)
from planet.api.helpers import (
    downloader,
)


@cli.command('init')
@click.option('--email', default=None, prompt=True)
@click.option('--password', default=None, prompt=True, hide_input=True)
def init(email, password):
    '''Login using email/password'''
    response = call_and_wrap(clientv1().login, email, password)
    write_planet_json({'key': response['api_key']})
    click.echo('initialized')


@cli.command('filter', context_settings=dict(max_content_width=119))
@filter_opts
def filter_dump(**kw):
    '''Build a AND filter from the specified filter options and output to
    stdout'''
    click.echo(json.dumps(filter_from_opts(**kw), indent=2))


@cli.command('quick-search')
@limit_option(100)
@pretty
@search_request_opts
@sort_order
def quick_search(limit, pretty, sort, **kw):
    '''Execute a quick search'''
    req = request_from_opts(**kw)
    cl = clientv1()
    page_size = min(limit, 250)
    echo_json_response(call_and_wrap(
        cl.quick_search, req, page_size=page_size, sort=sort
    ), pretty, limit)


@cli.command('create-search')
@pretty
@click.option('--name', required=True)
@search_request_opts
def create_search(pretty, **kw):
    '''Create a saved search'''
    req = request_from_opts(**kw)
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.create_search, req), pretty)


@cli.command('saved-search')
@click.argument('search_id', default='@-', required=False)
@sort_order
@pretty
@limit_option(100)
def saved_search(search_id, sort, pretty, limit):
    '''Execute a saved search'''
    sid = read(search_id)
    cl = clientv1()
    page_size = min(limit, 250)
    echo_json_response(call_and_wrap(
        cl.saved_search, sid, page_size=page_size, sort=sort
    ), limit=limit, pretty=pretty)


@cli.command('searches')
@click.option('--quick', is_flag=True, help='Quick searches')
@click.option('--saved', default=True, is_flag=True,
              help='Saved searches (default)')
def get_searches(quick, saved):
    '''List searches'''
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.get_searches, quick, saved), True)


@pretty
@search_request_opts
@click.option('--interval', default='month',
              type=click.Choice(['hour', 'day', 'month', 'week', 'year']),
              help='Specify the interval to aggregate by.')
@cli.command('stats')
def stats(pretty, **kw):
    '''Get search stats'''
    req = request_from_opts(**kw)
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.stats, req), pretty)


@asset_type_option
@search_request_opts
@click.option('--dest', type=click.Path(exists=True), help=('Location to '
              'download files to'))
@limit_option(None)
@cli.command('download')
def download(asset_type, dest, limit, **kw):
    '''Activate and download'''
    req = request_from_opts(**kw)
    cl = clientv1()
    page_size = min(limit, 250)
    items = cl.quick_search(req, page_size=page_size)
    asset_type = list(chain.from_iterable(asset_type))
    dl = downloader(cl, asset_type, dest or '.')
    monitor_stats(dl.stats, lambda x: click.echo(x, nl=False))
    handle_interrupt(dl.shutdown, dl.download, items.items_iter(limit))
