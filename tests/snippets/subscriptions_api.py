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
from datetime import datetime
from planet.subscription_request import (build_request,
                                         catalog_source,
                                         amazon_s3,
                                         harmonize_tool)


def create_request():
    '''Create a subscription request.'''

    # Area of interest for the subscription
    geom = {
        "coordinates":
        [[[139.5648193359375,
           35.42374884923695], [140.1031494140625, 35.42374884923695],
          [140.1031494140625,
           35.77102915686019], [139.5648193359375, 35.77102915686019],
          [139.5648193359375, 35.42374884923695]]],
        "type":
        "Polygon"
    }
    source = catalog_source(item_types=["PSScene"],
                            asset_types=["ortho_analytic_4b"],
                            geometry=geom,
                            start_time=datetime(2021, 3, 1))
    delivery = amazon_s3(aws_access_key_id="ACCESS-KEY-ID",
                         aws_secret_access_key="SECRET_ACCESS_KEY",
                         bucket="test_bucket",
                         aws_region="us-east-1")
    tools = harmonize_tool(target_sensor="Sentinel-2")

    # Build your subscriptions request
    subscription_request = build_request(name='test_subscription',
                                         source=source,
                                         delivery=delivery,
                                         tools=tools)
    return subscription_request


# list_subscriptions
async def list_subscriptions(status, limit):
    '''Code snippet for list_subscriptions.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        async for sub in client.list_subscriptions(status=status, limit=limit):
            return sub


# create_subscription
async def create_subscription(request):
    '''Code snippet for create_subscription.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        sub = await client.create_subscription(request=request)
        return sub


# cancel_subscription
async def cancel_subscription(subscription_id):
    '''Code snippet for cancel_subscription.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        _ = await client.cancel_subscription(subscription_id=subscription_id)


# update_subscription
async def update_subscription(subscription_id, request):
    '''Code snippet for update_subscription.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        sub = await client.update_subscription(subscription_id=subscription_id,
                                               request=request)
        return sub


# get_subscription
async def get_subscription(subscription_id):
    '''Code snippet for get_subscription.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        sub = await client.get_subscription(subscription_id=subscription_id)
        return sub


# get_results
async def get_results(subscription_id, status, limit):
    '''Code snippet for get_results.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        async for result in client.get_results(subscription_id=subscription_id,
                                               status=status,
                                               limit=limit):
            return result
