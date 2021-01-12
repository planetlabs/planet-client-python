Examples
========

Importing the API
-----------------

Everything needed is provided in the `api` module.

.. code-block:: python

    from planet import api

Creating a Client
-----------------

Without any arguments, the Orders Client will look for an API_KEY using the
operating system environment variable `PL_API_KEY`.

.. code-block:: python

    client = api.OrdersClient()
