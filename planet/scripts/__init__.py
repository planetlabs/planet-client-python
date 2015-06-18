'''
Copyright 2015 Planet Labs, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0
   
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
import click
import json
import logging
from planet import api
from os import path
import sys

client = api.Client()

pretty = click.option('-pp', '--pretty', default=False, is_flag=True)
scene_type = click.option('-s', '--scene-type', default='ortho')
dest_dir = click.option('-d', '--dest', help='Destination directory',
                        type=click.Path(file_okay=False, resolve_path=True))


def configure_logging(verbosity):
    '''configure logging via verbosity level of between 0 and 2 corresponding
    to log levels warning, info and debug respectfully.'''
    log_level = max(logging.DEBUG, logging.WARNING - logging.DEBUG*verbosity)
    logging.basicConfig(stream=sys.stderr, level=log_level)


def click_exception(ex):
    if type(ex) is api.APIException:
        raise click.ClickException('Unexpected response: %s' % ex.message)
    msg = "%s: %s" % (type(ex).__name__, ex.message)
    raise click.ClickException(msg)


def call_and_wrap(func, *args, **kw):
    '''call the provided function and wrap any API exception with a click
    exception. this means no stack trace is visible to the user but instead
    a (hopefully) nice message is provided.
    note: could be a decorator but didn't play well with click
    '''
    try:
        return func(*args, **kw)
    except api.APIException, ex:
        click_exception(ex)


def check_futures(futures):
    for f in futures:
        try:
            f.result()
        except api.InvalidAPIKey, invalid:
            click_exception(invalid)
        except api.APIException, other:
            click.echo('WARNING %s' % other.message)


@click.group()
@click.option('-w', '--workers', default=4, help='The number of concurrent downloads when requesting multiple scenes.')
@click.option('-v', '--verbose', count=True)
@click.option('-k', '--api-key',
              help='Valid API key - or via env variable %s' % api.ENV_KEY)
@click.option('-u', '--base-url', help='Optional for testing')
def cli(verbose, api_key, base_url, workers):
    configure_logging(verbose)
    '''Planet API Client'''
    if api_key:
        client.api_key = api_key
    if base_url:
        client.base_url = base_url
    client._workers = workers


@cli.command('list-scene-types')
def list_scene_types():
    '''List all scene types.'''
    click.echo(call_and_wrap(client.list_scene_types).get_raw())


@pretty
@scene_type
@cli.command('search')
@click.argument("aoi", default="-", required=False)
@click.option('--count', type=click.INT, required=False, help="Set the number of returned scenes.")
@click.option("--where", nargs=3, multiple=True, help="Provide additional search criteria. See https://www.planet.com/docs/v0/scenes/#metadata for search metadata fields.")
def get_scenes_list(scene_type, pretty, aoi, count, where):
    '''Get a list of scenes'''

    if aoi == "-":
        src = click.open_file('-')
        if not src.isatty():
            lines = src.readlines()
            aoi = ''.join([line.strip() for line in lines])
        else:
            aoi = None

    if where:
        conditions = {
            "%s.%s" % condition[0:2]: condition[2]
            for condition in where
        }
    else:
        conditions = {}

    res = call_and_wrap(client.get_scenes_list, scene_type=scene_type,
                        intersects=aoi, count=count, **conditions).get_raw()
    if pretty:
        res = json.dumps(json.loads(res), indent=2)
    click.echo(res)


@pretty
@scene_type
@click.argument('scene_id', nargs=1)
@cli.command('metadata')
def metadata(scene_id, scene_type, pretty):
    '''Get scene metadata'''

    res = call_and_wrap(client.get_scene_metadata, scene_id, scene_type).get_raw()

    if pretty:
        res = json.dumps(json.loads(res), indent=2)

    click.echo(res)


@scene_type
@dest_dir
@click.argument('scene_ids', nargs=-1)
@click.option('--product',
              type=click.Choice(
                  ["band_%d" % i for i in range(1, 12)] +
                  ['visual', 'analytic', 'qa']
              ), default='visual')
@cli.command('download')
@click.pass_context
def fetch_scene_geotiff(ctx, scene_ids, scene_type, product, dest):
    '''Fetch full scene image(s)'''

    if len(scene_ids) == 0:
        src = click.open_file('-')
        if not src.isatty():
            scene_ids = map(lambda s: s.strip(), src.readlines())
        else:
            click.echo(ctx.get_usage())

    futures = client.fetch_scene_geotiffs(scene_ids, scene_type, product,
                                          api.write_to_file(dest))
    check_futures(futures)


@scene_type
@dest_dir
@click.argument("scene-ids", nargs=-1)
@click.option('--size', type=click.Choice(['sm', 'md', 'lg']), default='md')
@click.option('--format', 'fmt', type=click.Choice(['png', 'jpg', 'jpeg']),
              default='png')
@cli.command('thumbnails')
def fetch_scene_thumbnails(scene_ids, scene_type, size, fmt, dest):
    '''Fetch scene thumbnail(s)'''

    if len(scene_ids) == 0:
        src = click.open_file('-')
        if not src.isatty():
            scene_ids = map(lambda s: s.strip(), src.readlines())

    futures = client.fetch_scene_thumbnails(scene_ids, scene_type, size, fmt,
                                            api.write_to_file(dest))
    check_futures(futures)


@scene_type
@click.argument("destination")
@click.option("--limit", default=-1, help='limit scene syncing')
@cli.command('sync')
def sync(destination, scene_type, limit):
    '''Synchronize a directory to a specified AOI'''
    if not path.exists(destination) or not path.isdir(destination):
        raise click.ClickException('destination must exist and be a directory')
    aoi_file = path.join(destination, 'aoi.geojson')
    if not path.exists(aoi_file):
        raise click.ClickException(
            'provide an aoi.geojson file in "%s"' % destination
        )
    aoi = None
    with open(aoi_file) as fp:
        aoi = fp.read()
    sync_file = path.join(destination, 'sync.json')
    if path.exists(sync_file):
        with open(sync_file) as fp:
            sync = json.loads(fp.read())
    else:
        sync = {}
    filters = {}
    if 'latest' in sync:
        filters['acquired.gt'] = sync['latest']
    res = call_and_wrap(client.get_scenes_list, scene_type=scene_type,
                        intersects=aoi, count=100, order_by='acquired asc',
                        **filters)
    click.echo('total scenes to fetch: %s' % res.get()['count'])
    if limit > 0:
        click.echo('limiting to %s' % limit)
    counter = type('counter', (object,),
        {'remaining': res.get()['count'] if limit < 1 else limit})()
    latest = None
    def progress_callback(arg):
        if not isinstance(arg, int):
            counter.remaining -= 1
            click.echo('downloaded %s, remaining %s' %
                       (arg.name, counter.remaining))
    write_callback = api.write_to_file(destination, progress_callback)
    for page in res.iter():
        features = page.get()['features'][:counter.remaining]
        if not features: break
        ids = [f['id'] for f in features]
        futures = client.fetch_scene_thumbnails(
            ids, scene_type, callback=write_callback
        )
        for f in features:
            metadata = path.join(destination, '%s_metadata.json' % f['id'])
            with open(metadata, 'wb') as fp:
                fp.write(json.dumps(f, indent=2))
        check_futures(futures)
        recent = max([
            api.strp_timestamp(f['properties']['acquired']) for f in features]
        )
        latest = max(latest, recent) if latest else recent
        if counter.remaining <= 0:
            break
    if latest:
        sync['latest'] = api.strf_timestamp(latest)
        with open(sync_file, 'wb') as fp:
            fp.write(json.dumps(sync, indent=2))
