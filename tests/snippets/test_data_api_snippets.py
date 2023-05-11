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
import planet
from planet import data_filter
import json
from datetime import datetime
import pytest
import os


@pytest.fixture
def search_filter(get_test_file_json):
    filename = 'data_search_filter_2022-01.json'
    return get_test_file_json(filename)


@pytest.mark.anyio
async def test_snippet_data_search(search_filter):
    '''Code snippet for search.'''
    # --8<-- [start:search]
    async with planet.Session() as sess:
        client = sess.client('data')
        items_list = [
            item async for item in client.search(['PSScene'],
                                                 search_filter=search_filter,
                                                 name="My Search",
                                                 sort="acquired asc",
                                                 limit=10)
        ]
    # --8<-- [end:search]
    assert len(items_list) == 10


@pytest.mark.anyio
async def test_snippet_data_create_search(search_filter):
    '''Code snippet for create_search.'''
    # --8<-- [start:create_search]
    async with planet.Session() as sess:
        client = sess.client('data')
        response = await client.create_search(item_types=['PSScene'],
                                              search_filter=search_filter,
                                              name="My Search")
    # --8<-- [end:create_search]
    assert 'PSScene' in response['item_types']
    return response


@pytest.mark.anyio
async def test_snippet_data_update_search(search_filter):
    '''Code snippet for update_search.'''
    # --8<-- [start:update_search]
    async with planet.Session() as sess:
        client = sess.client('data')
        response = await client.update_search(
            search_id='66722b2c8d184d4f9fb8b8fcf9d1a08c',
            item_types=['PSScene'],
            search_filter=search_filter,
            name="My Search")
    # --8<-- [end:update_search]
    assert ['PSScene'] not in response['item_types']
    assert '66722b2c8d184d4f9fb8b8fcf9d1a08c' in response['id']
    # TO DO: use a mocked search_id


@pytest.mark.anyio
async def test_snippet_data_list_searches():
    '''Code snippet for list_searches.'''
    # --8<-- [start:list_searches]
    async with planet.Session() as sess:
        client = sess.client('data')
        search_list = [
            item async for item in client.list_searches(
                sort='created asc', search_type="saved", limit=10)
        ]
    # --8<-- [end:list_searches]
    assert len(search_list) == 10
    # Verifying sort='created asc'
    parsed_search_list = [
        datetime.strptime(search['created'], '%Y-%m-%dT%H:%M:%S.%fZ')
        for search in search_list
    ]
    assert sorted(parsed_search_list) == parsed_search_list


@pytest.mark.anyio
async def test_snippet_data_delete_search(search_filter):
    '''Code snippet for delete_search.'''
    new_search = await test_snippet_data_create_search(search_filter)
    search_id = new_search['id']
    # --8<-- [start:delete_search]
    async with planet.Session() as sess:
        client = sess.client('data')
        await client.delete_search(search_id=search_id)
        # --8<-- [end:delete_search]
        search_list = [
            item async for item in client.list_searches(
                sort='created asc', search_type="saved", limit=10)
        ]
    assert search_id not in [search['id'] for search in search_list]


@pytest.mark.anyio
async def test_snippet_data_get_search():
    '''Code snippet for get_search.'''
    # --8<-- [start:get_search]
    async with planet.Session() as sess:
        client = sess.client('data')
        search = await client.get_search(
            search_id='66722b2c8d184d4f9fb8b8fcf9d1a08c')
    # --8<-- [start:get_search]
    assert len(search) == 10
    assert search['id'] == '66722b2c8d184d4f9fb8b8fcf9d1a08c'


@pytest.mark.anyio
async def test_snippet_data_run_search():
    '''Code snippet for run_search.'''
    # --8<-- [start:run_search]
    async with planet.Session() as sess:
        client = sess.client('data')
        items_list = [
            i async for i in client.run_search(
                search_id='66722b2c8d184d4f9fb8b8fcf9d1a08c', limit=10)
        ]
    # --8<-- [end:run_search]
    assert len(items_list) == 10


@pytest.mark.anyio
async def test_snippet_data_get_stats(search_filter):
    '''Code snippet for get_stats.'''
    # --8<-- [start:get_stats]
    async with planet.Session() as sess:
        client = sess.client('data')
        stats = await client.get_stats(item_types=['PSScene'],
                                       search_filter=search_filter,
                                       interval="month")
    # --8<-- [end:get_stats]
    assert stats['interval'] == 'month'
    assert len(stats['buckets']) != 0


