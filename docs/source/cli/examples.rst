Examples
========


Searching for Scenes
--------------------

Get latest 10 scenes::

    planet search --limit 10

Get scenes acquired recently::

    planet search --where acquired gt 2015-08-23

Additional criteria can be specified with multiple 3-part where clauses::

    planet search --where acquired gt 2015-08-23 --where acquired lt 2015-09-01

Get scenes that intersect a single point::

    planet search 'POINT(-105,40)'

Get scenes that intersect a geometry specified in a file named `aoi.geojson`::

    planet search aoi.geojson

Get latest 10 `landsat` scenes::

    planet search -s landsat --limit 10


Downloading Scenes
------------------

Download a ortho visual scene by ID to the current directory::

    planet download 20150810_235347_0b10

Download 2 `landsat` `qa` band scenes by ID to the `fetched` directory::

    planet download -d fetched -s landsat -product qa LC81300472015235LGN00 LC81300482015235LGN00


Integration With Other Tools
----------------------------

GitHub Gists
............

Create a `gist` using the `gist <http://defunkt.io/gist/>`_ command.

.. code-block:: bash

    # Search Planet's API for imagery acquired between June 17, 2015 and June 18, 2015
    planet search --where acquired gt 2015-06-17 --where acquired lt 2015-06-18 | gist -f planet-imagery-20150617-20150618.geojson

.. raw:: html

    <div style="margin-top:10px; margin-bottom:20px">
      <iframe class='ghmap' width="640" height="400" src="https://render.githubusercontent.com/view/geojson/?url=https%3A%2F%2Fgist.githubusercontent.com%2Fkapadia%2F6e722427cecd9ac79971%2Fraw%2Fhyperion-20150401-20150501.geojson#aa859151-d85a-414d-865c-9704fae891a1" frameborder="0"></iframe>
    </div>

    <script>
    window.onresize = function(e) {
      var mainEl = document.querySelector('#planet-cli');

      var mapElems = document.querySelectorAll('.ghmap');
      for (var i = 0; i < mapElems.length; i++) {
        mapElems[i].width = mainEl.clientWidth;
      }
    }

    window.onresize();
    </script>

Searching Using a Shapefile
...........................

Searching an area of interest described by a Shapefile, can be accomplished by chaining commands with `Fiona <https://github.com/Toblerity/Fiona>`_.

.. code-block:: bash

    $ fio dump santiago-de-chile.shp | planet search

Extracting Metadata Fields
..........................

Using `jq <http://stedolan.github.io/jq/>`_, useful information can be parsed from data returned by the Planet API.

.. code-block:: bash

    $ cat santiago-de-chile.geojson | planet search | jq -r ".features[].id"
    20150707_160055_090b
    20150707_160054_090b
    20150707_160053_090b
    20150707_160051_090b
    20150707_160050_090b
    20150707_160048_090b
    20150707_160047_090b
    20150707_160046_090b
    ...

Search Overlapping Imagery
..........................

Querying for Planet scenes that overlap another data source is easily accomplished by using `Rasterio <https://github.com/mapbox/rasterio>`_.

.. code-block:: bash

    $ rio bounds LC82210682015104LGN00_B1.TIF | planet search

Given that this Landsat scene was taken on April 14, 2015, it might be useful to search for Planet scenes that were taken in a similar timeframe.

.. code-block:: bash

    $ rio bounds LC82210682015104LGN00_B1.TIF | planet search --where acquired lt 2015-04-12 --where acquired gt 2015-04-14
