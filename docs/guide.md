# User Guide

## API
### Session

Communication with the Planet services is provided with the `Session` class.
The recommended way to use a `Session` is as a context manager. This will
provide for automatic clean up of connections when the context is left.

```python
>>> import asyncio
>>> import os
>>> from planet import Session
>>>
>>> async def main():
...     async with Session() as sess:
...         # perform operations here
...         pass
...
>>> asyncio.run(main())

```

Alternatively, use `await Session.aclose()` to close a `Session` explicitly:

```python
>>> async def main():
...     sess = Session()
...     # perform operations here
...     await sess.aclose()
...
>>> asyncio.run(main())

```

### Authentication

There are two steps to managing authentication information, obtaining the
authentication information from Planet and then managing it for local retrieval
for authentication purposes.

The recommended method for obtaining authentication information is through
logging in, using `Auth.from_login()` (note: using something like the `getpass`
module is recommended to ensure your password remains secure). Alternatively,
the api key can be obtained directly from the Planet account site and then used
in `Auth.from_key()`.

Once the authentication information is obtained, the most convenient way of
managing it for local use is to write it to a secret file using `Auth.write()`.
It can also be accessed, e.g. to store in an environment variable, as
`Auth.value`.

For example, to obtain and store authentication information:

```python
>>> import getpass
>>> from planet import Auth
>>>
>>> pw = getpass.getpass()
>>> auth = Auth.from_login('user', 'pw')
>>> auth.write()

```

When a `Session` is created, by default, authentication is read from the secret
file created with `Auth.write()`. This behavior can be modified by specifying
`Auth` explicitly using the methods `Auth.from_file()` and `Auth.from_env()`.
While `Auth.from_key()` and `Auth.from_login` can be used, it is recommended
that those functions be used in authentication initialization and the
authentication information be stored using `Auth.write()`.

The file and environment variable read from can be customized in the
respective functions. For example, authentication can be read from a custom
environment variable:

```python
>>> import asyncio
>>> import os
>>> from planet import Auth, Session
>>>
>>> auth = Auth.from_env('ALTERNATE_VAR')
>>> async def main():
...     async with Session(auth=auth) as sess:
...         # perform operations here
...         pass
...
>>> asyncio.run(main())

```


### Collecting Results

Some API calls, such as searching for imagery and listing orders, return a
varying, and potentially large, number of results. These API responses are
paged. The SDK manages paging internally and the associated client commands
return an asynchronous iterator over the results. These results can be
converted to a JSON blob using the `collect` command. When the results
represent GeoJSON features, the JSON blob is a GeoJSON FeatureCollection.
Otherwise, the JSON blob is a list of the individual results.


```python
>>> import asyncio
>>> from planet import collect, OrdersClient, Session
>>>
>>> async def main():
...     async with Session() as sess:
...         client = OrdersClient(sess)
...         orders = client.list_orders()
...         orders_list = collect(orders)
...
>>> asyncio.run(main())

```


### Orders Client

