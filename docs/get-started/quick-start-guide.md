---
title: Quick Start Guide
---

If you’re a Python developer, this Planet SDK for Python makes it easy to access Planet’s massive repository of satellite imagery and add Planet data to your data ops workflow.

If you’re not a Python developer, you can use the Command Line Interface (CLI) to get Planet data, and to process and analyze that data.

Take the following steps to install the SDK and connect with the Planet Server.

[TOC]

## Step 1: Install Python 3.7+ and a virtual environment

This is a Python package, so you’ll need to install Python (version 3.7 or greater), and setup and install a virtual environment.

Yes. Even if you’re not writing code—and only using the "no code" CLI part of the Planet SDK for Python—you’re using Python to communicate with the Planet Labs PBC servers. It’s not too tricky, but it does require a presence of mind to complete. If you need help with Python install and setting up a virtual environment, read [Virtual Environments and the Planet SDK for Python](venv-tutorial.md).

## Step 2: Install the Planet SDK for Python

Install the Planet SDK for Python using [pip](https://pip.pypa.io):

```console
$ pip install planet --pre --user
```

The [--user](https://pip.pypa.io/en/stable/user_guide/#user-installs) flag ensures the Python packages are installed relative to your user home folder. It is recommended for those new to pip.

## Step 3: Check the Planet SDK for Python version

```console
$ planet --version
```

You should be on some version 2 of the Planet SDK for Python.

## Step 4: Sign on to your account

Planet SDK for Python, like the Planet APIs, requires an account for use.

### Have your Planet account user name and password ready

To confirm your Planet account, or to get one if you don’t already have one, see [Get your Planet Account](get-your-planet-account.md).

### Authenticate with the Planet server

Just as you log in when you browse to https://account.planet.com, you’ll want to sign on to your account so you have access to your account and orders.

At a terminal console, type the following Planet command:

```console
$ planet auth init
```

You’ll be prompted for the email and password you use to access [your account](https://account.planet.com). When you type in your password, you won’t see any indication that the characters are being accepted. But when you hit enter, you’ll know that you’ve succeeded because you’ll see on the command line:

```console
Initialized
```

### Get your API key

Now that you've logged in, you can easily retrieve your API key that is being used for requests with the following command:

```console
planet auth value
```

Many `planet` calls you make require an API key. This is a very convenient way to quickly grab your API key.

## Step 5: Creating your first order

[*****TBW*****]

The Planet SDK for Python allows Python developers to write software that makes
use of the following Planet APIs:

* [orders](https://developers.planet.com/docs/orders/)
* [data](https://developers.planet.com/docs/data/)
* [subscriptions](https://developers.planet.com/docs/subscriptions/)
* [basemaps](https://developers.planet.com/docs/basemaps/), [tasking](https://developers.planet.com/docs/tasking/) and [analytics](https://developers.planet.com/docs/analytics/) API's are not yet implemented.

The client modules within the Python library are asynchronous, which greatly
speeds up many interactions with Planet’s APIs. Support for asynchronous
development is native to Python 3.6+ via the
[`asyncio` module](https://docs.python.org/3/library/asyncio.html). A great
resource for getting started with asynchronous programming in Python is
https://project-awesome.org/timofurrer/awesome-asyncio. The Writings and Talks
sections are particularly helpful in getting oriented.

Let’s start with creating an order with the Orders API:

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

