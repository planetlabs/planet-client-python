# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Quota API CLI"""
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import json

import click

import planet
from planet import QuotaClient
from . import types
from .cmds import coro, translate_exceptions
from ..order_request import sentinel_hub
from .io import echo_json
from .options import limit, pretty
from .session import CliSession

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def quota_client(ctx):
    base_url = ctx.obj['BASE_URL']
    async with CliSession() as sess:
        cl = QuotaClient(sess, base_url=base_url)
        yield cl


@click.group()  # type: ignore
@click.pass_context
@click.option('-u',
              '--base-url',
              default=None,
              help='Assign custom base Quota API URL.')
def quota(ctx, base_url):
    """Commands for interacting with the Quota API"""
    ctx.ensure_object(dict)
    ctx.obj['BASE_URL'] = base_url


@quota.command()
@click.pass_context
@click.option('--organization-id', type=int, help='Organization ID')
@click.option('--quota-style', type=str, help='Quota style')
@click.option('--limit', type=int, help='Limit the number of results')
@click.option('--offset', type=int, help='Offset for pagination')
@click.option('--fields', type=str, help='Comma separated list of fields to use')
@click.option('--filters', type=str, help='Filters to apply')
@coro
async def get_my_products(ctx, organization_id, quota_style, limit, offset, fields, filters):
    """Get my products"""
    async with quota_client(ctx) as client:
        products = await client.get_my_products(
            organization_id=organization_id,
            quota_style=quota_style,
            limit=limit,
            offset=offset,
            fields=fields,
            filters=json.loads(filters) if filters else None
        )
        echo_json(products)


@quota.command()
@click.pass_context
@click.argument('aoi_refs', nargs=-1)
@click.argument('product_id', type=int)
@click.argument('collection_id', type=str)
@coro
async def estimate_reservation(ctx, aoi_refs, product_id, collection_id):
    """Estimate a reservation"""
    async with quota_client(ctx) as client:
        estimate_payload = {
            "aoi_refs": list(aoi_refs),
            "product_id": product_id,
            "collection_id": collection_id
        }
        estimate = await client.estimate_reservation(estimate_payload)
        echo_json(estimate)


@quota.command()
@click.pass_context
@click.argument('aoi_refs', nargs=-1)
@click.argument('product_id', type=int)
@click.argument('collection_id', type=str)
@coro
async def create_reservation(ctx, aoi_refs, product_id, collection_id):
    """Create a reservation"""
    async with quota_client(ctx) as client:
        create_payload = {
            "aoi_refs": list(aoi_refs),
            "product_id": product_id,
            "collection_id": collection_id
        }
        created_reservation = await client.create_reservation(create_payload)
        echo_json(created_reservation)


@quota.command()
@click.pass_context
@click.option('--limit', type=int, help='Limit the number of results')
@click.option('--offset', type=int, help='Offset for pagination')
@click.option('--sort', type=str, help='Sort specification')
@click.option('--fields', type=str, help='Comma separated list of fields to use')
@click.option('--filters', type=str, help='Filters to apply')
@coro
async def get_reservations(ctx, limit, offset, sort, fields, filters):
    """Get reservations"""
    async with quota_client(ctx) as client:
        reservations = await client.get_reservations(
            limit=limit,
            offset=offset,
            sort=sort,
            fields=fields,
            filters=json.loads(filters) if filters else None
        )
        echo_json(reservations)


@quota.command()
@click.pass_context
@click.argument('aoi_refs', nargs=-1)
@click.argument('product_id', type=int)
@click.argument('collection_id', type=str)
@coro
async def create_bulk_reservations(ctx, aoi_refs, product_id, collection_id):
    """Create bulk reservations"""
    async with quota_client(ctx) as client:
        create_payload = {
            "aoi_refs": list(aoi_refs),
            "product_id": product_id,
            "collection_id": collection_id
        }
        job_details = await client.create_bulk_reservations(create_payload)
        echo_json(job_details)


@quota.command()
@click.pass_context
@click.argument('job_id', type=int)
@coro
async def get_bulk_reservation_job(ctx, job_id):
    """Get bulk reservation job"""
    async with quota_client(ctx) as client:
        job = await client.get_bulk_reservation_job(job_id)
        echo_json(job)


if __name__ == "__main__":
    quota()