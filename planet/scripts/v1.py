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
    asset_type_perms,
    filter_opts,
    limit_option,
    pretty,
    search_request_opts,
    sort_order
)
from .types import (
    AssetTypePerm,
    metavar_docs
)
from .util import (
    call_and_wrap,
    check_writable,
    click_exception,
    filter_from_opts,
    downloader_output,
    echo_json_response,
    read,
    search_req_from_opts,
)
from planet.api.utils import (
    handle_interrupt
)
from planet.api import downloader


filter_opts_epilog = '\nFilter Formats:\n\n' + \
                     '\n'.join(['%s\n\n%s' % (k, v.replace('    ', '')
                                              .replace('``', '\''))
                                for k, v in metavar_docs.items()])


@cli.group('data')
def data():
    '''Commands for interacting with the Data API'''
    pass


@data.command('filter', epilog=filter_opts_epilog)
@filter_opts
def filter_dump(**kw):
    '''Output a AND filter as JSON to stdout.

    If provided using --filter-json, combine the filters.

    The output is suitable for use in other commands via the
    --filter-json option.
    '''
    click.echo(json.dumps(filter_from_opts(**kw), indent=2))


@data.command('search', epilog=filter_opts_epilog)
@limit_option(100)
@pretty
@asset_type_perms
@search_request_opts
def quick_search(limit, pretty, sort, **kw):
    '''Execute a quick search.'''
    req = search_req_from_opts(**kw)
    cl = clientv1()
    page_size = min(limit, 250)
    echo_json_response(call_and_wrap(
        cl.quick_search, req, page_size=page_size, sort=sort
    ), pretty, limit)


@data.command('create-search', epilog=filter_opts_epilog)
@pretty
@click.option('--name', required=True)
@asset_type_perms
@search_request_opts
def create_search(pretty, **kw):
    '''Create a saved search'''
    req = search_req_from_opts(**kw)
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.create_search, req), pretty)


@data.command('saved-search')
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


@data.command('searches')
@click.option('--quick', is_flag=True, help='Quick searches')
@click.option('--saved', default=True, is_flag=True,
              help='Saved searches (default)')
def get_searches(quick, saved):
    '''List searches'''
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.get_searches, quick, saved), True)


@pretty
@asset_type_perms
@search_request_opts
@click.option('--interval', default='month',
              type=click.Choice(['hour', 'day', 'month', 'week', 'year']),
              help='Specify the interval to aggregate by.')
@data.command('stats', epilog=filter_opts_epilog)
def stats(pretty, **kw):
    '''Get search stats'''
    req = search_req_from_opts(**kw)
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.stats, req), pretty)


def _disable_item_type(ctx, param, value):
    if value:
        for p in ctx.command.params:
            if p.name == 'item_type':
                p.required = False
    return value


@asset_type_option
@search_request_opts
@click.option('--search-id', is_eager=True, callback=_disable_item_type,
              type=str, help='Use the specified search')
@click.option('--dry-run', is_flag=True, help=(
    'Only report the number of items that would be downloaded.'
))
@click.option('--activate-only', is_flag=True, help=(
    'Only activate the items. Outputs URLS for downloading.'
))
@click.option('--quiet', is_flag=True, help=(
    'Disable ANSI control output'
))
@click.option('--dest', default='.', help=(
    'Location to download files to'), type=click.Path(
        exists=True, resolve_path=True, writable=True, file_okay=False))
@limit_option(None)
@data.command('download', epilog=filter_opts_epilog)
def download(asset_type, dest, limit, sort, search_id, dry_run, activate_only,
             quiet, **kw):
    '''Activate and download'''
    cl = clientv1()
    page_size = min(limit or 250, 250)
    asset_type = list(chain.from_iterable(asset_type))
    # even though we're using functionality from click.Path, this was needed
    # to detect inability to write on Windows in a read-only vagrant mount...
    # @todo check/report upstream
    if not activate_only and not check_writable(dest):
        raise click.ClickException(
            'download destination "%s" is not writable' % dest)
    if search_id:
        if dry_run:
            raise click.ClickException(
                'dry-run not supported with saved search')
        if any(kw[s] for s in kw):
            raise click.ClickException(
                'search options not supported with saved search')
        search, search_arg = cl.saved_search, search_id
    else:
        # any requested asset-types should be used as permission filters
        kw['asset_type'] = [AssetTypePerm.to_permissions(asset_type)]
        req = search_req_from_opts(**kw)
        if dry_run:
            req['interval'] = 'year'
            stats = cl.stats(req).get()
            item_cnt = sum([b['count'] for b in stats['buckets']])
            asset_cnt = item_cnt * len(asset_type)
            click.echo(
                'would download approximately %d assets from %s items' %
                (asset_cnt, item_cnt)
            )
            return
        else:
            search, search_arg = cl.quick_search, req

    dl = downloader.create(cl)
    output = downloader_output(dl, disable_ansi=quiet)
    # delay initial item search until downloader output initialized
    output.start()
    try:
        items = search(search_arg, page_size=page_size, sort=sort)
    except Exception as ex:
        output.cancel()
        click_exception(ex)
    func = dl.activate if activate_only else dl.download
    args = [items.items_iter(limit), asset_type]
    if not activate_only:
        args.append(dest)
    # invoke the function within an interrupt handler that will shut everything
    # down properly
    handle_interrupt(dl.shutdown, func, *args)
