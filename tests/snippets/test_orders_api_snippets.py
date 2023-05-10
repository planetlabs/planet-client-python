# Copyright 2023 Planet Labs PBC.
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
"""Example of creating and downloading multiple orders.

This is an example of submitting two orders, waiting for them to complete, and
downloading them. The orders each clip a set of images to a specific area of
interest (AOI), so they cannot be combined into one order.

[Planet Explorer](https://www.planet.com/explorer/) was used to define
the AOIs and get the image ids.
"""
import json
from pathlib import Path
import planet
import pytest


@pytest.fixture
def create_request():
    '''Create an order request.'''

    # The Orders API will be asked to mask, or clip, results to
    # this area of interest.
    aoi = {
        "type":
        "Polygon",
        "coordinates": [[[-91.198465, 42.893071], [-91.121931, 42.893071],
                         [-91.121931, 42.946205], [-91.198465, 42.946205],
                         [-91.198465, 42.893071]]]
    }

    # In practice, you will use a Data API search to find items, but
    # for this example take them as given.
    items = ['20200925_161029_69_2223', '20200925_161027_48_2223']

    order = planet.order_request.build_request(
        name='iowa_order',
        products=[
            planet.order_request.product(item_ids=items,
                                         product_bundle='analytic_udm2',
                                         item_type='PSScene')
        ],
        tools=[planet.order_request.clip_tool(aoi=aoi)])

    return order


@pytest.mark.anyio
async def test_snippet_create_order():
    '''Code snippet for create_order.'''
    order_request = {
        "name":
        "test",
        "products": [{
            "item_ids": ['20230508_155304_44_2480'],
            "item_type": "PSScene",
            "product_bundle": "analytic_udm2"
        }],
    }
    # --8<-- [start:create_order]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.create_order(request=order_request)
    # --8<-- [end:create_order]
    return order
    assert len(order['id']) > 0


@pytest.mark.anyio
async def test_snippet_get_order():
    '''Code snippet for get_order.'''
    order = await test_snippet_create_order()
    order_id = order['id']
    # --8<-- [start:get_order]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.get_order(order_id=order_id)
    # --8<-- [end:get_order]
    assert len(order['id']) > 0
    # TO DO: get order ID some other way


@pytest.mark.anyio
async def test_snippet_cancel_order():
    '''Code snippet for cancel_order.'''
    order = await test_snippet_create_order()
    order_id = order['id']
    # --8<-- [start:cancel_order]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.cancel_order(order_id=order_id)
    # --8<-- [end:cancel_order]
    # TO DO: get order ID some other way
    assert order['state'] == 'cancelled'


# cancel_orders()
@pytest.mark.anyio
async def test_snippets_cancel_multiple_orders():
    '''Code snippet for cancel_order.'''
    order1 = await test_snippet_create_order()
    order2 = await test_snippet_create_order()
    order_id1 = order1['id']
    order_id2 = order2['id']
    # --8<-- [start:cancel_orders]
    async with planet.Session() as sess:
        client = sess.client('orders')
        orders = await client.cancel_orders(order_ids=[order_id1, order_id2])
    # --8<-- [end:cancel_orders]
    assert order1['state'] == 'cancelled'
    assert order2['state'] == 'cancelled'


# aggregated_order_stats()
async def aggregated_order_stats():
    '''Code snippet for aggregated_order_stats.'''
    async with planet.Session() as sess:
        client = sess.client('orders')
        json_resp = await client.aggregated_order_stats()
    return json.dumps(json_resp)


# download_asset()
async def download_asset(dl_url, directory):
    '''Code snippet for download_asset.'''
    async with planet.Session() as sess:
        client = sess.client('orders')
        filename = await client.download_asset(location=dl_url,
                                               directory=directory)
    dl_path = Path(directory, filename)
    return dl_path


# download_order() w/o checksum
async def download_order_without_checksum(order_id, directory):
    '''Code snippet for download_order without checksum.'''
    async with planet.Session() as sess:
        client = sess.client('orders')
        filenames = await client.download_order(order_id, directory=directory)
    dl_path = Path(directory, filenames)
    return dl_path


# download_order() w checksum
async def download_order_with_checksum(order_id, directory):
    '''Code snippet for download_order with checksum.'''
    # Options: 'MD5' or 'SHA256'
    checksum = 'MD5'
    async with planet.Session() as sess:
        client = sess.client('orders')
        filenames = await client.download_order(order_id=order_id,
                                                directory=directory)
        client.validate_checksum(Path(directory, order_id), checksum)
    dl_path = Path(directory, filenames)
    return dl_path


# wait()
async def wait(order_id):
    '''Code snippet for wait.'''
    async with planet.Session() as sess:
        client = sess.client('orders')
        _ = await client.wait(order_id=order_id, callback=print)


# list_orders()
async def list_orders():
    '''Code snippet for list_orders.'''
    async with planet.Session() as sess:
        client = sess.client('orders')
        async for order in client.list_orders():
            return order


async def order_example():
    # Create an order request
    request = create_request()

    # Create order
    order = await create_order(request)

    # Get order ID
    order_id = order['id']

    # Wait for download to be ready
    await wait(order_id)

    # Download order
    _ = await download_order_with_checksum(order_id, './')
