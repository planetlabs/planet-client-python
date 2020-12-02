Reference
=========

.. py:module:: planet.api

The public and stable API functions, classes and exceptions are all provided by the `planet.api` namespace.

The Orders Client Object
------------------------

The OrdersClient class is the supported way to access the Orders API.

This class includes functionality for all of the Orders API endpoints as well
as some additional functionality for managing the process of creating, polling,
and downloading an order.

For authorization, the Orders Client can be insantiated with the Planet API_KEY
or it can resolve the API_KEY from the operating system environment using the
`PL_API_KEY` value.

.. code-block:: python

   client = api.OrdersClient()

.. autoclass:: OrdersClient()
   :members:
