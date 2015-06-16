import click
import json
import logging
from planet import api
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
@click.option('-w', '--workers', default=4)
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
def list_all_scene_types():
    '''List all scene types.'''
    click.echo(call_and_wrap(client.list_all_scene_types).get_raw())


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


@pretty
@scene_type
@click.argument('id', nargs=1)
@cli.command('metadata')
def fetch_scene_info(id, scene_type, pretty):
    '''Fetch scene metadata'''
    res = call_and_wrap(client.fetch_scene_info, id, scene_type).get_raw()
    if pretty:
        res = json.dumps(json.loads(res), indent=2)
    click.echo(res)


@pretty
@scene_type
@cli.command('search')
@click.argument("aoi", default="-", required=False)
@click.option('--count', type=click.INT, required=False, help="Set the number of returned scenes.")
@click.option("--where", nargs=3, multiple=True, default={}, help="Provide additional search criteria. See https://www.planet.com/docs/v0/scenes/#metadata for search metadata fields.")
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
