.. highlight:: text

Examples
========

Get the latest 10 items from the API of any ItemType::

    planet quick-search --limit 10

Get recently acquired PSScene3Band ItemType records::

    planet quick-search --item-type PSScene3Band --date gt 2017-02-14

Search for a month. Note: criteria are applied as an AND filter::

    planet quick-search --item-type PSScene3Band --date gt 2017-02-14 --date lt 2017-03-14

Use the geometry defined in `aoi.json` to constrain a search for both PSScene3Band and PSScene4Band::

    planet quick-search --item-type PSScene3Band --item-type PSScene4Band --geom aoi.json

Output a search filter to a file::

    planet filter --range cloud_cover lt .1 --geom aoi.json > my-search.json

Create a saved search from a filter in a file with some additional options::

    planet create-search --item-type PSScene3Band --string-in satellite_id 0c12 --name my-search --filter-json my-search.json

Execute a saved search::

    planet saved-search 4782d4118fee4275860665129a1e23c1

Get statistics using a filter from a file::

    planet stats --item-type Sentinel2L1C --filter-json my-search.json

Activate and download the latest 3 PSScene3Band items to `images-download-directory`.

Note: this might take some time and directory must exist::

    planet download --item-type PSScene3Band --limit 3 --dest images-download-directory


Integration With Other Tools
----------------------------

TODO THESE NEED UPDATING

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
