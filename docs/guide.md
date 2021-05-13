# User Guide

## Session

Communication with the Planet services is provided with the `Session` class.
The recommended way to use a `Session` is as a context manager. This will
provide for automatic clean up of connections when the context is left.

```python
>>> import asyncio
>>> import os
>>> from planet import Session
>>>
>>> async def main():
...     async with Session() as sess:
...         # perform operations here
...         pass
...
>>> asyncio.run(main())

```

Alternatively, use `await Session.aclose()` to close a `Session` explicitly:

```python
>>> async def main():
...     sess = Session()
...     # perform operations here
...     await sess.aclose()
...
>>> asyncio.run(main())

```

## Authentication

There are two steps to managing authentication information, obtaining the
authentication information from Planet and then managing it for local retrieval
for authentication purposes.

The recommended method for obtaining authentication information is through
logging in, using `Auth.from_login()` (note: using something like the `getpass`
module is recommended to ensure your password remains secure). Alternatively,
the api key can be obtained directly from the Planet account site and then used
in `Auth.from_key()`.

Once the authentication information is obtained, the most convenient way of
managing it for local use is to write it to a secret file using `Auth.write()`.
It can also be accessed, e.g. to store in an environment variable, as
`Auth.value`.

For example, to obtain and store authentication information:

```python
>>> import getpass
>>> from planet import Auth
>>>
>>> pw = getpass.getpass()
>>> auth = Auth.from_login('user', 'pw')
>>> auth.write()

```

When a `Session` is created, by default, authentication is read from the
environment variable `PL_API_KEY`. If that variable is not set, then
authentication is read from the secret file created with `Auth.write()`.
This behavior can be modified by specifying Auth explicitely using the methods
`Auth.from_file()`, and `Auth.from_env()`. While `Auth.from_key()` and
`Auth.from_login` can be used, it is recommended that
those functions be used in authentication initialization and the authentication
information be stored in an environment variable or secret file.

The file and environment variable read from can be customized in the
respective functions. For example, authentication can be read from a custom
environment variable:

```python
>>> import asyncio
>>> import os
>>> from planet import Auth, Session
>>>
>>> auth = Auth.from_env('ALTERNATE_VAR')
>>> async def main():
...     async with Session(auth=auth) as sess:
...         # perform operations here
...         pass
...
>>> asyncio.run(main())

```

## Orders Client

The Orders Client mostly mirrors the
[Orders API](https://developers.planet.com/docs/orders/reference/#tag/Orders),
with the only difference being the addition of the ability to poll for when an
order is completed and to download an entire order.

```python
>>> from planet import OrdersClient
>>>
>>> async def main():
...     async with Session() as sess:
...         client = OrdersClient(sess)
...         # perform operations here
...
>>> asyncio.run(main())

```

### Creating an Order

When creating an order, the order details must be provided to the API. There
are two ways to specify the order details, a `JSON` blob and an `OrderDetails`
instance.

An `OrderDetails` instance is built up from instances of `Product`, `Tool`, 
`Delivery`, and `Notification` alongside other, simple parameters.

An example of creating an `OrderDetails` instance:

```python
>>> from planet.api.order_details import OrderDetails, Product
>>>
>>> image_ids = ['3949357_1454705_2020-12-01_241c']
>>> order_detail = OrderDetails(
...     'test_order',
...     [Product(image_ids, 'analytic', 'psorthotile')]
... )
...

```

The same thing, expressed as a `JSON` blob (pro tip: this can be obtained
with `order_detail.json`):

```python
>>> order_detail = {
...     'name': 'test_order',
...     'products': [{'item_ids': ['3949357_1454705_2020-12-01_241c'],
...                   'item_type': 'PSOrthoTile',
...                   'product_bundle': 'analytic'}],
... }

```

Once the order details are built up, creating an order is done within
the context of a `Session` with the `OrdersClient`:

```python
>>> async def main():
...     async with Session() as sess:
...         cl = OrdersClient(sess)
...         order_id = await cl.create_order(order_detail)
...
>>> asyncio.run(main())

```
