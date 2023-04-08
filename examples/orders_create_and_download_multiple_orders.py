# Copyright 2020 Planet Labs, Inc.
# Copyright 2022 Planet Labs PBC.
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
import asyncio
import os

import planet

DOWNLOAD_DIR = os.getenv('TEST_DOWNLOAD_DIR', '.')


def create_requests():
    # The Orders API will be asked to mask, or clip, results to
    # this area of interest.
    iowa_aoi = {
        "type":
        "Polygon",
        "coordinates": [[[-91.198465, 42.893071], [-91.121931, 42.893071],
                         [-91.121931, 42.946205], [-91.198465, 42.946205],
                         [-91.198465, 42.893071]]]
    }

    # In practice, you will use a Data API search to find items, but
    # for this example take them as given.
    iowa_items = ['20200925_161029_69_2223', '20200925_161027_48_2223']

    iowa_order = planet.order_request.build_request(
        name='iowa_order',
        products=[
            planet.order_request.product(item_ids=iowa_items,
                                         product_bundle='analytic_udm2',
                                         item_type='PSScene')
        ],
        tools=[planet.order_request.clip_tool(aoi=iowa_aoi)])

    oregon_aoi = {
        "type":
        "Polygon",
        "coordinates": [[[-117.558734, 45.229745], [-117.452447, 45.229745],
                         [-117.452447, 45.301865], [-117.558734, 45.301865],
                         [-117.558734, 45.229745]]]
    }

    oregon_items = ['20200909_182525_1014', '20200909_182524_1014']

    oregon_order = planet.order_request.build_request(
        name='oregon_order',
        products=[
            planet.order_request.product(item_ids=oregon_items,
                                         product_bundle='analytic_udm2',
                                         item_type='PSScene')
        ],
        tools=[planet.order_request.clip_tool(aoi=oregon_aoi)])

    return [iowa_order, oregon_order]


async def create_and_download(client, order_detail, directory):
    """Make an order, wait for completion, download files as a single task."""
    with planet.reporting.StateBar(state='creating') as reporter:
        order = await client.create_order(order_detail)
        reporter.update(state='created', order_id=order['id'])
        await client.wait(order['id'], callback=reporter.update_state)

    await client.download_order(order['id'], directory, progress_bar=True)


async def main():
    async with planet.Session() as sess:
        client = sess.client('orders')

        requests = create_requests()

        await asyncio.gather(*[
            create_and_download(client, request, DOWNLOAD_DIR)
            for request in requests
        ])


if __name__ == '__main__':
    asyncio.run(main())
