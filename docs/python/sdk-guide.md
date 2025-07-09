---
title: Python SDK User Guide
---

This guide is for Planet SDK for Python users who want to use Python code to search, order, customize, and deliver Planet imagery and data. If you’re new to Python, you may want to choose the no-code option of using the [command-line interface (CLI)](../../cli/cli-guide). But if you’ve successfully followed the instructions to [get started](../../get-started/quick-start-guide) and you’re ready to try your hand at Python coding, this guide should be all you need to use this SDK to get Planet data.

!!!note
    Looking for the asyncio-based SDK? See the [Planet Async SDK guide](./async-sdk-guide.md).

## Usage

### Install the Planet Python SDK

Use a package manager (such as `pip`) to install the Planet Python SDK:

```sh
pip install planet
```

### The Planet client

The `Planet` class is the main entry point for the Planet SDK. It provides access to the various APIs available on the Planet platform.

```python
from planet import Planet
pl = Planet()  # automatically detects authentication configured by `planet auth login`
```

The Planet client has members `data`, `orders`, and `subscriptions`, which allow you to interact with the Data API, Orders API, and Subscriptions API.


### Authentication
To establish a user session that will be saved to the user's home directory
and will be picked up by the SDK, execute the following command:

```bash
planet auth login
```

These examples will assume you have done this, and are using the SDK's default
client authentication mechanisms.  For more advanced use cases, see the
[Client Authentication Guide](../auth/auth-overview.md) for a complete discussion of
all authentication options provided by the SDK.  This includes user
authentication with a web browser, service account authentication for detached
workloads using OAuth2, and support for legacy applications using Planet API keys.

### Search

To search for items in the Planet catalog, use the `data.search()` method on the `Planet` client. The return value is an iterator that yields search
results:

```python
from planet import Planet

pl = Planet()
for item in pl.data.search(['PSScene'], limit=5):
    print(item)
```

#### Geometry

Use the `geometry` parameter to filter search results by geometry:

```python
geom = {
  "coordinates": [
    [
      [
        -125.41267816101056,
        46.38901501783491
      ],
      [
        -125.41267816101056,
        41.101114161051015
      ],
      [
        -115.51426167332103,
        41.101114161051015
      ],
      [
        -115.51426167332103,
        46.38901501783491
      ],
      [
        -125.41267816101056,
        46.38901501783491
      ]
    ]
  ],
  "type": "Polygon"
}
for item in pl.data.search(['PSScene'], geometry=geom, limit=5):
    print(item)
```

#### Filters

The Data API allows a wide range of search parameters. Whether using the `.search()` method, or
creating or updating a saved search, or requesting stats, a data search filter
can be provided to the API as a JSON blob. This JSON blob can be built up manually or by using the
`data_filter` module.

An example of creating the request JSON with `data_filter`:

```python
from datetime import datetime
from planet import data_filter

def main():
    pl = Planet()

    sfilter = data_filter.and_filter([
        data_filter.permission_filter(),
        data_filter.date_range_filter('acquired', gt=datetime(2022, 6, 1, 1))
    ])

    for item in pl.data.search(['PSScene'], search_filter=sfilter, limit=10):
        print(item["id"])
```

This returns scenes acquired after the provided date that you have permission to download using
your plan.

If you prefer to build the JSON blob manually, the above filter would look like this:

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

This means that if you already have Data API filters saved as a query, you can copy them directly into the SDK.

#### Downloading a single asset

Downloading a single asset with the Data API is a multi-step process involving: activating the asset,
waiting for the asset to be active, downloading the asset, and, optionally,
validating the downloaded file.

With wait and download, it is often desired to track progress as these
processes can take a long time. Therefore, in this example, we use a simple
print command to report wait status. `download_asset` has reporting built in.

!!!note
    For bulk orders, we recommend creating an order or subscription.

```python
def download_and_validate():
    pl = Planet()

    # get asset description
    item_type_id = 'PSScene'
    item_id = '20221003_002705_38_2461'
    asset_type_id = 'ortho_analytic_4b'
    asset = pl.data.get_asset(item_type_id, item_id, asset_type_id)

    # activate asset
    pl.data.activate_asset(asset)

    # wait for asset to become active
    asset = pl.data.wait_asset(asset, callback=print)

    # download asset
    path = pl.data.download_asset(asset)

    # validate download file
    pl.data.validate_checksum(asset, path)
```

### Placing an Order

