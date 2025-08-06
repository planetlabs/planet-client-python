---
title: Upgrade from Version 1 to Version 2
---

The Planet SDK for Python is Version 2 of what was previously referred to as the Planet API client. This V2 is a major update of the V1 SDK. As such, there are major structural changes to how it operates. However, many aspects are still quite similar to V1. Follow this migration guide to upgrade an application developed with V1 of the SDK to V2 with minimal fuss.

## Imports

The V2 SDK has a flatter code structure. Everything of note previously found under `planet.api` is now available from the `planet` module. So, `import planet` should give you everything you need.

If you are migrating from V1, and are using the Data API filter builder (from `planet.api import filters`), we do recommend also including `from planet import data_filter as filters` in your imports for an easy migration from the old filter module to the new one.

## Authentication

If you have your API key stored in the `PL_API_KEY` environment variable you will be automatically authenticated to the V2 API, similar to how V1 worked. For other methods for authenticating against the V2 SDK, check out [Authenticate with the Planet server](quick-start-guide/#authenticate-with-the-planet-server).

## Session for all communication

In Version 2, sessions are used to manage all communication with the Planet APIs. This provides for multiple asynchronous connections. For each API, there is a specific client object. This client manages polling and downloading, along with any other capabilities provided by the API.

Each client now requires a `Session` object, which stores connection information and authentication and manages an HTTP connection pool.

The best way of doing this is wrapping any code that invokes a client class in a block like so:

```python
from planet import OrdersClient, Session

async with Session() as session:
    client = OrdersClient(session)
    result = await client.create_order(order)
# Process result
```

You will see this usage in the project’s tests and in the `planet.cli`
package. As a convenience, you may also get a service client instance from a
session’s `client()` method.

```python
async with Session() as session:
    client = session.client('orders')
    result = await client.create_order(order)
# Process result
```

For more information about Session, refer to the [Python SDK User Guide](../../python/sdk-guide/#session).

## Asynchronous Methods

With the V1 client, all communication was synchronous. Asynchronous bulk support was provided with the `downloader` module. There was no built-in support for polling when an order was ready to download or tracking when an order was downloaded.

In V2, all `*Client` methods (for example, `DataClient().search`, `OrderClient().create_order`) are asynchronous. Any functions that call such methods must include `async` in their definition. To invoke asynchronous methods from synchronous code, you can wrap the async method calls in `asyncio.run()`. The following is an example of using async with session.

```python
import asyncio
from datetime import datetime
from planet import Session
from planet import data_filter as filters
 
async def do_search():
    async with Session() as session:
        client = session.client('data')
        date_filter = filters.date_range_filter('acquired', gte=datetime.fromisoformat("2022-11-18"), lte=datetime.fromisoformat("2022-11-21"))
        cloud_filter = filters.range_filter('cloud_cover', lte=0.1)
        download_filter = filters.permission_filter()
        return [item async for item in client.search(["PSScene"], filters.and_filter([date_filter, cloud_filter, download_filter]))]
 
items = asyncio.run(do_search())
```

For more details on interacting with the asynchronous portions of the SDK, refer to the [Python SDK User Guide](../../python/sdk-guide/#session).

## Data API
The Data API portion of SDK V2 is quite similar to V1, although some filters have been renamed for consistency (also reference the note on imports):

* `date_range` to `date_range_filter`
* `geom_filter` to `geometry_filter`
* `and_filter` and `or_filter` now takes a list of filters instead of multiple arguments, so just wrap the contents in `[]` 
* `permissions_filter` is now split into `permissions_filter` and `asset_filter`, reflecting a recent change in API structure. If you were using this previously, you’ll want to convert the old `permissions_filter` into an `asset_filter` (this also involves changing the filter values, e.g. `assets.ortho_analytic_8b_sr:download` will become `ortho_analytic_8b_sr`) and adding an empty `permissions_filter`.

`filters.build_seach_request` no longer exists, and has instead been integrated into the replacement for `client.quick_seach`. For example:

```python
planet.api.ClientV1().quick_search(filters.build_search_request(all_filters, ["PSScene"]))
```

Is now

```python
async with Session() as session:
    items = [i async for i in session.client('data').search(["PSScene"], all_filters)]
```

## Orders API

The Orders API capabilities in V1 were quite primitive, but those that did exist have been retained in much the same form; `ClientV1().create_order` becomes `OrdersClient(session).create_order`. (As with the `DataClient`, you must also use `async` and `Session` with `OrdersClient`.)

Additionally, there is now also an order builder in `planet.order_request`, similar to the preexisting search filter builder. For more details on this, refer to the [Creating an Order](../../python/sdk-guide/#create-an-order).
