# Copyright 2020 Planet Labs, Inc.
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

API_KEY = os.getenv('PL_API_KEY')
DOWNLOAD_DIR = os.getenv('TEST_DOWNLOAD_DIR', '.')

iowa_aoi = {
    "type": "Polygon",
    "coordinates": [[
        [-91.198465, 42.893071],
        [-91.121931, 42.893071],
        [-91.121931, 42.946205],
        [-91.198465, 42.946205],
        [-91.198465, 42.893071]]]
}

iowa_images = [
    '20200925_161029_69_2223',
    '20200925_161027_48_2223'
]
iowa_order = planet.OrderDetails(
    'iowa_order',
    [planet.Product(iowa_images, 'analytic', 'PSScene4Band')],
    tools=[planet.Tool('clip', {'aoi': iowa_aoi})]
)

oregon_aoi = {
    "type": "Polygon",
    "coordinates": [[
        [-117.558734, 45.229745],
        [-117.452447, 45.229745],
        [-117.452447, 45.301865],
        [-117.558734, 45.301865],
        [-117.558734, 45.229745]]]
}

oregon_images = [
    '20200909_182525_1014',
    '20200909_182524_1014'
]
oregon_order = planet.OrderDetails(
    'oregon_order',
    [planet.Product(oregon_images, 'analytic', 'PSScene4Band')],
    tools=[planet.Tool('clip', {'aoi': oregon_aoi})]
)


async def create_and_download(order_detail, directory, client):
    # create
    print('Creating order')
    oid = await client.create_order(order_detail)
    print(f'Order created: {oid}')

    # poll
    state = await client.poll(oid, verbose=True)
    print(f'Order {oid} final state: {state}')

    # download
    print(f'Downloading {oid} to {directory}.')
    filenames = await client.download_order(oid, directory, progress_bar=True)
    for f in filenames:
        print(f)


async def main():
    async with planet.Session(auth=(API_KEY, '')) as ps:
        client = planet.OrdersClient(ps)

        await asyncio.gather(
            create_and_download(iowa_order, DOWNLOAD_DIR, client),
            create_and_download(oregon_order, DOWNLOAD_DIR, client)
        )


if __name__ == '__main__':
    asyncio.run(main())
