# Copyright 2015 Planet Labs, Inc.
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

from os import path
import sys
import time
import json
import logging
import re
import warnings

import click

import planet
from planet.api.sync import _SyncTool
from planet import api
from planet.api.utils import complete

from requests.packages.urllib3 import exceptions as urllib3exc

client_params = {}

ORTHO_PRODUCTS = ['visual', 'analytic', 'unrectified']


def client():
    return api.Client(**client_params)


pretty = click.option('-pp/-r', '--pretty/--no-pretty', default=None,
                      is_flag=True, help='Format JSON output')
scene_type = click.option('-s', '--scene-type', default='ortho',
                          help='Type of scene',
                          type=click.Choice(['ortho', 'landsat']))
dest_dir = click.option('-d', '--dest', help='Destination directory',
                        type=click.Path(file_okay=False, resolve_path=True,
                                        exists=True))
workspace = click.option('--workspace', help='Workspace ID', type=int)


def limit_option(default):
    return click.option('--limit', type=click.INT, required=False,
                        default=default, help="Limit the number of items.")


# monkey patch warnings module to hide InsecurePlatformWarning - the warning
# notes 'may cause certain SSL connections to fail' so it doesn't seem to
# introduce any vulnerabilities
# we capture the warning if present and present this if any SSLError is caught
# just in case this configuration is an issue
_insecure_warning = []
showwarning = warnings.showwarning


def hack(message, category, filename, lineno):
    if category is urllib3exc.InsecurePlatformWarning:
        if len(_insecure_warning) == 0:
            _insecure_warning.append(message)
        return
    showwarning(message, category, filename, lineno)
warnings.showwarning = hack


def configure_logging(verbosity):
    '''configure logging via verbosity level of between 0 and 2 corresponding
    to log levels warning, info and debug respectfully.'''
    log_level = max(logging.DEBUG, logging.WARNING - logging.DEBUG*verbosity)
    logging.basicConfig(stream=sys.stderr, level=log_level)


def click_exception(ex):
    if type(ex) is api.exceptions.APIException:
        raise click.ClickException('Unexpected response: %s' % str(ex))
    msg = "%s: %s" % (type(ex).__name__, str(ex))
    raise click.ClickException(msg)


def call_and_wrap(func, *args, **kw):
    '''call the provided function and wrap any API exception with a click
    exception. this means no stack trace is visible to the user but instead
    a (hopefully) nice message is provided.
    note: could be a decorator but didn't play well with click
    '''
    try:
        return func(*args, **kw)
    except api.exceptions.APIException as ex:
        click_exception(ex)
    except urllib3exc.SSLError:
        # see monkey patch above re InsecurePlatformWarning
        if _insecure_warning:
            click.echo(click.style(str(_insecure_warning[0]), fg='red'))
        raise


def check_futures(futures):
    for f in futures:
        try:
            f.await()
        except api.InvalidAPIKey as invalid:
            click_exception(invalid)
        except api.APIException as other:
            click.echo('WARNING %s' % other.message)
        except api.RequestCancelled:
            pass


def summarize_throughput(bytes, start_time):
    elapsed = time.time() - start_time
    mb = float(bytes) / (1024 * 1024)
    click.echo('transferred %s bytes in %.2f seconds (%.2f MB/s)' %
               (bytes, elapsed, mb/elapsed))


def total_bytes(responses):
    return sum([len(r.get_body()) for r in responses])


def echo_json_response(response, pretty, limit=None):
    '''Wrapper to echo JSON with optional 'pretty' printing. If pretty is not
    provided explicity and stdout is a terminal (and not redirected or piped),
    the default will be to indent and sort keys'''
    indent = None
    sort_keys = False
    if pretty or (pretty is None and sys.stdout.isatty()):
        indent = 2
        sort_keys = True
    try:
        if hasattr(response, 'json_encode'):
            response.json_encode(click.get_text_stream('stdout'), limit=limit,
                                 indent=indent, sort_keys=sort_keys)
        else:
            res = response.get_raw()
            res = json.dumps(json.loads(res), indent=2, sort_keys=True)
            click.echo(res)
    except IOError as ioe:
        # hide scary looking broken pipe stack traces
        raise click.ClickException(str(ioe))


def read(value, split=False):
    '''Get the value of an option interpreting as a file implicitly or
    explicitly and falling back to the value if not explicitly specified.
    If the value is '@name', then a file must exist with name and the returned
    value will be the contents of that file. If the value is '@-' or '-', then
    stdin will be read and returned as the value. Finally, if a file exists
    with the provided value, that file will be read. Otherwise, the value
    will be returned.
    '''
    v = str(value)
    retval = value
    if v[0] == '@' or v == '-':
        fname = '-' if v == '-' else v[1:]
        try:
            with click.open_file(fname) as fp:
                if not fp.isatty():
                    retval = fp.read()
                else:
                    retval = None
        except IOError as ioe:
            # if explicit and problems, raise
            if v[0] == '@':
                raise click.ClickException(str(ioe))
    elif path.exists(v) and path.isfile(v):
        with click.open_file(v) as fp:
            retval = fp.read()
    if retval and split and type(retval) != tuple:
        retval = _split(retval.strip())
    return retval


