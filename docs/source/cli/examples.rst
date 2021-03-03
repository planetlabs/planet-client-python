.. highlight:: text

Examples
========

Data Examples
-------------

Get the latest 10 items from the API of any ItemType::

    planet data search --limit 10

Get recently acquired PSScene3Band ItemType records::

    planet data search --item-type PSScene3Band --date acquired gt 2017-02-14

Item types can be specified case-insensitively, with glob matching in the CLI::

    planet data search --item-type psscene* --date acquired gt 2017-02-14

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

    planet mosaics search global_monthly_2018_09_mosaic --bbox=-95.5,29.6,-95.3,29.8

Note that the format of ``--bbox`` is "xmin,ymin,xmax,ymax", so longitude comes
before latitude.

Get basic information (footprint, etc) for a particular mosaic quad::

    planet mosaics quad-info global_monthly_2018_09_mosaic 480-1200

Determine which scenes contributed to a particular mosaic quad::

    planet mosaics contribution global_monthly_2018_09_mosaic 480-1200

Download all quads for a mosaic (this is impractical for large mosaics, which
are hundreds of Terabytes in size)::

    planet mosaics download <mosaic_name>

Download all quads inside of a rectangular box for a mosaic::

    planet mosaics download global_monthly_2018_09_mosaic --bbox=-95.5,29.6,-95.3,29.8

Get information about a mosaic series::

    planet mosaics series describe <series_id>

Get list of mosaics in a mosaic series::

    planet mosaics series list-mosaics <series_id>

Analytics Examples
------------------
These examples assume that the reader is already familiar with the `Analytics User Guide`_.

.. This User Guide will be moved to the Dev Center in the near future.
.. _`Analytics User Guide`: https://docs.google.com/document/d/1-ZgGIFKb9IxxVMjTb603lRd6pwEygcri5rKxcsEjk8E/

List information for all feeds, subscriptions, or collections you have access to::

    planet analytics feeds list
    planet analytics subscriptions list
    planet analytics collections list

Note that you may want to parse the JSON that's output into a more human
readable format.  The cli does not directly provide options for this, but is
meant to be easily interoperable with other tools, e.g. `jq
<https://stedolan.github.io/jq/>`_.  For example, for feeds we may be interested in the ID,
description, and the target and source mosaics (if applicable)::

    planet analytics feeds list | jq -r '.data[] | [.id, .description, .created, .source.config.series_id, .target.config.series_id]'

The ID, description, source feed ID, and the created date are useful for a subscription::

    planet analytics subscriptions list | jq -r '.data[] | [.id, .feedID, .created]'

Get the first 10 subscriptions for a feed::

    planet analytics subscriptions list --feed-id <feed-id> --limit 10

Get information about a particular feed, subscription, or collection::

    planet analytics feeds describe <feed_id>
    planet analytics subscriptions describe <subscription_id>
    planet analytics collections describe <collection_id or subscription_id>

List all mosaics associated with a feed, subscription, or collection (if the feed is mosaics-based only)::

    planet analytics feeds list-mosaics <feed_id>
    planet analytics subscriptions list-mosaics <subscription_id>
    planet analytics collections list-mosaics <collection_id or subscription_id>

Features (GeoJSON results) for a collection can be requested in one of two ways. The `list` option
will only return slices of results (defaults to 100 at a time), whereas `list-all` will stream
features until all features have been retrieved. Both options accept the same additional filters.

    planet analytics collections features list <collection_id or subscription_id>
    planet analytics collections features list-all <collection_id or subscription_id>

To page through results when using `list`::

    planet analytics collections features list <collection_id or subscription_id>
    planet analytics collections features list <collection_id or subscription_id> --before <feature_id_of_last_feature_in_previous_page>

Get the 10 most recent features (GeoJSON results) for a collection::

    planet analytics collections features list <collection_id or subscription_id> --limit 10

Stream all features (GeoJSON results) since last seen feature::

    planet analytics collections features list-all <collection_id or subscription_id> --after <feature_id>

Get features (GeoJSON results) for a collection within a certain time range::

    planet analytics collections features list <collection_id or subscription_id> --time-range 2019-01-01T00:00:00.00Z/2019-02-01T00:00:00.00Z
    planet analytics collections features list-all <collection_id or subscription_id> --time-range 2019-01-01T00:00:00.00Z/2019-02-01T00:00:00.00Z

Get features (GeoJSON results) for a collection within a certain area::

    planet analytics collections features list <collection_id or subscription_id> --bbox 122.3,47.6,122.4,47.7
    planet analytics collections features list-all <collection_id or subscription_id> --bbox 122.3,47.6,122.4,47.7

It is also possible to get resources associated with a particular GeoJSON feature in a collection.
Just as different feeds are based upon different imagery types and produce different types of
output, each feed’s resources are varied:

* `source-quad`: Download the mosaic quad used to derive a feature, only available for collections associated with feeds that operate on mosaics
* `target-quad`: Download the mosaic quad that contains the raster output of a feed, only available for collections associated with feeds that output raster data
* `source-image-info`: Get the metadata for the source Planet product (ex. PSScene3Band) used to derive a feature, only available for non-mosaic feeds

Requesting a resource for a feature in a collection::

    planet analytics collections features get source-quad <collection_id or subscription_id> <feature_id>
    planet analytics collections features get target-quad <collection_id or subscription_id> <feature_id>
    planet analytics collections features get source-image-info <collection_id or subscription_id> <feature_id>

Orders Examples
-----------------

