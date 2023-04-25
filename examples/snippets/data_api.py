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


# search
async def search(item_types, search_filter, name, sort, limit):
    '''Code snippet for search.'''
    async with planet.Session() as sess:
        client = sess.client('data')
        async for item in client.search(item_types=item_types,
                                        search_filter=search_filter,
                                        name=name,
                                        sort=sort,
                                        limit=limit):
            print(item)


# create_search
async def create_search(item_types, search_filter, name):
    '''Code snippet for create_search.'''
    async with planet.Session() as sess:
        client = sess.client('data')
        items = await client.create_search(item_types=item_types,
                                           search_filter=search_filter,
                                           name=name)
        print(items)


# update_search
async def update_search(search_id, item_types, search_filter, name):
    '''Code snippet for update_search.'''
    async with planet.Session() as sess:
        client = sess.client('data')
        items = await client.update_search(search_id=search_id,
                                           item_types=item_types,
                                           search_filter=search_filter,
                                           name=name)
        print(items)


# list_searches
async def list_searches(sort, search_type, limit):
    '''Code snippet for list_searches.'''
    async with planet.Session() as sess:
        client = sess.client('data')
        async for item in client.list_searches(sort=sort,
                                               search_type=search_type,
                                               limit=limit):
            print(item)


# delete_search
async def delete_search(search_id):
    '''Code snippet for delete_search.'''
    async with planet.Session() as sess:
        client = sess.client('data')
        await client.delete_search(search_id)


# get_search
async def get_search(search_id):
    '''Code snippet for get_search.'''
    async with planet.Session() as sess:
        client = sess.client('data')
        items = await client.get_search(search_id)
        print(items)

# run_search

# get_stats

# list_item_assets

# get_asset

# activate_asset

# wait_asset

# download_asset w/o checksum

# download_asset w checksum


# Create search filters
def create_filters():
    pass
