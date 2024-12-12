---
title: Planet Client Quick Start
---

The Planet SDK for Python makes it easy to access Planet’s massive repository of satellite imagery and add Planet
data to your data ops workflow.

**Note:** This is the new, non-asyncio client. If you want to take advantage of asyncio, check the [asyncio client quick start guide](quick-start-guide.md).

Your feedback on this version of our client is appreciated. Please raise an issue on [GitHub](https://github.com/planetlabs/planet-client-python/issues) if you encounter any problems.

## Dependencies

This package requires [Python 3.9 or greater](https://python.org/downloads/). A virtual environment is strongly recommended.

You will need your Planet API credentials. You can find your API key in [Planet Explorer](https://planet.com/explorer) under Account Settings.

## Installation

Install from PyPI using pip:

```bash
pip install planet
```

## Usage

### Authentication

Use the `PL_API_KEY` environment variable to authenticate with the Planet API.

```bash
export PL_API_KEY=your_api_key
```

These examples will assume you are using the `PL_API_KEY` environment variable. If you are, you can skip to the next section.

#### Authenticate using the Session class

Alternately, you can also authenticate using the `Session` class:

```python
from planet import Auth, Session, Auth
from planet.auth import APIKeyAuth

pl = Planet(session=Session(auth=APIKeyAuth(key='your_api_key')))
```


### The Planet client

The `Planet` class is the main entry point for the Planet SDK. It provides access to the various APIs available on the Planet platform.

```python
from planet import Planet
pl = Planet()  # automatically detects PL_API_KEY
```

The Planet client has members `data`, `orders`, and `subscriptions`, which allow you to interact with the Data API, Orders API, and Subscriptions API.

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

    for item in pl.data.search(['PSScene'], filter=sfilter, limit=10):
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

### Placing an Order

Once you have a list of scenes you want to download, you can place an order for assets using the Orders API client. Please review
[Items and Assets](https://developers.planet.com/docs/apis/data/items-assets/) in the Developer Center for a refresher on item types
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
               product_bundle='analytic_udm2',
               item_type='psscene')
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

request = build_request("Standard PSScene Ortho Analytic", source=source, delivery={})

# define a delivery method. In this example, we're using AWS S3.
delivery = amazon_s3(ACCESS_KEY_ID, SECRET_ACCESS_KEY, "test", "us-east-1")

# finally, create the subscription
subscription = pl.subscriptions.create_subscription(request)
```