def read_aoi(value):
    '''See if the provided AOI looks like a WKT or GeoJSON and if so, return
    as text or a parsed dict. If the value resolves to nothing, return None.
    Otherwise raise ClickException if the provided value is not either.
    '''
    aoi = None
    raw = read(value)
    if raw:
        if api.utils.probably_wkt(raw):
            aoi = raw
        else:
            aoi = api.utils.probably_geojson(raw)
        if aoi is None:
            raise click.ClickException('The provided AOI does not look like '
                                       'WKT or GeoJSON')
    return aoi


def _split(value):
    '''return input split on any whitespace'''
    return re.split('\s+', value)


@click.group()
@click.option('-w', '--workers', default=4,
              help=('The number of concurrent downloads when requesting '
                    'multiple scenes.'))
@click.option('-v', '--verbose', count=True, help='Specify verbosity')
@click.option('-k', '--api-key',
              help='Valid API key - or via env variable %s' % api.auth.ENV_KEY)
@click.option('-u', '--base-url', help='Optional for testing')
@click.version_option(version=planet.__version__, message='%(version)s')
def cli(verbose, api_key, base_url, workers):
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
@click.option('--email', default=None, prompt=True)
@click.option('--password', default=None, prompt=True, hide_input=True)
def init(email, password):
    '''Login using email/password'''
    response = call_and_wrap(client().login, email, password)
    planet.api.utils.write_planet_json({'key': response['api_key']})
    click.echo('initialized')


@pretty
@scene_type
@workspace
@cli.command('search')
@click.argument('aoi', default='@-', required=False)
@limit_option(1000)
@click.option('--where', nargs=3, multiple=True,
              help=('Provide additional search criteria. See '
                    'https://www.planet.com/docs/v0/scenes/#metadata for '
                    'search metadata fields.'))
def get_scenes_list(scene_type, pretty, aoi, limit, where, workspace):
    '''Get a list of scenes.'''

    aoi = read_aoi(aoi)
    conditions = {'workspace': workspace}

    if where:
        conditions.update([
            ("%s.%s" % condition[0:2], condition[2])
            for condition in where
        ])

    echo_json_response(call_and_wrap(
        client().get_scenes_list,
        scene_type=scene_type, intersects=aoi, count=limit,
        **conditions), pretty, limit=limit)


@pretty
@scene_type
@click.argument('scene_id', nargs=1)
@cli.command('metadata')
def metadata(scene_id, scene_type, pretty):
    '''Get scene metadata'''

    echo_json_response(call_and_wrap(client().get_scene_metadata,
                       scene_id, scene_type), pretty)


@scene_type
@dest_dir
@click.argument('scene_ids', nargs=-1)
@click.option('--product',
              type=click.Choice(
                  ["band_%d" % i for i in range(1, 12)] +
                  ORTHO_PRODUCTS + ['qa']
              ), default='visual')
@cli.command('download')
def fetch_scene_geotiff(scene_ids, scene_type, product, dest):
    """
    Download full scene image(s).
    """
    scene_ids = read(scene_ids or '@-', split=True)
    if not scene_ids:
        return

    start_time = time.time()
    cl = client()
    futures = cl.fetch_scene_geotiffs(scene_ids, scene_type, product,
                                      api.utils.write_to_file(dest))
    complete(futures, check_futures, cl)
    summarize_throughput(total_bytes(futures), start_time)


@scene_type
@dest_dir
@click.argument("scene-ids", nargs=-1)
@click.option('--size', type=click.Choice(['sm', 'md', 'lg']), default='md',
              help='Thumbnail size')
@click.option('--format', 'fmt', type=click.Choice(['png', 'jpg', 'jpeg']),
              default='png', help='Thumbnail format')
@cli.command('thumbnails')
def fetch_scene_thumbnails(scene_ids, scene_type, size, fmt, dest):
    '''Fetch scene thumbnail(s)'''

    scene_ids = read(scene_ids or '@-', split=True)
    if not scene_ids:
        return

    cl = client()
    futures = cl.fetch_scene_thumbnails(scene_ids, scene_type, size, fmt,
                                        api.write_to_file(dest))
    complete(futures, check_futures, cl)


@scene_type
@workspace
@click.argument("destination")
@limit_option(default=-1)
@click.option("--dryrun", is_flag=True, help='Do not actually download')
@click.option("--products", multiple=True,
              type=click.Choice(ORTHO_PRODUCTS + ['all']),
              help='Specifiy products to download, default is visual')
