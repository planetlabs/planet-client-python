---
title: Quick Start
---


## Step 1: Activate a virtual environment

This is a Python toolkit, so you'll need to install Python (version 3.7 or greater), and setup and install a virtual environment.

Yep. Even if you're not writing code—and only using the "no code" CLI part of the Toolkit—you're using Python to communicate with the Planet Labs PBC servers. It's not too tricky, but it does require a presence of mind to complete. If you need help with Python install and setting up a virtual environment, read [Getting started with venv & Planet SDK](venv-tutorial.md).

## Step 2: Install the Planet Earth Observation Toolkit

Install with [pip](https://pip.pypa.io):

```console
$ pip install planet --user
```

The [--user](https://pip.pypa.io/en/stable/user_guide/#user-installs)
flag is highly recommended for those new to pip.

## Step 3: Get your API Key ready

Planet's APIs require an account for use. For more information on where to find your API key, or to sign up to get one, see [Get Your API Key](get-your-api-key.md).

## Step 4: Check the toolkit version

```console
$ planet --version
```

You should be on some version 2 of the toolkit. If you're not, or you need more information about versioning, early access, and upgrading, see [Early Access to Planet SDK (aka "V2")](v2_earlyaccess.md).

## Step 5: Sign on to your account

Just as you log in when you browse to https://account.planet.com, you'll want to sign on to your account so you have access to your account and orders.

## Step 6: Use the Toolkit to authenticate against the Planet servers

```console
$ planet auth init
```

You'll be prompted for the email and password you use to access [your account](https://account.planet.com).

When you type in your password, you won't see any indication that the characters are being accepted. But when you hit enter, you'll know that you've succeeded because you'll see on the command line:

```console
Initialized
```

## Step 7: Creating your first order

[*****TBW*****]

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

