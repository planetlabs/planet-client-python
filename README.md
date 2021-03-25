# Planet API Client

[![Build Status](https://travis-ci.org/planetlabs/planet-client-python.svg?branch=master)](https://travis-ci.org/planetlabs/planet-client-python)

Python client library for Planet's APIs.

The client provides access to the following Planet APIs:
* [analytics](https://developers.planet.com/docs/analytics/)
* [basemaps](https://developers.planet.com/docs/basemaps/) (referred to in the client as `mosaics`) 
* [data](https://developers.planet.com/docs/data/)
* [orders](https://developers.planet.com/docs/orders/)

## Installation

### Prerequisites

* Python version 3.7+

### Install package

```console
$ pip install planet
```

The [--user](https://pip.pypa.io/en/stable/user_guide/#user-installs)
flag is highly recommended for those new to [pip](https://pip.pypa.io).

A PEX executable (Windows not supported) and source releases are
[here](https://github.com/planetlabs/planet-client-python/releases/latest).

## Authentication

Planet's APIs require an account for use.
[Sign up here](https://www.planet.com/explorer/?signup).


## Quick Start

The client modules within the Python library are asynchronous, which greatly
speeds up many interactions with Planet's APIs. Support for asynchronous
development is native to Python 3.6+ via the
[`asyncio` module](https://docs.python.org/3/library/asyncio.html). A great
resource for getting started with asynchronous programming in Python is
https://project-awesome.org/timofurrer/awesome-asyncio. The Writings and Talks
sections are particularly helpful in getting oriented.

```python
>>> import asyncio
>>> import os
>>> import planet
>>>
>>> API_KEY = os.getenv('PL_API_KEY')
>>>
>>> image_ids = ['3949357_1454705_2020-12-01_241c']
>>> order_details = planet.OrderDetails(
...     'test_order',
...     [planet.Product(image_ids, 'analytic', 'psorthotile')]
... )
>>>
>>> async def create_order(order_details):
...     async with planet.Session(auth=(API_KEY, '')) as ps:
...         client = planet.OrdersClient(ps)
...         return await client.create_order(order_details)
>>>
>>> oid = asyncio.run(create_order(order_details))

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
please contribute to
[Determine need for synchronous support](https://github.com/planetlabs/planet-client-python/issues/251)

Why async? Because things get *really cool* when you want to work with multiple
orders. See [orders_multiple_orders.py](examples/orders_multiple_orders.py) for
an example of submitting two orders, waiting for them to complete, and
downloading them. The orders each clip a set of images to a specific area of
interest (AOI), so they cannot be combined into one order.
(hint: [Planet Explorer](https://www.planet.com/explorer/) was used to define
the AOIs and get the image ids.)
 
## Documentation

Online documentation:
https://planetlabs.github.io/planet-client-python/index.html

Documentation is also provided for download
[here](https://github.com/planetlabs/planet-client-python/releases/latest).

## Development

To contribute or develop with this library, see
[CONTRIBUTING](https://github.com/planetlabs/planet-client-python/CONTRIBUTING.md)
