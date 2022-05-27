# Planet SDK for Python

[![Build Status](https://travis-ci.org/planetlabs/planet-client-python.svg?branch=master)](https://travis-ci.org/planetlabs/planet-client-python)

[Planet](https://planet.com) Software Development Kit (SDK) for Python.

## Versions and Stability

The default branch (main) of this repo is for the [Planet SDK for 
Python](https://github.com/planetlabs/planet-client-python/projects/2),
a complete rewrite and upgrade from the original [Planet Python 
Client](https://developers.planet.com/docs/pythonclient/). If you 
are looking for the source code to that library see the 
[v1](https://github.com/planetlabs/planet-client-python/tree/v1) branch.

The Planet SDK for Python is in 'pre-release' stages, working towards an 
initial release around July. Active development is tracked in the [Planet SDK 
for Python Project](https://github.com/planetlabs/planet-client-python/projects/2). 
The initial release will support Orders, Data and Subscription API's in the 
command-line interface, with corresponding Python libraries. We expect 'beta' 
milestones to be released in some form for each of the API's. After the 
initial July release there will be additional work to support the remaining 
Planet API's ([analytics](https://developers.planet.com/docs/analytics/), 
[basemaps](https://developers.planet.com/docs/basemaps/) and 
[tasking](https://developers.planet.com/docs/tasking/)).

## Documentation

Full documentation is not yet hosted online but can be built and hosted locally
(see [CONTRIBUTING.md](CONTRIBUTING.md)) or can be read from source in the
`[docs](docs/)` directory.

## Quick Start

The Planet SDK includes both a Python API and a command-line interface (CLI)
to make use of the following Planet APIs:

* [orders](https://developers.planet.com/docs/orders/)
* [data](https://developers.planet.com/docs/data/) (not yet implemented)
* [subscriptions](https://developers.planet.com/docs/subscriptions/) (not 
 yet implemented)

This quickstart focuses on getting started with the CLI to place an order.
For information on the Python API see the 
[documentation](https://planet-sdk-for-python.readthedocs.io/en/latest/)

After you've installed the client, as explained in the [installation](#installation)
section below, you first must initialize the client with your Planet 
username and password:

```console
$ planet auth init
Email: <youremail@domain.com>
Password: 
Initialized
```

The email address and password you use should be the same as your login to 
[Planet Explorer](https://planet.com/explorer). The `auth init` command
will automatically get your API key and store it locally.

Now that you're initialized let's start with creating an order with the 
Orders API:

```console
$ planet orders create --name my-first-order --id <scene-ids> \ 
    --item-type PSScene --bundle visual
```

You should supply a unique name after `--name` for each new order, to help
you identify what oder. The `--id` is one or more scene ids (separated by
commas). These can be obtained from the data API, and you can also grab them
from any search in Planet Explorer. Just be sure the scene id matches the
[item-type](https://developers.planet.com/docs/apis/data/items-assets/#item-types) 
to get the right type of image. And then be sure to specify a 
[bundle](https://developers.planet.com/docs/orders/product-bundles-reference/).
The most common ones are `visual` and `analytic`. 

This will give you an order response JSON as shown in the 'example response' in
[the Order API docs](https://developers.planet.com/docs/orders/ordering/#basic-ordering). 
You can grab the `id` from that response, which will look something like 
`dfdf3088-73a2-478c-a8f6-1bad1c09fa09`. You can then use that order-id in a 
single command  to wait for the order and download it when you are ready:

```console
$ planet orders wait <order-id> && planet orders download <order-id>
```

This usually takes at least a few minutes, and can be longer if it is a large request
(lots of items or big items like SkySatCollect). The default `wait` will last about
15 minutes, but can easily be extended with the `--max-attempts` option.

You can also just wait to download until the order is fulfilled. To check on its status
just use: 

```console
$ planet orders get <id>
```

And then use `planet download <id>` when the order is ready. 

There are many more options in the command-line interface. One of the best ways
to explore is to just use `--help` after any command to see the options. There is
also lots of good information in the docs, in the 
[User Guide](https://planet-sdk-for-python.readthedocs.io/en/latest/guide/#cli)
and the [CLI Reference](https://planet-sdk-for-python.readthedocs.io/en/latest/cli/).

## Installation

This repository is not yet available on PyPi or any other distribution channels. To 
install you must [clone this repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
to your local computer. After you have the repo local just navigate to the root
directory.

Then you can install locally with [pip](https://pip.pypa.io):

```console
$ python -m pip install . 
```

The [--user](https://pip.pypa.io/en/stable/user_guide/#user-installs)
flag is highly recommended for those new to pip.

The Planet SDK for Python requires Python 3.7+.

After installation you should be able to use the command-line interface. Just type
`planet` into the command-line and the usage and options should appear. If it doesn't 
work don't hesitate to ask for help in the [discussions](https://github.com/planetlabs/planet-client-python/discussions/categories/q-a)

## Authentication

Planet's APIs require an account for use.
[Sign up here](https://www.planet.com/explorer/?signup).

## Development

To contribute or develop with this library, see
[CONTRIBUTING.md](CONTRIBUTING.md).
