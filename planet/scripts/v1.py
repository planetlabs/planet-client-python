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
from .types import (
    metavar_docs
)
from .util import (
    filter_from_opts,
    call_and_wrap,
    echo_json_response,
    read,
    search_req_from_opts,
)
from planet.api.utils import (
    handle_interrupt,
    monitor_stats,
    write_planet_json
)
from planet.api.helpers import (
    downloader,
)


filter_opts_epilog = '\nFilter Formats:\n\n' + \
                     '\n'.join(['%s\n\n%s' % (k, v.replace('    ', ''))
                                for k, v in metavar_docs.items()])


@cli.command('init')
@click.option('--email', default=None, prompt=True)
@click.option('--password', default=None, prompt=True, hide_input=True)
def init(email, password):
    '''Login using email/password'''
    response = call_and_wrap(clientv1().login, email, password)
    write_planet_json({'key': response['api_key']})
    click.echo('initialized')


@cli.command('filter', epilog=filter_opts_epilog)
@filter_opts
def filter_dump(**kw):
    '''Output a AND filter as JSON to stdout.

    If provided using --filter-json, combine the filters.

    The output is suitable for use in other commands via the
    --filter-json option.
    '''
    click.echo(json.dumps(filter_from_opts(**kw), indent=2))


@cli.command('quick-search', epilog=filter_opts_epilog)
@limit_option(100)
@pretty
@search_request_opts
@sort_order
def quick_search(limit, pretty, sort, **kw):
    '''Execute a quick search.'''
    req = search_req_from_opts(**kw)
    cl = clientv1()
    page_size = min(limit, 250)
    echo_json_response(call_and_wrap(
        cl.quick_search, req, page_size=page_size, sort=sort
    ), pretty, limit)


@cli.command('create-search', epilog=filter_opts_epilog)
@pretty
@click.option('--name', required=True)
@search_request_opts
def create_search(pretty, **kw):
    '''Create a saved search'''
    req = search_req_from_opts(**kw)
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
@cli.command('stats', epilog=filter_opts_epilog)
def stats(pretty, **kw):
    '''Get search stats'''
    req = search_req_from_opts(**kw)
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.stats, req), pretty)


@asset_type_option
@search_request_opts
@click.option('--search-id', type=str, help=(
    'Use the specified search'
))
@click.option('--dry-run', is_flag=True, help=(
    'Only report the number of items that would be downloaded.'
))
@click.option('--dest', type=click.Path(exists=True), help=('Location to '
              'download files to'))
@limit_option(None)
@cli.command('download', epilog=filter_opts_epilog)
def download(asset_type, dest, limit, search_id, dry_run, **kw):
    '''Activate and download'''
    cl = clientv1()
    page_size = min(limit or 250, 250)
    asset_type = list(chain.from_iterable(asset_type))
    if search_id:
        if dry_run:
            raise click.ClickException(
                'dry-run not supported with saved search')
        if any(kw[s] for s in kw if s not in ('item_type',)):
            raise click.ClickException(
                'search options not supported with saved search')
        items = cl.saved_search(search_id, page_size=page_size)
    else:
        req = search_req_from_opts(**kw)
        if dry_run:
            req['interval'] = 'year'
            if not req['filter']['config']:
                raise click.ClickException(
                    'dry-run not supported with open query')
            stats = cl.stats(req).get()
            item_cnt = sum([b['count'] for b in stats['buckets']])
            asset_cnt = item_cnt * len(asset_type)
            click.echo(
                'would download approximately %d assets from %s items' %
                (asset_cnt, item_cnt)
            )
            return
        else:
            items = cl.quick_search(req, page_size=page_size)

    dl = downloader(cl, asset_type, dest or '.')
    monitor_stats(dl.stats, lambda x: click.echo(x, nl=False))
    handle_interrupt(dl.shutdown, dl.download, items.items_iter(limit))