@cli.command('sync')
def sync(destination, workspace, scene_type, limit, dryrun, products):
    '''Synchronize a directory to a specified AOI or workspace'''
    aoi = None
    filters = {'workspace': workspace}

    if 'all' in products:
        products = ORTHO_PRODUCTS
    else:
        products = products or ('visual',)

    sync_tool = _SyncTool(client(), destination, aoi,
                          scene_type, products, **filters)

    try:
        to_fetch = sync_tool.init(limit)
    except ValueError as ve:
        raise click.ClickException(str(ve))
    click.echo('total scene products to fetch: %s' % to_fetch)
    if limit > -1:
        click.echo('limiting to %s' % limit)

    if dryrun:
        click.echo('would download:')
        for scene in sync_tool.get_scenes_to_sync():
            click.echo(scene['id'])
        return

    def progress_callback(name, remaining):
        click.echo('downloaded %s, remaining %s' %
                   (name, remaining))

    start_time = time.time()

    summary = sync_tool.sync(progress_callback)

    if summary.transferred:
        summarize_throughput(summary.transferred, start_time)


@pretty
@limit_option(default=50)
@cli.command('mosaics')
def list_mosaics(limit, pretty):
    """
    List all mosaics
    """
    echo_json_response(call_and_wrap(client().list_mosaics), pretty, limit)


@pretty
@cli.command('mosaic')
@click.argument('mosaic_name', nargs=1)
def get_mosaic(mosaic_name, pretty):
    """
    Describe a specified mosaic
    """
    echo_json_response(call_and_wrap(client().get_mosaic, mosaic_name), pretty)


@pretty
@cli.command('mosaic-quads')
@click.argument('mosaic_name', nargs=1)
@click.argument('aoi', default='@-', required=False)
@limit_option(default=100)
def get_mosaic_quads(mosaic_name, aoi, limit, pretty):
    """
    Get quad info for the specified mosaic
    """
    aoi = read_aoi(aoi)

    if aoi:
        # work around backend limitation of using a FeatureCollection
        aoi = api.utils.geometry_from_json(aoi)

    echo_json_response(
        call_and_wrap(client().get_mosaic_quads,
                      mosaic_name, intersects=aoi), pretty, limit)


@cli.command('download-quads')
@dest_dir
@click.argument('mosaic_name', nargs=1)
@click.argument('quad_ids', nargs=-1)
def download_quads(mosaic_name, quad_ids, dest):
    """
    Download quad geotiffs
    """
    quad_ids = read(quad_ids, split=True)
    cl = client()
    futures = call_and_wrap(cl.fetch_mosaic_quad_geotiffs, mosaic_name,
                            quad_ids, api.write_to_file(dest))
    complete(futures, check_futures, cl)


@pretty
@cli.command('list-workspaces')
def list_workspaces(pretty):
    """
    List workspaces.
    """
    echo_json_response(call_and_wrap(client().get_workspaces), pretty)


@pretty
@cli.command('get-workspace')
@click.argument('id', nargs=1)
def get_workspace(pretty, id):
    """
    Get workspace.
    """
    echo_json_response(call_and_wrap(client().get_workspace, id), pretty)


@cli.command('set-workspace')
@click.argument("workspace", default="@-", required=False)
@click.option('--id', help='If provided, update the workspace with this id')
@click.option('--aoi', help='The geometry to use')
@click.option('--name', help='Workspace name')
@click.option('--create', is_flag=True, help='Specify workspace creation')
@click.option('--where', nargs=3, multiple=True,
              help=('Provide additional search criteria. See '
                    'https://www.planet.com/docs/v0/scenes/#metadata for '
                    'search metadata fields.'))
def set_workspace(id, aoi, name, create, workspace, where):
    '''Create or modify a workspace'''
    workspace = read(workspace)
    try:
        workspace = json.loads(workspace) if workspace else None
    except ValueError:
        raise click.ClickException('workspace must be JSON')

    cl = client()

    if workspace is None and id:
        workspace = cl.get_workspace(id).get()

    # what workspace id are we working with
    if not id:
        id = workspace.get('id', None)
    if create:
        id = None

    aoi = read_aoi(aoi)
    if aoi:
        geom = api.utils.geometry_from_json(aoi)
        if geom is None:
            raise click.ClickException('unable to find geometry in aoi')
        workspace['filters'] = {
            'geometry': {
                'intersects': geom
            }
        }
    if name:
        workspace['name'] = name

    if where:
        if 'filters' not in workspace:
            workspace['filters'] = {}
        filters = workspace['filters']
        for k, c, v in where:
            if k not in filters:
                filters[k] = {}
            group = filters.get(k)
            if v == '-' and c in group:
                group.pop(c)
            else:
                group[c] = v
            if not group:
                filters.pop(k)

    if not workspace:
        raise click.ClickException('nothing to do')
    echo_json_response(call_and_wrap(cl.set_workspace,
                       workspace, id), pretty)
