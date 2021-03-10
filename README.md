# Planet API Client

[![Build Status](https://travis-ci.org/planetlabs/planet-client-python.svg?branch=master)](https://travis-ci.org/planetlabs/planet-client-python)

Python client library and Command-Line Interface (CLI) for Planet's APIs.

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

Authentication information can be obtained and stored locally with the CLI
`planet init` command. Both the Python library and CLI will default to using
the stored authentication information, if available (not yet implemented, see
issues #244 and #248).

Additionally, authentication information can be provided to the CLI by
storing the api key in the environmental variable `PL_API_KEY` or by specifying
the api key with the flag `-k` or `--api-key` (TODO: link to cli documentation
here).

## Quick Start

### Python Library Usage

The client modules within the Python library are asynchronous, which greatly
speeds up many interactions with Planet's APIs. Support for asynchronous
development is native to Python 3.6+ via the
[`asyncio` module](https://docs.python.org/3/library/asyncio.html) and is
fairly easy to implement.

```python
import asyncio
import os
from planet.api import APlanetSession, AOrdersClient
from planet.api.order_details import OrderDetails, Product

API_KEY = os.getenv('PL_API_KEY')

image_ids = ['3949357_1454705_2020-12-01_241c']
order_details = OrderDetails(
    'test_order',
    [Product(image_ids, 'analytic', 'psorthotile')]
)

async def create_order(order_details):
    async with APlanetSession(auth=(API_KEY, '')) as ps:
        client = AOrdersClient(ps)
        return await client.create_order(order_details)

oid = asyncio.run(create_order(order_details))
print(oid)
```

Not into async? No problem. Just wrap the library and async operations together
and call from your synchronous code.

```python
def sync_create_order(order_details):
    return asyncio.run(create_order(order_details))

oid = sync_create_order(order_details)
print(oid)
```

Why async? Because things get *really cool* when you want to work with multiple
orders. Here's an example of submitting two orders, waiting for them to
complete, and downloading them. The orders each clip a set of images to a
specific area of interest (AOI), so they cannot be combined into one order.
(hint: [Planet Explorer](https://www.planet.com/explorer/) was used to define
the AOIs and get the image ids.)
 

```python
import asyncio
import os
from planet.api import APlanetSession, AOrdersClient
from planet.api.order_details import OrderDetails, Product, Tool

API_KEY = os.getenv('PL_API_KEY')

iowa_aoi = {
    "type": "Polygon",
    "coordinates": [[
        [-91.198465, 42.893071],
        [-91.121931, 42.893071],
        [-91.121931, 42.946205],
        [-91.198465, 42.946205],
        [-91.198465, 42.893071]]]
}

iowa_images = [
    '20200925_161029_69_2223',
    '20200925_161027_48_2223'
]
iowa_order = OrderDetails(
    'iowa_order',
    [Product(iowa_images, 'analytic', 'PSScene4Band')],
    tools=[Tool('clip', {'aoi': iowa_aoi})]
)

oregon_aoi = {
    "type": "Polygon",
    "coordinates": [[
        [-117.558734, 45.229745],
        [-117.452447, 45.229745],
        [-117.452447, 45.301865],
        [-117.558734, 45.301865],
        [-117.558734, 45.229745]]]
}

oregon_images = [
    '20200909_182525_1014',
    '20200909_182524_1014'
]
oregon_order = OrderDetails(
    'oregon_order',
    [Product(oregon_images, 'analytic', 'PSScene4Band')],
    tools=[Tool('clip', {'aoi': oregon_aoi})]
)


async def create_and_download(order_detail, client):
    oid = await client.create_order(order_detail)
    print(oid)
    state = await client.poll(oid, verbose=True)
    print(state)
    filenames = await client.download_order(oid, progress_bar=True)
    print(f'downloaded {oid}, {len(filenames)} files downloaded.')


async def main():
    async with APlanetSession(auth=(API_KEY, '')) as ps:
        client = AOrdersClient(ps)
        await asyncio.gather(
            create_and_download(iowa_order, client),
            create_and_download(oregon_order, client)
        )

asyncio.run(main())
```
[Example output](example_output.md)


## CLI Usage (Not yet Implemented)

**Hint:** autocompletion can be enabled in some shells using:
```console
    $ eval "$(_PLANET_COMPLETE=source planet)"
```

Basics and help:

```console
    $ planet --help
```

Specific API client usage:
```console
    $ planet data
```    

Specific command help:
```console
    $ planet data download --help
```

## Documentation

Online documentation:
https://planetlabs.github.io/planet-client-python/index.html

Documentation is also provided for download
[here](https://github.com/planetlabs/planet-client-python/releases/latest).

## Development

To contribute or develop with this library, see
[CONTRIBUTING](https://github.com/planetlabs/planet-client-python/CONTRIBUTING.md)
