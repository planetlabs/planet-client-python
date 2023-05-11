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
import shutil
import os
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
async def test_snippet_orders_create_order():
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
    assert len(order['id']) > 0
    return order


@pytest.mark.anyio
async def test_snippet_orders_get_order():
    '''Code snippet for get_order.'''
    order = await test_snippet_orders_create_order()
    order_id = order['id']
    # --8<-- [start:get_order]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.get_order(order_id=order_id)
    # --8<-- [end:get_order]
    assert len(order['id']) > 0
    # TO DO: get order ID some other way


@pytest.mark.anyio
async def test_snippet_orders_cancel_order():
    '''Code snippet for cancel_order.'''
    order = await test_snippet_orders_create_order()
    order_id = order['id']
    # --8<-- [start:cancel_order]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.cancel_order(order_id=order_id)
    # --8<-- [end:cancel_order]
    # TO DO: get order ID some other way
    assert order['state'] == 'cancelled'


@pytest.mark.anyio
async def test_snippets_cancel_multiple_orders():
    '''Code snippet for cancel_order.'''
    order1 = await test_snippet_orders_create_order()
    order2 = await test_snippet_orders_create_order()
    order_id1 = order1['id']
    order_id2 = order2['id']
    # --8<-- [start:cancel_orders]
    async with planet.Session() as sess:
        client = sess.client('orders')
        orders = await client.cancel_orders(order_ids=[order_id1, order_id2])
    # --8<-- [end:cancel_orders]
    assert orders['result']['succeeded']['count'] == 2


@pytest.mark.anyio
async def test_snippet_orders_aggregated_order_stats():
    '''Code snippet for aggregated_order_stats.'''
    # --8<-- [start:aggregated_order_stats]
    async with planet.Session() as sess:
        client = sess.client('orders')
        json_resp = await client.aggregated_order_stats()
    # --8<-- [start:aggregated_order_stats]
    assert 'organization' and 'user' in [key for key in json_resp.keys()]


@pytest.mark.anyio
async def test_snippet_orders_download_asset():
    '''Code snippet for download_asset.'''
    # order = await test_snippet_orders_create_order()
    # order_id = order['id']
    order_id = "decde86f-a57a-45bd-89f9-2af49a661e25"
    # --8<-- [start:download_asset]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.get_order(order_id=order_id)
        # Find order info
        info = order['_links']['results']
        # Find and download the the composite.tif file
        for i in info:
            if 'composite.tif' in i['name']:
                location = i['location']
                filename = await client.download_asset(location=location)
                # --8<-- [end:download_asset]
                assert filename.exists()
                os.remove(filename)
            else:
                pass


@pytest.mark.anyio
async def test_snippet_orders_download_order_without_checksum():
    '''Code snippet for download_order without checksum.'''
    order_id = "decde86f-a57a-45bd-89f9-2af49a661e25"
    # --8<-- [start:download_order_without_checksum]
    async with planet.Session() as sess:
        client = sess.client('orders')
        filenames = await client.download_order(order_id=order_id)
    # --8<-- [end:download_order_without_checksum]
    assert all([filename.exists() for filename in filenames])
    shutil.rmtree(filenames[0].parent)


@pytest.mark.anyio
async def test_snippet_orders_download_order_with_checksum():
    '''Code snippet for download_order with checksum.'''
    order_id = "decde86f-a57a-45bd-89f9-2af49a661e25"
    # --8<-- [start:download_order_without_checksum]
    async with planet.Session() as sess:
        client = sess.client('orders')
        filenames = await client.download_order(order_id=order_id)
        client.validate_checksum(directory=Path(order_id), checksum="MD5")
    # --8<-- [end:download_order_without_checksum]
    assert all([filename.exists() for filename in filenames])
    shutil.rmtree(filenames[0].parent)


@pytest.mark.anyio
async def test_snippet_orders_wait():
    '''Code snippet for wait.'''
    order_id = "decde86f-a57a-45bd-89f9-2af49a661e25"
    # --8<-- [start:wait]
    async with planet.Session() as sess:
        client = sess.client('orders')
        state = await client.wait(order_id=order_id)
    # --8<-- [end:wait]
    assert state == 'success'


@pytest.mark.anyio
async def test_snippet_orders_list_orders():
    '''Code snippet for list_orders.'''
    # --8<-- [start:list_orders]
    async with planet.Session() as sess:
        client = sess.client('orders')
        order_descriptions = [order async for order in client.list_orders()]
    # --8<-- [start:list_orders]
    assert order_descriptions[0].keys() == {
        '_links',
        'created_on',
        'error_hints',
        'id',
        'last_message',
        'last_modified',
        'name',
        'products',
        'state'
    }