The Orders Client mostly mirrors the
[Orders API](https://developers.planet.com/docs/orders/reference/#tag/Orders),
with the only difference being the addition of the ability to poll for when an
order is completed and to download an entire order.

```python
>>> from planet import OrdersClient
>>>
>>> async def main():
...     async with Session() as sess:
...         client = OrdersClient(sess)
...         # perform operations here
...
>>> asyncio.run(main())

```

#### Creating an Order

When creating an order, the order request details must be provided to the API
as a JSON blob. This JSON blob can be built up manually or by using the
`build_request` function.

An example of creating the request JSON with `build_request`:

```python
>>> from planet import order_request
>>> products = [
...     order_request.product(['20170614_113217_3163208_RapidEye-5'],
...                           'analytic', 'REOrthoTile')
... ]
...
>>> tools = [
...     order_request.toar_tool(scale_factor=10000),
...     order_request.reproject_tool(projection='WSG84', kernel='cubic'),
...     order_request.tile_tool(1232, origin_x=-180, origin_y=-90,
...               pixel_size=0.000027056277056,
...               name_template='C1232_30_30_{tilex:04d}_{tiley:04d}')
... ]
...
>>> request = order_request.build_request(
...     'test_order', products=products, tools=tools)
...

```

The same thing, expressed as a `JSON` blob:

```python
>>> request = {
...   "name": "test_order",
...   "products": [
...     {
...       "item_ids": [
...         "20170614_113217_3163208_RapidEye-5"
...       ],
...       "item_type": "REOrthoTile",
...       "product_bundle": "analytic"
...     }
...   ],
...   "tools": [
...     {
...       "toar": {
...         "scale_factor": 10000
...       }
...     },
...     {
...       "reproject": {
...         "projection": "WSG84",
...         "kernel": "cubic"
...       }
...     },
...     {
...       "tile": {
...         "tile_size": 1232,
...         "origin_x": -180,
...         "origin_y": -90,
...         "pixel_size": 2.7056277056e-05,
...         "name_template": "C1232_30_30_{tilex:04d}_{tiley:04d}"
...       }
...     }
...   ]
... }

```

Once the order request is built up, creating an order is done within
the context of a `Session` with the `OrdersClient`:

```python
>>> async def main():
...     async with Session() as sess:
...         cl = OrdersClient(sess)
...         order = await cl.create_order(request)
...
>>> asyncio.run(main())

```

#### Waiting and Downloading an Order

Once an order is created, the Orders API takes some time to create the order
and thus we must wait a while before downloading the order.
We can use waiting to watch the order creation process and find out when the
order is created successfully and ready to download.

With wait and download, it is often desired to track progress as these
processes can take a long time. Therefore, in this example, we use a progress
bar from the `reporting` module to report wait status. `download_order` has
reporting built in.

```python
from planet import reporting

>>> async def create_wait_and_download():
...     async with Session() as sess:
...         cl = OrdersClient(sess)
...         with reporting.StateBar(state='creating') as bar:
...             # create order
...             order = await cl.create_order(request)
...             bar.update(state='created', order_id=order['id'])
...
...             # poll
...             await cl.wait(order['id'], callback=bar.update_state)
...
...         # download
...         await cl.download_order(order['id'])
...
>>> asyncio.run(create_poll_and_download())
```

#### Validating Checksums

Checksum validation provides for verification that the files in an order have
been downloaded successfully and are not missing, currupted, or changed. This
functionality is included in the OrderClient, but does not require an instance
of the class to be used.


To perform checksum validation:

```python
from pathlib import Path

# path includes order id
order_path = Path('193e5bd1-dedc-4c65-a539-6bc70e55d928')
OrdersClient.validate_checksum(order_path, 'md5')
```




### Data Client

The Data Client mostly mirrors the
[Data API](https://developers.planet.com/docs/apis/data/reference/),
with the only difference being the addition of functionality to activate an
asset, poll for when activation is complete, and download the asset.

```python
>>> from planet import DataClient
>>>
>>> async def main():
...     async with Session() as sess:
...         client = DataClient(sess)
...         # perform operations here
...
>>> asyncio.run(main())

```

#### Filter

When performing a quick search, creating or updating a saved search, or
requesting stats, the data search filter must be provided to the API
as a JSON blob. This JSON blob can be built up manually or by using the
`data_filter` module.

An example of creating the request JSON with `data_filter`:

```python
>>> from datetime import datetime
>>> from planet import data_filter
>>> sfilter = data_filter.and_filter([
...     data_filter.permission_filter(),
...     data_filter.date_range_filter('acquired', gt=datetime(2022, 6, 1, 1))
... ])
```

The same thing, expressed as a `JSON` blob:

```python
>>> sfilter = {
...     'type': 'AndFilter',
...     'config': [
...         {'type': 'PermissionFilter', 'config': ['assets:download']},
...         {
...             'type': 'DateRangeFilter',
...             'field_name': 'acquired',
...             'config': {'gt': '2022-06-01T01:00:00Z'}
...         }
...     ]
... }
```

Once the filter is built up, performing a search is done within
the context of a `Session` with the `DataClient`:

```python
>>> async def main():
...     async with Session() as sess:
...         cl = DataClient(sess)
...         items = await cl.quick_search(sfilter)
...
>>> asyncio.run(main())
```

## CLI

### Authentication

The `auth` command allows the CLI to authenticate with Planet servers. Before
any other command is run, the CLI authentication should be initiated with

```console
$ planet auth init
```

To store the authentication information in an environment variable, e.g.
for passing into a Docker instance:

```console
$ export PL_API_KEY=$(planet auth value)
```


### Collecting Results

Some API calls, such as searching for imagery and listing orders, return a
varying, and potentially large, number of results. These API responses are
paged. The SDK manages paging internally and the associated cli commands
output the results as a sequence. These results can be converted to a JSON blob
using the `collect` command. When the results
represent GeoJSON features, the JSON blob is a GeoJSON FeatureCollection.
Otherwise, the JSON blob is a list of the individual results.

```console
$ planet data search-quick PSScene filter.json | planet collect -
```

contents of `filter.json`:

```json
{
   "type":"DateRangeFilter",
   "field_name":"acquired",
   "config":{
      "gt":"2019-12-31T00:00:00Z",
      "lte":"2020-01-31T00:00:00Z"
   }
}
```

### Orders API

Most `orders` cli commands are simple wrappers around the
[Planet Orders API](https://developers.planet.com/docs/orders/reference/#tag/Orders)
commands.


#### Create Order File Inputs

Creating an order supports JSON files as inputs and these need to follow certain
formats.


##### --cloudconfig
The file given with the `--cloudconfig` option should contain JSON that follows
the options and format given in
[Delivery to Cloud Storage](https://developers.planet.com/docs/orders/delivery/#delivery-to-cloud-storage).

An example would be:

Example: `cloudconfig.json`
```
{
    "amazon_s3": {
        "aws_access_key_id": "aws_access_key_id",
        "aws_secret_access_key": "aws_secret_access_key",
        "bucket": "bucket",
        "aws_region": "aws_region"
    },
    "archive_type": "zip"
}
```

##### --clip
The file given with the `--clip` option should contain valid [GeoJSON](https://geojson.org/).
It can be a Polygon geometry, a Feature, or a FeatureClass. If it is a FeatureClass,
only the first Feature is used for the clip geometry.

Example: `aoi.geojson`
```
{
    "type": "Polygon",
    "coordinates": [
        [
            [
                37.791595458984375,
                14.84923123791421
            ],
            [
                37.90214538574219,
                14.84923123791421
            ],
            [
                37.90214538574219,
                14.945448293647944
            ],
            [
                37.791595458984375,
                14.945448293647944
            ],
            [
                37.791595458984375,
                14.84923123791421
            ]
        ]
    ]
}
```

##### --tools
The file given with the `--tools` option should contain JSON that follows the
format for a toolchain, the "tools" section of an order. The toolchain options
and format are given in
[Creating Toolchains](https://developers.planet.com/docs/orders/tools-toolchains/#creating-toolchains).

Example: `tools.json`
```
[
    {
        "toar": {
            "scale_factor": 10000
        }
    },
    {
        "reproject": {
            "projection": "WGS84",
            "kernel": "cubic"
        }
    },
    {
        "tile": {
            "tile_size": 1232,
            "origin_x": -180,
            "origin_y": -90,
            "pixel_size": 2.7056277056e-05,
            "name_template": "C1232_30_30_{tilex:04d}_{tiley:04d}"
        }
    }
]
```

