import asyncio
import logging
import os
import sys
import time

from planet.api import APlanetSession, AOrdersClient

LOGGER = logging.getLogger(__name__)
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, stream=sys.stdout, level=logging.DEBUG)

API_KEY = os.getenv('PL_API_KEY')

TEST_ORDER = {
      "name": "test_order",
      "products": [
        {
          "item_ids": [
            "3949357_1454705_2020-12-01_241c",
            "3949357_1454805_2020-12-01_241c"
          ],
          "item_type": "PSOrthoTile",
          "product_bundle": "analytic"
        }
      ]
    }


async def create_order(client):
    oid = await client.create_order(TEST_ORDER)
    LOGGER.info(oid)
    return oid


async def get_order(client, oid=None):
    oid = oid or "6e08ecea-0770-487b-91ac-dd45827ae2cd"
    order = await client.get_order(oid)
    LOGGER.info(f'Order {oid} has {len(order.results)} results')
    return order


async def cancel_order(client, oid=None):
    oid = await client.create_order(TEST_ORDER)
    await client.cancel_order(oid)
    LOGGER.info(f'Order {oid} cancelled')


async def download_asset(client):
    LOGGER.debug('downloading')
    url = "https://api.planet.com/compute/ops/download/?token=eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MTE3ODY3MjUsInN1YiI6InNsMzJHY05QZUNpZ2cwVDVzT25MaXJRWDR2aVMySmg0em8rVzRvV3VoaldIMWhJeko5QWhHT1ErbjltMVV0RmZGdEFwVFRLem5vdUZmY1NFMmlJbThBPT0iLCJ0b2tlbl90eXBlIjoiZG93bmxvYWQtYXNzZXQtc3RhY2siLCJhb2kiOiIiLCJhc3NldHMiOlt7Iml0ZW1fdHlwZSI6IiIsImFzc2V0X3R5cGUiOiIiLCJpdGVtX2lkIjoiIn1dLCJ1cmwiOiJodHRwczovL3N0b3JhZ2UuZ29vZ2xlYXBpcy5jb20vY29tcHV0ZS1vcmRlcnMtbGl2ZS84MjA5NDA5ZS01MjNlLTQ3ODUtOGQ0ZC0yYTY3NTVlY2E0YzkvUFNPcnRob1RpbGUvMzk0OTM1N18xNDU0NzA1XzIwMjAtMTItMDFfMjQxY19CR1JOX0FuYWx5dGljLnRpZj9FeHBpcmVzPTE2MTE3ODY3MjVcdTAwMjZHb29nbGVBY2Nlc3NJZD1jb21wdXRlLWdjcy1zdmNhY2MlNDBwbGFuZXQtY29tcHV0ZS1wcm9kLmlhbS5nc2VydmljZWFjY291bnQuY29tXHUwMDI2U2lnbmF0dXJlPUolMkJIcTBMNE9jY1BneiUyRmFlVGZSVzdCblNDVjYlMkZmYXoxZmZBTWRTSWdWcnpSRTlaWjklMkZEJTJGWVREZ25tTEUlMkJaMWt2Z2g4d2wzZ0VnS2w0S3lqJTJGR1VMdEt6WFBGbTNNamFPYlR3aUpzbXBnVW5rJTJGajRaRlp4RHJxdjcxdjdrSmxMYU1yd3pBQVE5em9rSUhyUmh3dkpJJTJGJTJCQXh4eFF6alQzMyUyRlAzb1c4U2JZR2RiSExSYUxjb0RFU3hHOVN4WFhNblREYjlBSm5oTkZBVnNFckt0ZnFDNG5nQXgyRXRNVUNWb2RIaWVzVlM5TWtHSkZqODJTOHZHMHhJcmxsb1o3UVZ0aW5Fb0RmMTZsVnhpTFdrSTdqSVFaekYwM3h6UyUyQnRza0ZZU2kzZzRVdE1Wa25WTWFZd0ElMkJ3ZUprNWZYZUVtZ0dScFpyRjJpaXJBckhUbFJhUUQzWmVRJTNEJTNEIiwic291cmNlIjoiT3JkZXJzIFNlcnZpY2UifQ.vjUyws36-5-SgMrtAbT7RuXkmM3YlJOnhMOF_Q_ZZAz0XJ3QPhj_GbAYfgV8uyhf4m0HQJIR7xTbld_AcJr4fA" # noqa

    await client.download_asset(url)


async def download_order(client, oid=None):
    oid = oid or "6e08ecea-0770-487b-91ac-dd45827ae2cd"
    await client.download_order(oid)


async def cancel_orders(client):
    resp = await client.cancel_orders()
    print(resp)


async def create_and_download(client):
    oid = await client.create_order(TEST_ORDER)
    await client.poll(oid)
    await client.download_order(oid)


async def main():
    start = time.time()
    auth = (API_KEY, "")
    async with APlanetSession(auth=auth) as ps:
        client = AOrdersClient(ps)
        await asyncio.gather(
            create_and_download(client),
            create_and_download(client),
            create_and_download(client),
            # create_order(client),
            # cancel_order(client),
            # download_order(client),
            # cancel_orders(client),
            # get_order(client),
            # get_order(client, "4b9b88bf-1d62-45f4-8bf9-4cd2fa6abb61"),
            )
    LOGGER.info(f'Process took {time.time()-start}s')

if __name__ == '__main__':
    asyncio.run(main())
