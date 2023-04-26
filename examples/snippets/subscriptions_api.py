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


def create_request():
    pass


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
        sub = await client.create_subscription(request)
        return sub


# cancel_subscription
async def cancel_subscription(subscription_id):
    '''Code snippet for cancel_subscription.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        _ = await client.cancel_subscription(subscription_id)


# update_subscription
async def update_subscription(subscription_id, request):
    '''Code snippet for update_subscription.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        sub = await client.update_subscription(subscription_id, request)
        return sub


# get_subscription
async def get_subscription(subscription_id):
    '''Code snippet for get_subscription.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        sub = await client.get_subscription(subscription_id)
        return sub


# get_results
async def get_results(subscription_id, status, limit):
    '''Code snippet for get_results.'''
    async with planet.Session() as sess:
        client = sess.client('subscriptions')
        async for result in client.get_results(subscription_id,
                                               status=status,
                                               limit=limit):
            return result
