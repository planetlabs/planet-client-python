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
"""Example of downloading multiple assets in parallel

This is an example of getting two assets, activating them, waiting for them to
become active, downloading them, then validating the checksums of downloaded
files.

[Planet Explorer](https://www.planet.com/explorer/) was used to define
the AOIs and get the image ids.
"""
import asyncio

from planet import Session

river_item_id = '20221003_002705_38_2461'
river_item_type = 'PSScene'
river_asset_type = 'ortho_analytic_4b'

wildfire_item_id = '20221019_183717_11_2475'
wildfire_item_type = 'PSScene'
wildfire_asset_type = 'basic_analytic_4b'


async def download_and_validate(client, item_id, item_type_id, asset_type_id):
    """Activate, download, and validate an asset as a single task."""
    # Get asset description
    asset = await client.get_asset(item_type_id, item_id, asset_type_id)

    # Activate asset
    await client.activate_asset(asset)

    # Wait for asset to become active
    asset = await client.wait_asset(asset, callback=print)

    # Download asset
    path = await client.download_asset(asset)

    # Validate download file
    client.validate_checksum(asset, path)


async def main():
    """Download and validate assets in parallel."""
    async with Session() as sess:
        client = sess.client('data')
        await asyncio.gather(
            download_and_validate(client,
                                  river_item_id,
                                  river_item_type,
                                  river_asset_type),
            download_and_validate(client,
                                  wildfire_item_id,
                                  wildfire_item_type,
                                  wildfire_asset_type))


if __name__ == '__main__':
    asyncio.run(main())