@pytest.mark.anyio
async def test_snippet_data_list_item_assets():
    '''Code snippet for list_item_assets.'''
    # --8<-- [start:list_item_assets]
    async with planet.Session() as sess:
        client = sess.client('data')
        assets = await client.list_item_assets(
            item_type_id='PSScene', item_id='20221003_002705_38_2461')
    # --8<-- [end:list_item_assets]
    assert len(assets) == 14


@pytest.mark.anyio
async def test_snippet_data_get_asset():
    '''Code snippet for get_asset.'''
    # --8<-- [start:get_asset]
    async with planet.Session() as sess:
        client = sess.client('data')
        asset = await client.get_asset(item_type_id='PSScene',
                                       item_id='20221003_002705_38_2461',
                                       asset_type_id='basic_udm2')
    # --8<-- [end:get_asset]
    assert asset['type'] == 'basic_udm2'


@pytest.mark.anyio
async def test_snippet_data_activate_asset():
    '''Code snippet for activate_asset.'''
    # --8<-- [start:activate_asset]
    async with planet.Session() as sess:
        client = sess.client('data')
        asset = await client.get_asset(item_type_id='PSScene',
                                       item_id='20221003_002705_38_2461',
                                       asset_type_id='basic_udm2')
        await client.activate_asset(asset)
    # --8<-- [end:activate_asset]
    assert asset['status'] == 'active'


@pytest.mark.anyio
async def test_snippet_data_wait_asset():
    '''Code snippet for wait_asset.'''
    # --8<-- [start:wait_asset]
    async with planet.Session() as sess:
        client = sess.client('data')
        asset = await client.get_asset(item_type_id='PSScene',
                                       item_id='20221003_002705_38_2461',
                                       asset_type_id='basic_udm2')
        _ = await client.wait_asset(asset, callback=print)
    # --8<-- [end:wait_asset]
    assert asset['status'] == 'active'


@pytest.mark.anyio
async def test_snippet_data_download_asset_without_checksum():
    '''Code snippet for download_asset without a checksum.'''
    # --8<-- [start:download_asset_without_checksum]
    async with planet.Session() as sess:
        client = sess.client('data')
        asset = await client.get_asset(item_type_id='PSScene',
                                       item_id='20221003_002705_38_2461',
                                       asset_type_id='basic_udm2')
        path = await client.download_asset(asset=asset)
    # --8<-- [end:download_asset_without_checksum]
    assert path.exists()
    os.remove(path)


@pytest.mark.anyio
async def test_snippet_data_download_asset_with_checksum():
    '''Code snippet for download_asset with a checksum.'''
    # --8<-- [start:download_asset_with_checksum]
    async with planet.Session() as sess:
        client = sess.client('data')
        asset = await client.get_asset(item_type_id='PSScene',
                                       item_id='20221003_002705_38_2461',
                                       asset_type_id='basic_udm2')
        path = await client.download_asset(asset=asset)
        client.validate_checksum(asset, path)
    # --8<-- [end:download_asset_with_checksum]
    assert path.exists()
    os.remove(path)


# Create search filters
def create_search_filter():
    '''Create a search filter.'''

    # Geometry you wish to clip to
    with open("aoi.geojson") as f:
        geom = json.loads(f.read())

    # Build your filters with all types of requirements
    date_range_filter = data_filter.date_range_filter("acquired",
                                                      gte=datetime(month=1,
                                                                   day=1,
                                                                   year=2017),
                                                      lte=datetime(month=1,
                                                                   day=1,
                                                                   year=2018))
    clear_percent_filter = data_filter.range_filter('clear_percent', 90)
    cloud_cover_filter = data_filter.range_filter('cloud_cover', None, 0.1)
    geom_filter = data_filter.geometry_filter(geom)
    asset_filter = data_filter.asset_filter(
        ["basic_analytic_4b", "basic_udm2", "ortho_visual"])
    permission_filter = data_filter.permission_filter()
    std_quality_filter = data_filter.std_quality_filter()

    # Search filter containing all filters listed above
    search_filter = data_filter.and_filter([
        date_range_filter,
        clear_percent_filter,
        cloud_cover_filter,
        geom_filter,
        asset_filter,
        permission_filter,
        std_quality_filter
    ])

    return search_filter
