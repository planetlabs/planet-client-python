# Planet SDK for Python

[![Build Status](https://travis-ci.org/planetlabs/planet-client-python.svg?branch=master)](https://travis-ci.org/planetlabs/planet-client-python)

[Planet](https://planet.com) Software Development Kit (SDK) for Python.

## Documentation

Full documentation is not yet hosted online but can be built and hosted locally
(see [CONTRIBUTING.md](CONTRIBUTING.md)) or can be read from source in the
`docs` directory.

## Quick Start

The Planet SDK for Python allows Python developers to write software that makes
use of the following Planet APIs:

* [orders](https://developers.planet.com/docs/orders/)
* [data](https://developers.planet.com/docs/data/) (not implemented)
* [analytics](https://developers.planet.com/docs/analytics/) (not implemented)
* [basemaps](https://developers.planet.com/docs/basemaps/) (referred to in the client as `mosaics`) (not implemented)

The client modules within the Python library are asynchronous, which greatly
speeds up many interactions with Planet's APIs. Support for asynchronous
development is native to Python 3.6+ via the
[`asyncio` module](https://docs.python.org/3/library/asyncio.html). A great
resource for getting started with asynchronous programming in Python is
https://project-awesome.org/timofurrer/awesome-asyncio. The Writings and Talks
sections are particularly helpful in getting oriented.

Let's start with creating an order with the Orders API:

```python
>>> import asyncio
>>> import os
>>> import planet
>>>
>>> request = {
...   "name": "test_order",
...   "products": [
...     {
...       "item_ids": [
...         "3949357_1454705_2020-12-01_241c"
...       ],
...       "item_type": "PSOrthoTile",
...       "product_bundle": "analytic"
...     }
...   ]
... }
...
>>> async def create_order(request):
...     async with planet.Session() as ps:
...         client = planet.OrdersClient(ps)
...         return await client.create_order(request)
...
>>> oid = asyncio.run(create_order(request))

```

Not into async? No problem. Just wrap the library and async operations together
and call from your synchronous code.

```python
>>> def sync_create_order(order_details):
...     return asyncio.run(create_order(order_details))
>>>
>>> oid = sync_create_order(order_details)

```

When using `asyncio.run` to develop synchronous code with the async library,
keep in mind this excerpt from the
[asyncio.run](https://docs.python.org/3/library/asyncio-task.html#asyncio.run)
documentation:

"*This function always creates a new event loop and closes it at the end. It
should be used as a main entry point for asyncio programs, and should ideally
only be called once.*"

Do you have a use case where native synchronous support is essential? If so,
please contribute to this
[issue](https://github.com/planetlabs/planet-client-python/issues/251).

Why async? Because things get *really cool* when you want to work with multiple
orders. See [orders_create_and_download_multiple_orders.py](examples/orders_create_and_download_multiple_orders.py) for
an example of submitting two orders, waiting for them to complete, and
downloading them. The orders each clip a set of images to a specific area of
interest (AOI), so they cannot be combined into one order.
(hint: [Planet Explorer](https://www.planet.com/explorer/) was used to define
the AOIs and get the image ids.)

## Installation

Install with [pip](https://pip.pypa.io):

```console
$ python -m pip install . 
```

The [--user](https://pip.pypa.io/en/stable/user_guide/#user-installs)
flag is highly recommended for those new to pip.

The Planet SDK for Python requires Python 3.7+.

## Authentication

Planet's APIs require an account for use.
[Sign up here](https://www.planet.com/explorer/?signup).

## Development

To contribute or develop with this library, see
[CONTRIBUTING.md](CONTRIBUTING.md).
