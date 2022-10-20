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

from planet import Session, DataClient

item_id = '20221003_002705_38_2461'
item_type_id = 'PSScene'
ortho_analytic_asset_type_id = 'ortho_analytic_4b'
analytic_asset_type_id = 'basic_analytic_4b'

async def download_and_validate(item_id, item_type_id, asset_type_id):
    async with Session() as sess:
        cl = DataClient(sess)

        # get asset description
        asset = await cl.get_asset(item_type_id, item_id, asset_type_id)

        # activate asset
        await cl.activate_asset(asset)

        # wait for asset to become active
        asset = await cl.wait_asset(asset, callback=print)

        # download asset
        path = await cl.download_asset(asset)

        # validate download file
        cl.validate_checksum(asset, path)


async def main():
    await asyncio.gather(
        download_and_validate(item_id, item_type_id, ortho_analytic_asset_type_id),
        download_and_validate(item_id, item_type_id, analytic_asset_type_id))


if __name__ == '__main__':
    asyncio.run(main())
