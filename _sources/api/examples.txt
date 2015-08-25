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

   client = api.Client()

Searching for Scenes
--------------------

Get the most recent Planet scenes.

.. code-block:: python

   body = client.get_scenes_list(scene_type='ortho')

Get the most recent Landsat scenes.

.. code-block:: python

   body = client.get_scenes_list(scene_type='landsat')

Providing metadata filters in a search.

.. code-block:: python

   filters = { 'sat.id.eq' : '090b'}
   body = client.get_scenes_list(scene_type='landsat', **filters)

Using an AOI (in WKT in this example) to search.

.. code-block:: python

   wkt = 'POINT(-100 40)'
   body = client.get_scenes_list(scene_type='landsat', intersection=wkt)

Handling a response `body` - the `get` method returns JSON (in this case, GeoJSON).

.. code-block:: python

   geojson = body.get()
   # the results are paginated and the total result set count is provided
   print '%s total results' % geojson['count']
   # loop over features and print the scene 'id'
   for f in geojson['features']:
       print f['id']

Downloading Scenes
------------------

One or more scenes may be downloaded using scenes ids. Downloading is currently
done asynchronously and a callback must be provided. The callback will execute
when data is available.

.. code-block:: python

   scene_ids = ['20150810_235346_0b10', '20150810_235345_0b10']
   # create a callback that will write scenes to the 'downloads' directory
   # note - the directory must exist!
   callback = api.write_to_file('downloads')
   bodies = client.fetch_scene_geotiffs(ids, callback=callback)
   # await the completion of the asynchronous downloads, this is where
   # any exception handling should be performed
   for b in bodies:
       b.await()