List all recent orders for the authenticated user::

    planet orders list

Get the status of a single order by Order ID::

    planet orders get <order ID>

Note that you may want to parse the JSON that's output into a more human
readable format.  The cli does not directly provide options for this, but is
meant to be easily interoperable with other tools, e.g. `jq
<https://stedolan.github.io/jq/>`_.

To cancel a running order by given order ID::

    planet orders cancel <order ID>

To download an order to your local machine::

    planet orders download <order ID>

Optionally, a `--dest <path to destination>` flag may be specified too.

Creating an Order
..................

The minimal command to create a simple order looks something like::

    planet orders create --name "my order" \
      --id 20151119_025740_0c74,20151119_025741_0c74 \
      --bundle visual --item-type psscene3band

If no toolchain or delivery details are specified, a basic order with download
delivery will be placed for the requested bundle including the item id(s) specified.

In the place of `--id`, you can insert a Data search string. This will populate
the list of IDs from a search. For example::

    planet orders create --name "my order" \
        --ids_from_search $'--item-type PSScene3Band --date acquired gt 2017-02-14 --date acquired lt 2017-03-14 --limit 6 --geom \'{
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {},
          "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [
                  -116.40701293945311,
                  43.061363052307875
                ],
                [
                  -116.4451217651367,
                  43.05032512283074
                ],
                [
                  -116.4320755004883,
                  43.017450433440814
                ],
                [
                  -116.37508392333984,
                  43.01092359150748
                ],
                [
                  -116.3393783569336,
                  43.03677585761058
                ],
                [
                  -116.35894775390624,
                  43.06186472916744
                ],
                [
                  -116.40701293945311,
                  43.061363052307875
                ]
              ]
            ]
          }
        }
      ]
    }\'' \
    --bundle visual \
    --item-type psscene3band \
    --zip bundle --email \
    --clip '{
        "type": "Polygon",
        "coordinates": [
          [
            [
              -116.40701293945311,
              43.061363052307875
            ],
            [
              -116.4451217651367,
              43.05032512283074
            ],
            [
              -116.4320755004883,
              43.017450433440814
            ],
            [
              -116.37508392333984,
              43.01092359150748
            ],
            [
              -116.3393783569336,
              43.03677585761058
            ],
            [
              -116.35894775390624,
              43.06186472916744
            ],
            [
              -116.40701293945311,
              43.061363052307875
            ]
          ]
        ]
      }'

Note that `--ids_from_search` is passed as a string value.

Additionally, optional toolchain & delivery details can be provided on the command line, e.g.::

    planet orders create --name "my order" \
      --id 20151119_025740_0c74,20151119_025741_0c74 \
      --bundle visual --item-type psscene3band --zip order --email

This places the same order as above, and will also provide a .zip archive
download link for the full order, as well as email notification. If you change
`--zip order` to `--zip bundle`, the individual bundles will be zipped rather
than the full order.

You can also clip the items in an order by providing a GeoJSON AOI Geometry
with the `--clip` parameter::

    planet orders create --name "my order" \
      --id 20151119_025740_0c74,20151119_025741_0c74 \
      --bundle visual --item-type psscene3band
      --clip '{
          "type": "Polygon",
          "coordinates": [
            [
              [
                -163.828125,
                -44.59046718130883
              ],
              [
                181.7578125,
                -44.59046718130883
              ],
              [
                181.7578125,
                78.42019327591201
              ],
              [
                -163.828125,
                78.42019327591201
              ],
              [
                -163.828125,
                -44.59046718130883
              ]
            ]
          ]
        }'

Alternatively, you can specify a file that contains your GeoJSON AOI using the
`@` notation, e.g. `--clip @path/to/aoi.json`.

It should be noted that if the clip AOI you specify does not intersect with the
items in `--id` or `--ids_from_search` you may end up with a zero result order.
If some of the items intersect, you will receive those items.

The Orders API allows you to specify a toolchain of operations to be performed
on your order prior to download. To read more about tools & toolchains, visit
`the docs <https://developers.planet.com/docs/orders/tools-toolchains/>`_ .

To add tool operations to your order, use the `--tools` option to specify a
json-formatted file containing an array (list) of the desired tools an their
settings.

.. note:: The json-formatted file must be formatted as an array (enclosed in square brackets), even if only specifying a single tool

For example, to apply the 3 tools `TOAR -> Reproject -> Tile` in sequence to an
order, you would create a `.json` file similar to the following::

    [
        {
          "toar": {
            "scale_factor": 10000
          }
        },
        {
          "reproject": {
            "projection": "WGS84",
            "kernel": "cubic"
          }
        },
        {
          "tile": {
            "tile_size": 1232,
            "origin_x": -180,
            "origin_y": -90,
            "pixel_size": 0.000027056277056,
            "name_template": "C1232_30_30_{tilex:04d}_{tiley:04d}"
          }
        }
    ]


Similarly, you can also specify cloud delivery options on an order create
command with the `--cloudconfig <path to json file>` option. In this case, the
json file should contain the required credentials for your desired cloud
storage destination, for example::

    {
          "amazon_s3":{
             "bucket":"foo-bucket",
             "aws_region":"us-east-2",
             "aws_access_key_id":"",
             "aws_secret_access_key":"",
             "path_prefix":""
          }

You can find complete documentation of Orders API cloud storage delivery and
required credentials `in the docs here
<https://developers.planet.com/docs/orders/ordering-delivery/#delivery-to-cloud-storage_1>`_.

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
