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
import planet


# create_order()
async def create_order(request):
    '''Code snippet for create_order.'''
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.create_order(request)
    return order


# get_order()
async def get_order(order_id):
    '''Code snippet for get_order.'''
    async with planet.Session() as sess:
        client = sess.client('orders')
        order = await client.get_order(order_id)
    return order


# cancel_order()
async def cancel_order(order_id):
    '''Code snippet for cancel_order.'''
    async with planet.Session() as sess:
        client = sess.client('orders')
        json_resp = await client.cancel_order(order_id)
    return json.dumps(json_resp)

# cancel_orders()

# aggregated_order_stats()

# download_asset()

# download_order()

# validate_checksum()

# wait()

# list_orders()

# 