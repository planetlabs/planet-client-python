Reference
=========

.. py:module:: planet.api

The public and stable API functions, classes and exceptions are all provided by the `planet.api` namespace.

The Client Object
-----------------

The Client class is the supported way to access the API.

Unless specific functionality is needed, the correct way to instantiate a Client is with zero arguments.

The Client will resolve the API_KEY from the operating system environment using the `PL_API_KEY` value.

.. code-block:: python

   client = api.ClientV1()

.. autoclass:: ClientV1()
   :members:


.. _api-search-request:

Client Search Requests
----------------------

The general search request form is a Python dict, for example.

.. code-block:: javascript

  {
    "item_types": ['PSScene3Band'],
    "filter": {
      "type": "AndFilter",
      "config": [
        "type": "RangeFilter",
        "field_name": "cloud_cover",
        "config": {
          "lte": 0.5
        }
      ]
    }
  }

The ``stats`` function requires an additional ``interval`` property in the
request body.

When creating a saved search, the ``name`` property in the request body will
be used to give the new search a name.

.. note:: Request and Filter logic is not validated on the client.

Filters
-------

The filters module provides a small convenience layer for building filters
and requests.

.. automodule:: planet.api.filters
   :members:



Client Return Values
--------------------

.. py:module:: planet.api.models

Most `Client` methods return a :py:class:`Body` subclass that provides access to the HTTP response body in addition to the HTTP request and response details.

For many responses, it is sufficient to use the `get` method to obtain the HTTP response as JSON.

For paginated responses, the :py:class:`Paged` provides convenience functions to explicitly page through results as well as an iterator to the underlying items in each response.

Download functions return a :py:class:`Response` object that handles some aspects of asynchronous execution. Namely, streaming chunks to a handler to prevent memory issues and awaiting completion of the task.

The basic `Body` methods include:

.. autoclass:: Body()
   :members:
   :exclude-members: __init__

The `Response` class returned by download functions has two methods:

.. autoclass:: Response()
   :members:
   :exclude-members: __init__

Most responses are more specific than a body. The JSON body provides the contents as JSON.

.. autoclass:: JSON()
   :members:

Paginated responses provide a paging iterator as well as an iterator of each pages contents.

The :py:meth:`Paged.items_iter` method provides iteration over the contents of each page response.

For examples, an :py:class:`Items` response page contains a FeatureCollection of zero or more Item objects.
Each Item is a record represented as a GeoJSON feature with properties describing it's metadata.
When using the `iterator` from the :py:meth:`Paged.items_iter` method, only Item Feature objects will be returned.

To handle assembling the items from each page into a collection again and streaming them as JSON, use the :py:meth:`Paged.json_encode` method.

.. autoclass:: Paged()
   :members:

.. py:class:: Items()

   Items is a Body that contains a FeatureCollection so when using `items_iter`, it will yield `Feature` GeoJSON objects.

.. py:class:: Searches()

   Searches is a Body that contains an array of searches, so when using `items_iter`, it will yield `Search` JSON objects.


Utilities
---------

.. autofunction:: planet.api.write_to_file


Activating and Downloading Many Assets
--------------------------------------

A common use case is to activate and download the results of a search. While
the Client provides the lower-level functionality for this, the `Downloader`
class provides convenience for managing this process for a large number of
items and assets.

Create a downloader using:

.. autofunction:: planet.api.downloader.create

.. autoclass:: planet.api.downloader.Downloader
   :members:


Client Exceptions
-----------------

In addition to other exceptions, expected or otherwise, each HTTP operation has
the potential to raise one of the following exceptions:

.. automodule:: planet.api.exceptions
   :members:
