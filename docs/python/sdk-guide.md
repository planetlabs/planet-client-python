---
title: Python SDK User Guide
---

This guide is for Planet SDK for Python users who want to use Python code to search, order, customize, and deliver Planet imagery and data. If you’re new to Python, you may want to choose the no-code option of using the [command-line interface (CLI)](../../cli/cli-guide). But if you’ve successfully followed the instructions to [get started](../../get-started/quick-start-guide) and you’re ready to try your hand at Python coding, this guide should be all you need to use this SDK to get Planet data.

This guide walks you through the steps:

* **[Authenticate](#authenticate-with-planet-services)**—pass your username and password to Planet services to verify your permissions to data.
* **[Create a session](#create-a-session)**—set up a context for calling on Planet servers and receiving data back.
* **[Create an order](#create-an-order)**—build an orders client, send the request within the session context, and download it when it’s ready.
* **[Collect and list data](#collecting-results)**—handle the potentially large number of results from a search for imagery.
* **[Query the data catalog](#query-the-data-catalog)**—search the catalog based on a filter, activate the assets you want, and download and validate it when it’s ready.

## Authenticate with Planet services

An SDK `Session` requires authentication to communicate with Planet services. This
authentication information is retrieved when a `Session` is created. By default,
a `Session` retrieves authorization key from the environment variable `PL_API_KEY` or a secret file, in that order of priority.

The SDK provides the `auth.Auth` class for managing authentication information.
This module can be used to obtain authentication information from the username
and password with `Auth.from_login()`. Additionally, it can be created with
the API key obtained directly from the Planet account site with `Auth.from_key(<API_KEY>)`.

Once you have provided the authentication information (in other words, the username and API key), it can be accessed by way of the `Auth.value`. The most convenient way of managing it for local use is to write it to a secret file using `Auth.write()`. For example, to obtain and store authentication information:

Once you have provided the authentication information (in other words, the account username and password), it can be accessed by way of `Auth.value`. The most convenient way of managing it for local use is to write it to a secret file using `Auth.write()`.
It can also be accessed, for example, to store in an environment variable, such as
`Auth.value`.

Here is an example of retrieving and storing authentication information:

```python
# Get the user account name and password
# from the command line and environment,
# and store credentials in an Auth object
import getpass
from planet import Auth

user = input("Username: ")
pw = getpass.getpass()
auth = Auth.from_login(user,pw)
auth.store()
```

The default authentication behavior of the `Session` can be modified by specifying
`Auth` explicitly using the methods `Auth.from_file()` and `Auth.from_env()`.
While `Auth.from_key()` and `Auth.from_login` can be used, it is recommended
that those functions be used in authentication initialization. Authentication 
information should be stored using `Auth.store()`.

You can customize the manner of retrieval and location to read from when retrieving the authorization information. The file and environment variable read from can be customized in the respective functions. For example, authentication can be read from a custom
environment variable, as in the following code:

```python
import asyncio
import os
from planet import Auth, Session

auth = Auth.from_env('ALTERNATE_VAR')
async def main():
    async with Session(auth=auth) as sess:
        # perform operations here
        pass

asyncio.run(main())

```

## Create your first session

Communication with the Planet services is provided by way of the `Session` class. The `Session` class automatically implements rate limiting that allows for smooth asynchronous communication with Planet servers. Note that this rate-limiting only works when one `Session` is being used. Employing multiple sessions will cause the rate-limiting to be bypassed and can cause collisions.

To use `Session`, it’s recommended to use it as a context manager. In this way, your session is clearly defined and is handled as part of the context. For example, the context manager handles automatic cleanup of connections when the context is left, such as when an exception occurs.

```python
import asyncio
import os
from planet import Session

async def main():
    async with Session() as sess:
        # perform operations here
        pass

asyncio.run(main())
```

Alternatively, you may need to manually manage the lifecycle of the session, for example to reuse it across multiple asynchronous functions. In this case, you may consider using `await Session.aclose()` and close that `Session` explicitly:

```python
async def main():
    sess = Session()
    # perform operations here
    await sess.aclose()

asyncio.run(main())
```

### Use asyncio to order Planet data

As noted above, to ensure your session is properly managed and cleaned up when it’s no longer needed, create a session using the `Session` class and use it as a context manager.

The proper implementation of the `Session` class:

* uses it as a context manager, with rate limiting which allows for smooth asynchronous communication with Planet servers
* works with one `Session` at a time—multiple sessions bypass rate-limiting and can cause collisions

!!!warning "Caution"
    Do not use multiple `Sessions` as it can cause collisions and bypass rate-limiting.

For an example of using `asyncio` to order Planet data with a rate-limited session, you can see in the <a href="https://github.com/planetlabs/planet-client-python/blob/main/examples/orders_create_and_download_multiple_orders.py" target="_blank">Create and download multiple orders</a> example. The main function in that example creates a client session and pulls in multiple request objects (an area of interest in Iowa and another in Oregon that were created in a `create_requests()` function). The requests are dynamically generated and queued. Finally, orders are delivered into your preferred location (using a `create_and_download()` function).

```python
import asyncio
import os

import planet
.
.
.
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
```

## Create an order

The Orders Client mostly mirrors the [Planet Orders API](https://developers.planet.com/docs/orders/reference/#tag/Orders). This SDK provides additional abilities, for example to poll for order completion and to download an entire order.

### Create an order request

As a first step in ordering, you create an order request object. This request object is transmitted to the Planet service as a JSON object. The SDK provides a way for you to build up that object: `planet.order_request.build_request()`. The following code returns an order request object, with the values you’ve provided for:

* a name for your order
* what product to order—in this example, `PSScene` items with `analytic_udm2` product bundle asset types
* what tools to use—here, the clip tool with the area of interest (AOI) to clip within

```python
def create_request():
    # This is your area of interest for the Orders clipping tool
    oregon_aoi = {
       "type":
       "Polygon",
       "coordinates": [[[-117.558734, 45.229745], [-117.452447, 45.229745],
                        [-117.452447, 45.301865], [-117.558734, 45.301865],
                        [-117.558734, 45.229745]]]
   }

   # In practice, you will use a Data API search to find items, but
   # for this example take them as given.
   oregon_items = ['20200909_182525_1014', '20200909_182524_1014']

   oregon_order = planet.order_request.build_request(
       name='oregon_order',
       products=[
           planet.order_request.product(item_ids=oregon_items,
                                        product_bundle='analytic_udm2',
                                        item_type='PSScene')
       ],
       tools=[planet.order_request.clip_tool(aoi=oregon_aoi)])

   return oregon_order
```

This would be equivalent to a manually created JSON object with the following description:

```json
{
   "name":"oregon_order”,
   "products":[
      {
         "Item_ids":["20200909_182525_1014",
                     "20200909_182524_1014"],
         "item_type":"PSScene",
         "product_bundle":"analytic_sr_udm2"
      }
   ],
  "tools": [
    {
      "clip": {
        "aoi": {
          "type": "Polygon",
          "coordinates": [
            [[-117.558734, 45.229745], [-117.452447, 45.229745],
             [-117.452447, 45.301865], [-117.558734, 45.301865],
             [-117.558734, 45.229745]]
          ]
        }
      }
    }
  ]
}
```

Once the order request is built, create an order within the context of a `Session` with the `OrdersClient` `create_order()` function and pass the order request object in:

```python
async def main():
    async with Session() as sess:
        cl = sess.client('orders')
        order = await cl.create_order(request)

asyncio.run(main())

```

So given the order object created with the call to `create_request()`, [above](#create-an-order-request), the following code creates an Orders API client and uses that client to create and order.

```python
async def main():
    # Create a session and client
    # The Orders API client is also a subclass of the Session
    # class, so it has all the same methods.
    async with planet.Session() as sess:

        # 'orders' is the service name for the Orders API.
        cl = sess.client('orders')

        request = create_request()
        order = await cl.create_order(request)
```

If you run the code now, it appears as if nothing happens, because the order is being created and more importantly because you haven’t described where the order should be delivered to.

At this point, you can go into your account dashboard and select My Orders to see the order. And if the order is finished, you can select “download” (the default delivery mechanism) to view the order, see a preview of the clipping tool, and download the assets.

But of course, the point is to use the SDK to also deliver the ordered assets to a specified location automatically, which the next section describes.

### Waiting and downloading an order

After creating an order client, there is typically a waiting period before the assets can be downloaded. During this time, the order is being processed and customized according to the specifications provided in the order request. To monitor the progress of the order creation process and determine when the assets are ready for download, you can use the wait method provided by the Orders API client.

With wait and download, it is often desired to track progress as these
processes can take a long time. To track the progress of the order, the following example code uses a progress bar from the reporting module to report the wait status. The `download_order` method has built-in reporting capabilities, so we don’t need to use a progress bar for the download process.

```python
from planet import reporting

async def create_wait_and_download():
    async with Session() as sess:
        cl = sess.client('orders')
        with reporting.StateBar(state='creating') as bar:
            # create order
            order = await cl.create_order(request)
            bar.update(state='created', order_id=order['id'])

            # poll
            await cl.wait(order['id'], callback=bar.update_state)

        # download
        await cl.download_order(order['id'])

asyncio.run(create_poll_and_download())
```

Following on the the request object you created with the `create_request()`, [above](#create-an-order-request), the following function provides the status as you wait for the file to be downloaded to the current directory:

```python
async def create_and_download(client, order_detail, directory):
   with planet.reporting.StateBar(state='creating') as reporter:
       order = await client.create_order(order_detail)
       reporter.update(state='created', order_id=order['id'])
       await client.wait(order['id'], callback=reporter.update_state)

   await client.download_order(order['id'], directory, progress_bar=True)

async def main():
   async with planet.Session() as sess:
       cl = sess.client('orders')

       # Create the order request
       request = create_request()

       # Create and download the order
       order = await create_and_download(cl, request, DOWNLOAD_DIR)
```

Now, instead of going to your account dashboard to see the order request running, you can see the status as output on your output. For example:

```console
02:06 - order [id number] - state: running
```

And when your order is ready, it will download into the current directory, while writing status to the output:

```console
order-id/PSScene/20200909_182524_1014_metadata.json: 100%|█| 0.00k/0.00k [0
order-id/PSScene/20200909_182524_1014_3B_AnalyticMS_metadata_clip.xml: 100%
order-id/PSScene/20200909_182524_1014_3B_udm2_clip.tif: 100%|█| 0.55k/0.55k
order-id/PSScene/20200909_182524_1014_3B_AnalyticMS_clip.tif: 100%|█| 25.5k
order-id/PSScene/20200909_182525_1014_metadata.json: 100%|█| 0.00k/0.00k [0
order-id/PSScene/20200909_182525_1014_3B_AnalyticMS_metadata_clip.xml: 100%
order-id/PSScene/20200909_182525_1014_3B_udm2_clip.tif: 100%|█| 0.52k/0.52k
order-id/PSScene/20200909_182525_1014_3B_AnalyticMS_clip.tif: 100%|█| 27.1k
order-id/manifest.json: 100%|██████████| 0.00k/0.00k [00:00<00:00, 788kB/s]
```

### Validating checksums

Checksum validation provides for verification that the files in an order have
been downloaded successfully and are not missing, corrupted, or changed. This
functionality is included in the OrderClient, but does not require an instance
of the class to be used.

To perform checksum validation:

```python
from pathlib import Path

# path includes order id
order_path = Path('193e5bd1-dedc-4c65-a539-6bc70e55d928')
OrdersClient.validate_checksum(order_path, 'md5')
```

## Collecting results

Some API calls, such as searching for imagery and listing orders, return a
varying, and potentially large, number of results. These API responses are
paged. The SDK manages paging internally and the associated client commands
return an asynchronous iterator over the results. These results can be
converted to a JSON blob using the `collect` command. When the results
represent GeoJSON features, the JSON blob is a GeoJSON FeatureCollection.
Otherwise, the JSON blob is a list of the individual results.

```python
import asyncio
from planet import collect, Session

async def main():
    async with Session() as sess:
        client = sess.client('orders')
        orders_list = collect(client.list_orders())

asyncio.run(main())

```

Alternatively, these results can be converted to a list directly with

```python
orders_list = [o async for o in client.list_orders()]
```

## Query the data catalog

The Data Client mostly mirrors the
[Data API](https://developers.planet.com/docs/apis/data/reference/),
with the only difference being the addition of functionality to activate an
asset, poll for when activation is complete, and download the asset.

```python
async def main():
    async with Session() as sess:
        client = sess.client('data')
        # perform operations here

asyncio.run(main())
```

### Filter

When performing a quick search, creating or updating a saved search, or
requesting stats, the data search filter must be provided to the API
as a JSON blob. This JSON blob can be built up manually or by using the
`data_filter` module.

An example of creating the request JSON with `data_filter`:

```python
from datetime import datetime
from planet import data_filter
sfilter = data_filter.and_filter([
    data_filter.permission_filter(),
    data_filter.date_range_filter('acquired', gt=datetime(2022, 6, 1, 1))
])
```

The same thing, expressed as a `JSON` blob:

```python
sfilter = {
    'type': 'AndFilter',
    'config': [
        {'type': 'PermissionFilter', 'config': ['assets:download']},
        {
            'type': 'DateRangeFilter',
            'field_name': 'acquired',
            'config': {'gt': '2022-06-01T01:00:00Z'}
        }
    ]
}
```

Once the filter is built up, performing a search is done within
the context of a `Session` with the `DataClient`:

```python
async def main():
    async with Session() as sess:
        cl = sess.client('data')
        items = [i async for i in cl.search(['PSScene'], sfilter)]

asyncio.run(main())
```

### Downloading an asset

Downloading an asset is a multi-step process involving: activating the asset,
waiting for the asset to be active, downloading the asset, and, optionally,
validating the downloaded file.

With wait and download, it is often desired to track progress as these
processes can take a long time. Therefore, in this example, we use a simple 
print command to report wait status. `download_asset` has reporting built in.

```python
async def download_and_validate():
    async with Session() as sess:
        cl = sess.client('data')

        # get asset description
        item_type_id = 'PSScene'
        item_id = '20221003_002705_38_2461'
        asset_type_id = 'ortho_analytic_4b'
        asset = await cl.get_asset(item_type_id, item_id, asset_type_id)
        
        # activate asset
        await cl.activate_asset(asset)

        # wait for asset to become active
        asset = await cl.wait_asset(asset, callback=print)

        # download asset
        path = await cl.download_asset(asset)

        # validate download file
        cl.validate_checksum(asset, path)
```

## API Exceptions

When errors occur, the Planet SDK for Python exception hierarchy is as follows:

* All exceptions inherit from the base exception called `PlanetError`.
* Client-side errors are raised as `ClientError`.
* Server-side errors are raised as specific exceptions based on the http code. These specific exceptions all inherit from `APIError`  and contain the original error message returned by the server.
