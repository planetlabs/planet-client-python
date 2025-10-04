# Copyright 2025 Planet Labs PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from contextlib import asynccontextmanager
import json
import click
from click.exceptions import ClickException

from planet.cli.io import echo_json
from planet.clients.analytics import AnalyticsClient

from .cmds import command
from .options import limit
from .session import CliSession


@asynccontextmanager
async def analytics_client(ctx):
    async with CliSession() as sess:
        cl = AnalyticsClient(sess, base_url=ctx.obj['BASE_URL'])
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Analytics API URL.')
def analytics(ctx, base_url):
    """Commands for interacting with the Analytics API"""
    ctx.obj['BASE_URL'] = base_url


@analytics.group()  # type: ignore
def feeds():
    """Commands for interacting with Analytics feeds"""
    pass


@command(feeds, name="list")
@limit
async def feeds_list(ctx, limit, pretty):
    """List available analytics feeds.

    Example:

    \b
    planet analytics feeds list
    planet analytics feeds list --limit 10
    """
    async with analytics_client(ctx) as cl:
        feeds_iter = cl.list_feeds(limit=limit)
        async for feed in feeds_iter:
            echo_json(feed, pretty)


@command(feeds, name="get")
@click.argument('feed_id', required=True)
async def feeds_get(ctx, feed_id, pretty):
    """Get details of a specific analytics feed.

    Parameters:
        FEED_ID: The ID of the analytics feed

    Example:

    \b
    planet analytics feeds get my-feed-id
    """
    async with analytics_client(ctx) as cl:
        feed = await cl.get_feed(feed_id)
        echo_json(feed, pretty)


@command(feeds, name="stats")
@click.argument('feed_id', required=True)
@click.option('--subscription-id',
              help='Get stats for a specific subscription.')
@click.option('--start-time',
              help='Start time for temporal filtering (ISO 8601 format).')
@click.option('--end-time',
              help='End time for temporal filtering (ISO 8601 format).')
async def feeds_stats(ctx,
                      feed_id,
                      subscription_id,
                      start_time,
                      end_time,
                      pretty):
    """Get statistics for an analytics feed.

    Parameters:
        FEED_ID: The ID of the analytics feed

    Example:

    \b
    planet analytics feeds stats my-feed-id
    planet analytics feeds stats my-feed-id --start-time 2023-01-01T00:00:00Z
    """
    async with analytics_client(ctx) as cl:
        stats = await cl.get_feed_stats(feed_id=feed_id,
                                        subscription_id=subscription_id,
                                        start_time=start_time,
                                        end_time=end_time)
        echo_json(stats, pretty)


@analytics.group()  # type: ignore
def subscriptions():
    """Commands for interacting with Analytics subscriptions"""
    pass


@command(subscriptions, name="list")
@click.option('--feed-id', help='Filter subscriptions by feed ID.')
@limit
async def subscriptions_list(ctx, feed_id, limit, pretty):
    """List analytics subscriptions.

    Example:

    \b
    planet analytics subscriptions list
    planet analytics subscriptions list --feed-id my-feed-id
    """
    async with analytics_client(ctx) as cl:
        subs_iter = cl.list_subscriptions(feed_id=feed_id, limit=limit)
        async for subscription in subs_iter:
            echo_json(subscription, pretty)


@command(subscriptions, name="get")
@click.argument('subscription_id', required=True)
async def subscriptions_get(ctx, subscription_id, pretty):
    """Get details of a specific analytics subscription.

    Parameters:
        SUBSCRIPTION_ID: The ID of the analytics subscription

    Example:

    \b
    planet analytics subscriptions get my-subscription-id
    """
    async with analytics_client(ctx) as cl:
        subscription = await cl.get_subscription(subscription_id)
        echo_json(subscription, pretty)


@analytics.group()  # type: ignore
def results():
    """Commands for interacting with Analytics results"""
    pass


@command(results, name="search")
@click.argument('feed_id', required=True)
@click.option('--subscription-id', help='Filter results by subscription ID.')
@click.option('--start-time',
              help='Start time for temporal filtering (ISO 8601 format).')
@click.option('--end-time',
              help='End time for temporal filtering (ISO 8601 format).')
@click.option('--bbox', help='Bounding box as west,south,east,north.')
@click.option('--geometry', help='GeoJSON geometry for spatial filtering.')
@limit
async def results_search(ctx,
                         feed_id,
                         subscription_id,
                         start_time,
                         end_time,
                         bbox,
                         geometry,
                         limit,
                         pretty):
    """Search for analytics results.

    Parameters:
        FEED_ID: The ID of the analytics feed to search

    Example:

    \b
    planet analytics results search my-feed-id
    planet analytics results search my-feed-id --start-time 2023-01-01T00:00:00Z
    planet analytics results search my-feed-id --bbox -122.5,37.7,-122.3,37.8
    """
    # Parse bbox if provided
    bbox_list = None
    if bbox:
        try:
            bbox_list = [float(x.strip()) for x in bbox.split(',')]
            if len(bbox_list) != 4:
                raise ValueError("bbox must contain exactly 4 values")
        except (ValueError, TypeError) as e:
            raise ClickException(f"Invalid bbox format: {e}")

    # Parse geometry if provided
    geometry_dict = None
    if geometry:
        try:
            geometry_dict = json.loads(geometry)
        except json.JSONDecodeError as e:
            raise ClickException(f"Invalid geometry JSON: {e}")

    async with analytics_client(ctx) as cl:
        results_iter = cl.search_results(feed_id=feed_id,
                                         subscription_id=subscription_id,
                                         start_time=start_time,
                                         end_time=end_time,
                                         bbox=bbox_list,
                                         geometry=geometry_dict,
                                         limit=limit)
        async for result in results_iter:
            echo_json(result, pretty)


@command(results, name="get")
@click.argument('result_id', required=True)
async def results_get(ctx, result_id, pretty):
    """Get details of a specific analytics result.

    Parameters:
        RESULT_ID: The ID of the analytics result

    Example:

    \b
    planet analytics results get my-result-id
    """
    async with analytics_client(ctx) as cl:
        result = await cl.get_result(result_id)
        echo_json(result, pretty)


@command(results, name="download")
@click.argument('result_id', required=True)
@click.option('--format',
              default='json',
              type=click.Choice(['json', 'geojson', 'csv']),
              help='Download format (default: json).')
async def results_download(ctx, result_id, format, pretty):
    """Download analytics result data.

    Parameters:
        RESULT_ID: The ID of the analytics result

    Example:

    \b
    planet analytics results download my-result-id
    planet analytics results download my-result-id --format geojson
    """
    async with analytics_client(ctx) as cl:
        data = await cl.download_result(result_id, format)

        if format.lower() in ['json', 'geojson']:
            echo_json(data, pretty)
        else:
            # For CSV or other text formats
            click.echo(data)
