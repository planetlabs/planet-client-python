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
    clientv1,
    analytics_client_v1
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
    BoundingBox,
    metavar_docs,
    DateInterval
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
from planet.api.utils import write_to_file


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


@cli.group('mosaics')
def mosaics():
    '''Commands for interacting with the Mosaics API'''
    pass


@mosaics.command('list')
@pretty
def list_mosaics(pretty):
    '''List information for all available mosaics'''
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.get_mosaics), pretty)


@mosaics.command('search')
@click.argument('name')
@click.option('--bbox', type=BoundingBox(), help=(
    'Region to query as a comma-delimited string:'
    ' lon_min,lat_min,lon_max,lat_max'
))
@click.option('--rbox', type=BoundingBox(), help='Alias for --bbox')
@limit_option(None)
@pretty
def search_mosaics(name, bbox, rbox, limit, pretty):
    '''Get quad IDs and information for a mosaic'''
    bbox = bbox or rbox
    cl = clientv1()
    mosaic, = cl.get_mosaic_by_name(name).items_iter(1)
    response = call_and_wrap(cl.get_quads, mosaic, bbox)
    echo_json_response(response, pretty, limit)


@mosaics.command('info')
@click.argument('name')
@pretty
def mosaic_info(name, pretty):
    '''Get information for a specific mosaic'''
    cl = clientv1()
    echo_json_response(call_and_wrap(cl.get_mosaic_by_name, name), pretty)


@mosaics.command('quad-info')
@click.argument('name')
@click.argument('quad')
@pretty
def quad_info(name, quad, pretty):
    '''Get information for a specific mosaic quad'''
    cl = clientv1()
    mosaic, = cl.get_mosaic_by_name(name).items_iter(1)
    echo_json_response(call_and_wrap(cl.get_quad_by_id, mosaic, quad), pretty)


@mosaics.command('contribution')
@click.argument('name')
@click.argument('quad')
@pretty
def quad_contributions(name, quad, pretty):
    '''Get contributing scenes for a mosaic quad'''
    cl = clientv1()
    mosaic, = cl.get_mosaic_by_name(name).items_iter(1)
    quad = cl.get_quad_by_id(mosaic, quad).get()
    response = call_and_wrap(cl.get_quad_contributions, quad)
    echo_json_response(response, pretty)


@mosaics.command('download')
@click.argument('name')
@click.option('--bbox', type=BoundingBox(), help=(
    'Region to download as a comma-delimited string:'
    ' lon_min,lat_min,lon_max,lat_max'
))
@click.option('--rbox', type=BoundingBox(), help='Alias for --bbox')
@click.option('--quiet', is_flag=True, help=(
    'Disable ANSI control output'
))
@click.option('--dest', default='.', help=(
    'Location to download files to'), type=click.Path(
     exists=True, resolve_path=True, writable=True, file_okay=False
))
@limit_option(None)
def download_quads(name, bbox, rbox, quiet, dest, limit):
    '''Download quads from a mosaic'''
    bbox = bbox or rbox
    cl = clientv1()

    dl = downloader.create(cl, mosaic=True)
    output = downloader_output(dl, disable_ansi=quiet)
    output.start()
    try:
        mosaic, = cl.get_mosaic_by_name(name).items_iter(1)
        items = cl.get_quads(mosaic, bbox).items_iter(limit)
    except Exception as ex:
        output.cancel()
        click_exception(ex)
    # invoke the function within an interrupt handler that will shut everything
    # down properly
    handle_interrupt(dl.shutdown, dl.download, items, [], dest)


@cli.group('analytics')
def analytics():
    '''Commands for interacting with the Analytics Feed API'''
    pass


@analytics.command('check_connection')
@pretty
def health(pretty):
    '''
    Check that we can connect to the API
    :param pretty:
    :return:
    '''
    cl = analytics_client_v1()
    click.echo('Using base URL: {}'.format(cl.base_url))
    response = cl.check_analytics_connection()
    echo_json_response(response, pretty)


@analytics.group('subscriptions')
def subscriptions():
    '''Commands for interacting with the Analytics Feed API for subscriptions'''
    pass


@subscriptions.command('list')
@click.option('--feed-id', type=str)
@limit_option(250)  # Analytics API default
@click.option('--before', type=str, help=
              'When paginating, provide the identifier for last subscription on previous page.'
              )
@pretty
def list_subscriptions(pretty, limit, feed_id, before):
    '''List all subscriptions user has access to.'''
    cl = analytics_client_v1()
    response = cl.list_analytic_subsriptions(feed_id, limit, before)
    echo_json_response(response, pretty)


@subscriptions.command('describe')
@click.argument('subscription_id')
@pretty
def get_subscription_info(subscription_id, pretty):
    '''Get metadata for specific subscription.'''
    cl = analytics_client_v1()
    sub_info = cl.get_subscription_info(subscription_id)
    echo_json_response(sub_info, pretty)


@analytics.group('features')
def features():
    '''Commands for interacting with the Analytics Feed API for features'''
    pass


@features.command('list')
@click.argument('subscription_id')
@limit_option(250)  # Analytics API default
@click.option('--bbox', type=BoundingBox(), help=(
    'Region to query as a comma-delimited string:'
    ' lon_min,lat_min,lon_max,lat_max'
))
@click.option('--rbox', type=BoundingBox(), help='Alias for --bbox')
@click.option('--time-range', type=DateInterval(), help=(
        'Time interval. Can be open or closed interval, start times are inclusive and end times are exclusive:'
        '2019-01-01T00:00:00.00Z/2019-02-01T00:00:00.00Z (Closed interval for January 2019),'
        '2019-01-01T00:00:00.00Z/.. (Open interval for all items since the start of January 2019),'
        '2019-01-01T00:00:00.00Z (instant)'
))
@click.option('--before', type=str, help='Get features published before the item with the provided ID.')
@click.option('--after', type=str, help='Get features published after the item with the provided ID.')
@pretty
def list_features(subscription_id, pretty, limit, rbox, bbox, time_range, before, after):
    '''Request feature list for a particular subscription.'''
    cl = analytics_client_v1()
    bbox = bbox or rbox
    features = cl.list_analytic_subscription_features(subscription_id, limit, bbox, time_range, before, after)
    echo_json_response(features, pretty)


@features.command('get')
@click.argument('resource_type', type=click.Choice(['source-image-info', 'target-quad', 'source-quad']))
@click.argument('subscription_id')
@click.argument('feature_id')
@click.option('--dest', default='.', help=(
    'Location to download files to'), type=click.Path(
     exists=True, resolve_path=True, writable=True, file_okay=False
))
@pretty
def get_associated_resource(subscription_id, feature_id, resource_type, pretty, dest):
    '''Request resources associated with a particular subscription/feature combination.'''
    cl = analytics_client_v1()
    if resource_type in ['target-quad', 'source-quad']:
        click.echo('Requesting {} for {}/{} selected destination directory is: {}'.format(resource_type, subscription_id, feature_id, dest))

    resource = cl.get_associated_resource_for_analytic_feature(subscription_id, feature_id, resource_type)

    if resource_type == 'source-image-info':
        echo_json_response(resource, pretty)

    if resource_type in ['target-quad', 'source-quad']:
        writer = write_to_file(dest, None)
        writer(resource)
        click.echo('{} written, available at: {}/{}'.format(resource_type, dest, resource.name))