Once you have a list of scenes you want to download, you can place an order for assets using the Orders API client. Please review
[Items and Assets](https://docs.planet.com/develop/apis/data/items/) for a refresher on item types
and asset types.

Use the `order_request` module to build an order request, and then use the `orders.create_order()` method to place the order.

Orders take time to process. You can use the `orders.wait()` method to wait for the order to be ready, and then use the `orders.download_order()` method to download the assets.

Warning: running the following code will result in quota usage based on your plan.

```python
from planet import Planet, order_request

def main():
    pl = Planet()
    image_ids = ["20200925_161029_69_2223"]
    request = order_request.build_request(
        name='test_order',
        products=[
           order_request.product(
               item_ids=image_ids,
               product_bundle='analytic_8b_udm2',
               item_type='PSScene',
               fallback_bundle='analytic_udm2,analytic_3b_udm2')
       ]
    )

    order = pl.orders.create_order(request)

    # wait for the order to be ready
    # note: this may take several minutes.
    pl.orders.wait(order['id'])

    pl.orders.download_order(order['id'], overwrite=True)
```

### Creating a subscription

#### Prerequisites

Subscriptions can be delivered to a destination. The following example uses Amazon S3.
You will need your ACCESS_KEY_ID, SECRET_ACCESS_KEY, bucket and region name.

#### Scene subscription

To subscribe to scenes that match a filter, use the `subscription_request` module to build a request, and
pass it to the `subscriptions.create_subscription()` method of the client.

By default, a request to create a subscription will not clip matching imagery which intersects the source geometry.  To clip to the subscription source geometry, set `planet.subscription_request.build_request()` keyword argument `clip_to_source = True` as in the example below.  To clip to a custom geometry, set `planet.subscription_request.build_request()`  keyword argument `clip_to_source = False` (or omit it entirely to fall back on the default value), and instead configure the custom clip AOI with `planet.subscription_request.clip_tool()`.

Warning: the following code will create a subscription, consuming quota based on your plan.

```python
from planet.subscription_request import catalog_source, build_request, amazon_s3

source = catalog_source(
    ["PSScene"],
    ["ortho_analytic_4b"],
    geometry={
        "type": "Polygon",
        "coordinates": [
            [
                [37.791595458984375, 14.84923123791421],
                [37.90214538574219, 14.84923123791421],
                [37.90214538574219, 14.945448293647944],
                [37.791595458984375, 14.945448293647944],
                [37.791595458984375, 14.84923123791421],
            ]
        ],
    },
    start_time=datetime.now(),
    publishing_stages=["standard"],
    time_range_type="acquired",
)

# define a delivery method. In this example, we're using AWS S3.
delivery = amazon_s3(ACCESS_KEY_ID, SECRET_ACCESS_KEY, "test", "us-east-1")

# build the request payload
request = build_request("Standard PSScene Ortho Analytic", source=source, delivery=delivery, clip_to_source=True)

# finally, create the subscription
subscription = pl.subscriptions.create_subscription(request)
```

### Features API Collections and Features

The Python SDK now supports [Features API](https://docs.planet.com/develop/apis/features/) Collections and Features (note: in the SDK and API, Features are often referred to as items in a collection).

Collections and Features/items that you create in in the SDK will be visible in Features API and Features Manager.

#### Creating a collection

You can use the Python SDK to create feature collections in the Features API.

```python
new_collection = pl.features.create_collection(title="my collection", description="a new collection")
```

#### Listing collections

```python
collections = pl.features.list_collections()
for collection in collections:
  print(collection)
```

#### Listing features/items in a collection

```python
items = pl.features.list_items(collection_id)
for item in items:
  print(item)

```

#### Using items as geometries for other methods

You can pass collection items/features directly to other SDK methods. Any method that requires a geometry will accept
a Features API Feature.

!!!note
    When passing a Features API Feature to other methods, the [feature ref](https://docs.planet.com/develop/apis/features/#feature-references) will be used. This means any searches or subscriptions you create will be linked to your feature.

```python
# collection_id: the ID of a collection in Features API

items = pl.features.list_items(collection_id)
example_feature = next(items)
results = pl.data.search(["PSScene"], geometry=example_feature)
```

!!!note
    Reserving quota for features is currently not supported in the SDK. However, you may create features within the SDK and then use [Features Manager](https://planet.com/features) to reserve quota.

## API Exceptions

When errors occur, the Planet SDK for Python exception hierarchy is as follows:

* All exceptions inherit from the base exception called `PlanetError`.
* Client-side errors are raised as `ClientError`.
* Server-side errors are raised as specific exceptions based on the http code. These specific exceptions all inherit from `APIError`  and contain the original error message returned by the server.

## How to Get Help

As The Planet SDK (V2) is in active development, features & functionality will continue to be added.

If there's something you're missing or are stuck, the development team would love to hear from you.

  - To report a bug or suggest a feature, [raise an issue on GitHub](https://github.com/planetlabs/planet-client-python/issues/new)
  - To get in touch with the development team, email [developers@planet.com](mailto:developers@planet.com)
