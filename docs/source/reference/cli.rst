.. module:: planet.scripts

.. cli:

Planet CLI
==========

This library comes with a command line interface to expose many common requests, such as searching, downloading, and obtaining metadata.

Here's an example of what can be done using the cli and GitHub Gists.

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

The CLI can be used to rapidly search an area of interest (AOI). Suppose you have an AOI in GeoJSON format:

.. code-block:: bash

    $ cat santiago-de-chile.geojson | planet search
    {
      "count": 1135,
      "type": "FeatureCollection",
      "features": [
      ...
      ]
    }

Searching an area of interest described by a Shapefile, can be accomplished by chaining commands with `Fiona
<https://github.com/Toblerity/Fiona>`_.

.. code-block:: bash

    $ fio dump santiago-de-chile.shp | planet search

Using `jq
<http://stedolan.github.io/jq/>`_, useful information can be parsed from data returned by the Planet API.

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

Querying for Planet scenes that overlap another data source is easily accomplished by using `Rasterio
<https://github.com/mapbox/rasterio>`_.

.. code-block:: bash

    $ rio bounds LC82210682015104LGN00_B1.TIF | planet search

Given that this Landsat scene was taken on April 14, 2015, it might be useful to search for Planet scenes that were taken in a similar timeframe.

.. code-block:: bash

    $ rio bounds LC82210682015104LGN00_B1.TIF | planet search --where acquired lt 2015-04-12 --where acquired gt 2015-04-14
