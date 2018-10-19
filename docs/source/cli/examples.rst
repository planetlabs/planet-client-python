.. highlight:: text

Examples
========

Get the latest 10 items from the API of any ItemType::

    planet data search --limit 10

Get recently acquired PSScene3Band ItemType records::

    planet data search --item-type PSScene3Band --date gt 2017-02-14

Item types can be specified case-insensitively, with prefix matching in the CLI::

    planet data search --item-type psscene --date gt 2017-02-14

Search for a month. Note: criteria are applied as an AND filter::

    planet data search --item-type PSScene3Band --date acquired gt 2017-02-14 --date acquired lt 2017-03-14

Use the geometry defined in `aoi.json` to constrain a search for both PSScene3Band and PSScene4Band::

    planet data search --item-type PSScene3Band --item-type PSScene4Band --geom aoi.json

Output a search filter to a file::

    planet data filter --range cloud_cover lt .1 --geom aoi.json > my-search.json

Create a saved search from a filter in a file with some additional options (this will output the search id for later use)::

    planet data create-search --item-type PSScene3Band --string-in satellite_id 0c12 --name my-search --filter-json my-search.json

Execute a saved search::

    planet data saved-search 4782d4118fee4275860665129a1e23c1

Get statistics using a filter from a file::

    planet data stats --item-type Sentinel2L1C --filter-json my-search.json

Activate and download the latest 3 PSScene3Band items to `images-download-directory`.

Note: this might take some time and directory must exist::

    planet data download --item-type PSScene3Band --limit 3 --dest images-download-directory

Mosaic Examples
---------------

List information for all mosaics you have access to::

    planet mosaics list

Note that you may want to parse the JSON that's output into a more human
readable format.  The cli does not directly provide options for this, but is
meant to be easily interoperable with other tools, e.g. `jq
<https://stedolan.github.io/jq/>`_.  For example, we could output just the name
and date range of each mosaic with::

    planet mosaics list | jq -r '.mosaics[] | [.name, .first_acquired, .last_acquired] | @tsv' 

Get basic information for a specific mosaic::

    planet mosaics info global_monthly_2018_09_mosaic

List the first 10 quads for a mosaic (Omitting the ``--limit`` option will
list all quads. Keep in mind that there may be millions for a global mosaic.)::

    planet mosaics search global_monthly_2018_09_mosaic --limit=10

Find all quads inside a particular area of interest::
    
    planet mosaics search global_monthly_2018_09_mosaic --rbox=-95.5,29.6,-95.3,29.8

Note that the format of ``--rbox`` is "xmin,ymin,xmax,ymax", so longitude comes
before latitude.

Get basic information (footprint, etc) for a particular mosaic quad::

    planet mosaics quad-info global_monthly_2018_09_mosaic 480-1200

Determine which scenes contributed to a particular mosaic quad::

    planet mosaics contribution global_monthly_2018_09_mosaic 480-1200

Download all quads for a mosaic (this is impractical for large mosaics, which
are hundreds of Terabytes in size)::

    planet mosaics download <mosaic_name>

Download all quads inside of a rectangular box for a mosaic::

    planet mosaics download global_monthly_2018_09_mosaic --rbox=-95.5,29.6,-95.3,29.8

Integration With Other Tools
----------------------------

The output of search results is valid GeoJSON so these can be piped into a file or tool.

Create a `gist` using the `gist <http://defunkt.io/gist/>`_ command::

    planet data search --item-type psscene --limit 100 | gist -f latest-scenes.geojson

Searching Using a Shapefile
...........................

Searching an area of interest described by a Shapefile, can be accomplished by chaining commands with `Fiona <https://github.com/Toblerity/Fiona>`_.::

    $ fio dump santiago-de-chile.shp | planet data search --item-type psscene --geom @-

Note: the `@-` value for `--geom` specifies reading from stdin

Extracting Metadata Fields
..........................

Using jq_, useful information can be parsed from data returned by the Planet API.

.. code-block:: bash

    $ planet data search --item-type psscene --limit 100 | jq -r ".features[].id"
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
Given that this Landsat scene was taken on April 14, 2015, it might be useful to search for Planet scenes that were taken in a similar timeframe.

.. code-block:: bash

    $ rio bounds LC82210682015104LGN00_B1.TIF | planet data search --item-type psscene --geom - --date acquired gt 2015-04-12 --date acquired lt 2015-04-14
