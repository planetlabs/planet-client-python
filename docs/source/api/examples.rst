Examples
========

Importing the API
-----------------

Everything needed is provided in the `api` module.

.. code-block:: python

    from planet import api

Creating a Client
-----------------

Without any arguments, the Client will look for an API_KEY using the operating system environment variable `PL_API_KEY`.

.. code-block:: python

    client = api.ClientV1()

Searching for Items
-------------------

A common case is searching for items in an AOI.

.. code-block:: python

    aoi = {
      "type": "Polygon",
      "coordinates": [
        [
          [-122.54, 37.81],
          [-122.38, 37.84],
          [-122.35, 37.71],
          [-122.53, 37.70],
          [-122.54, 37.81]
        ]
      ]
    }

    # build a filter for the AOI
    query = api.filters.and_filter(
      api.filters.geom_filter(aoi)
    )
    # we are requesting PlanetScope 4 Band imagery
    item_types = ['PSScene4Band']
    request = api.filters.build_search_request(query, item_types)
    # this will cause an exception if there are any API related errors
    results = client.quick_search(request)

    # items_iter returns an iterator over API response pages
    for item in results.items_iter(10):
      # each item is a GeoJSON feature
      sys.stdout.write('%s\n' % item['id'])
