---
title: Upgrade from Version 1 to Version 2
---

The Planet SDK for Python is Version 2 of what was previously referred to as the Planet API client. This V2 is a major update of the V1 SDK. As such, there are major structural changes to how it operates. However, many aspects are still quite similar to V1. Follow this migration guide to upgrade an application developed with v1 of the SDK to V2 with minimal fuss.

## Imports

The V2 SDK has a flatter code structure. Everything of note previously found under `planet.api` is now available from the `planet` module. So, `import planet` should give you everything you need.

If you are migrating from V1, and were using the Data API filter builder (from `planet.api import filters`), we do recommend also including `from planet import data_filter as filters` in your imports for an easy migration from the old filter module to the new one.

## Authentication

In Version 1, a single client was created for all APIs,
`client=api.ClientV1(api_key=API_KEY)`. To authenticate automatically in V2, use an API key stored in the `PL_API_KEY` environment variable by adding `planet.Auth.from_env(`PL_API_KEY`).write()` to the first line of your script. For other methods for authenticating against the SDK, check out [Authenticate with the Planet server](quick-start-guide/#authenticate-with-the-planet-server).

## Session for all communication

In Version 2, sessions are used to manage all communication with the Planet APIs. This provides for multiple asynchronous connections. An API-specific client is created. This client manages polling and downloading, along with any other capabilities provided by the API.

Each client now requires a `Session` object, which stores connection information and authentication.

The best way of doing this is wrapping any code that invokes a client class in a block like so:

```python
async with Session() as session:
        client = OrdersClient(session)
        result = await client.create_order(order)
# Process result
```

For more information about Session, refer to the [SDK user guide](../../python/sdk-guide/#session).

# Asynchronous Methods

With the V1 client, all commumication was synchronous. Asynchronous bulk support was provided with the `downloader` module. There was no built-in support for polling when an order was ready to download or tracking when an order was downloaded.

In V2, all `*Client` methods (for example, `DataClient().quick_search`, `OrderClient().create_order`) are asynchronous. Any functions that call such methods must include `async` in their definition. To invoke asynchronous methods from synchronous code, you can wrap the async method calls in `asyncio.run()`.

For more details on interacting with the asynchronous portions of the SDK, refer to the [SDK user guide](../../python/sdk-guide/#session).

# Data API
The Data API portion of SDK V2 is quite similar to V1, although some filters have been renamed for consistency (also reference the note on imports):

* `date_range` to `date_range_filter`
* `geom_filter` to `geometry_filter`
* `and_filter` and `or_filter` now takes a list of filters instead of multiple arguments, so just wrap the contents in `[]` 
* `permissions_filter` is now split into `permissions_filter` and `asset_filter`, reflecting a recent change in API structure. If you were using this previously, you’ll want to convert the old `permissions_filter` into an `asset_filter` (this also involves changing the filter values, e.g. `assets.ortho_analytic_8b_sr:download` will become `ortho_analytic_8b_sr`) and adding an empty `permissions_filter`.

`filters.build_seach_request` no longer exists, and has instead been integrated into the replacement for `client.quick_seach`. For example:

```console
planet.api.ClientV1().quick_search(filters.build_search_request(all_filters, ["PSScene"]))
```

Is now

```console
async with Session() as session: 
planet.DataClient(session).quick_search(["PSScene"], all_filters)
```

# Orders API

The Orders API capabilities in V1 were quite primitive, but those that did exist have been retained in much the same form; `ClientV1().create_order` becomes `OrderClient(session).create_order`. (As with the `DataClient`, you must also use `async` and `Session` with `OrderClient`.)

Additionally, there is now also an order builder in `planet.order_request`, similar to the preexisting search filter builder. For more details on this, refer to the [Creating an Order](../../python/sdk-guide/#creating-an-order).
