---
title: CLI for Orders API Tutorial
---

## Introduction

The `planet orders` command enables interaction with the [Orders API](https://developers.planet.com/apis/orders/),
which lets you activate and download Planet data products in bulk, and apply various 
'tools' to your processes. This tutorial takes you through all the main capabilities 
of the CLI for creating and downloading orders. It depends on several more advanced 
command-line concepts, but this tutorial should let you get a sense of what you can do, 
with enough examples that you should be able to adapt the commands for what you want to do. 
If you’re interested in deeper understanding what is going on
then check out our [CLI Concepts](cli-intro.md) guide.

## Core Workflows

### List Orders

You can use the `list` command to see details of existing orders. By default they will be sorted
by most recently created.

```sh
planet orders list
```

If you’ve not placed any orders with Explorer, the CLI or the API directly, then the results
of this call will be blank, so you may want to try out some of the create order commands below.

Sometimes that list gets too long, so you can put a limit on how many are returned using the
`--limit` parameter.

#### Formatting

You can also print the list of orders more nicely:

```sh
planet orders list --pretty
```

The `--pretty` flag is built into most Planet CLI commands, and it formats the JSON to be
more readable.

You can also use `jq`, a powerful command-line JSON-processing tool, that is mentioned in 
the [CLI introduction]((cli-intro.md#jq).

```sh
planet orders list | jq
```

Piping any output through jq will format it nicely and do syntax highlighting. You can 
also `jq` to just show select information, which can be useful for getting a quick sense 
of the state of the state of things and pull out id’s for other operations:

```sh
planet orders list | jq -rs '.[] | "\(.id) \(.created_on) \(.state) \(.name)"'
```

You can customize which fields you want to show by changing the values.

A list of your orders can also be viewed in a UI at https://www.planet.com/account/#/orders

#### Number of existing orders

You can use `jq` to process the output for more insight, like get a count of how many existing
orders you have. Orders are automatically deleted 90 days after completion, so this number
roughly is equivalent to the number of orders created in the last 90 days.

```sh
planet orders list | jq -s length
```

This uses `-s` to collect the output into a single array, and `length` then tells the
length of the array.

#### Filtering

The `list` command supports filtering on a variety of fields:
* `--state`: Filter by order state. Options include `queued`, `failed`, `success`, `partial` and `cancelled`.
* `--source-type`: Filter by source type. Options include `scenes`, `basemaps`, or `all`. The default is `all`.
* `--name`: Filter by name.
* `--name-contains`: Only return orders with a name that contains the provided string.
* `--created-on`: Filter on the order creation time or an interval of creation times.
* `--last-modified`: Filter on the order's last modified time or an interval of last modified times.
* `--hosting`: Filter on orders containing a hosting location (e.g. SentinelHub). Accepted values are `true` or `false`.

Datetime args (`--created-on` and `--last-modified`) can either be a date-time or an interval, open or closed. Date and time expressions adhere to RFC 3339. Open intervals are expressed using double-dots.
* A date-time: `2018-02-12T23:20:50Z`
* A closed interval: `2018-02-12T00:00:00Z/2018-03-18T12:31:12Z`
* Open intervals: `2018-02-12T00:00:00Z/..` or `../2018-03-18T12:31:12Z`

To list orders in progress:
```sh
planet orders list --state running
```

To list orders with the `scenes` source type:
```sh
planet orders list --source-type scenes
```

To list orders that were created in 2024:
```sh
planet orders list --created-on 2024-01-01T00:00:00Z/2025-01-01T00:00:00Z
```

To list orders with a hosting location:
```sh
planet orders list --hosting true
```

To list orders with the name `my location xyz`:
```sh
planet orders list --name "my location xyz"
```

To list orders with a name containing `xyz`:
```sh
planet orders list --name-contains xyz
```

#### Sorting

The `list` command also supports sorting the orders on one or more fields: `name`, `created_on`, `state`, and `last_modified`. The sort direction can be specified by appending ` ASC` or ` DESC` to the field name (default is ascending).

When multiple fields are specified, the sort order is applied in the order the fields are listed.

Sorting examples:
* `--sort-by name`: sorts orders by name alphabetically.
* `--sort-by "created_on DESC"`: sorts orders by most recently created.
* `--sort-by "last_modified DESC"`: sorts subscriptions by most recently modified.
* `--sort-by "state ASC"`: sorts orders by state alphabetically.
* `--sort-by "name,last_modified DESC"`: sorts subscriptions by name first, and most recently modified second.

### Info on an Order

For a bit more information about an order, including the location of any downloads, use
the `get` command, using the order id.

```sh
planet orders get 782b414e-4e34-4f31-86f4-5b757bd062d7
```

### Create an Order Request

To create an order you need a name, a [bundle](https://developers.planet.com/apis/orders/product-bundles-reference/),
 one or more id’s, and an [item type](https://developers.planet.com/docs/apis/data/items-assets/#item-types):

First lets get the ID of an item you have download access to, using the Data API: 

```sh
planet data filter | planet data search PSScene --limit 1 --filter - | jq -r .id 
```

If you don't have access to PlanetScope data then replace PSScene with SkySatCollect.
Then make the following call:

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'My First Order' \
    20220605_124027_64_242b
```

Running the above command should output the JSON needed to create an order:

```json
{"name": "My First Order", "products": [{"item_ids": ["20220605_124027_64_242b"], "item_type": "PSScene", "product_bundle": "analytic_sr_udm2"}], "metadata": {"stac": {}}}
```

You can also use `jq` here to make it a bit more readable:

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'My First Order' \
    20220605_124027_64_242b \
    | jq
```

```json
{
  "name": "My First Order",
  "products": [
    {
      "item_ids": [
        "20220605_124027_64_242b"
      ],
      "item_type": "PSScene",
      "product_bundle": "analytic_sr_udm2"
    }
  ],
  "metadata": {
    "stac": {}
  }
}
```

#### Zip archives of bundles and orders

You can request that all files of a bundle be zipped together by using the `--archive-type` option. The only type of archive currently available is "zip".

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'My First Zipped Order' \
    --archive-type zip \
    20220605_124027_64_242b
```

You can request that all files of the entire order be zipped together by using the `--single-archive` option.

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'My First Zipped Order' \
    --archive-type zip \
    --single-archive \
    20220605_124027_64_242b,20220605_124025_34_242b
```

*New in version 2.1*

#### Sentinel Hub Hosting

You can deliver your orders directly to Sentinel Hub using the hosting options.

```
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'My First Order' \
    20220605_124027_64_242b \
    --hosting sentinel_hub \
    --collection_id ba8f7274-aacc-425e-8a38-e21517bfbeff
```

- The --hosting option is optional and currently supports sentinel_hub as its only value.
- The --collection_id is also optional. If you decide to use this, ensure that the order request and the collection have matching bands. If you're unsure, allow the system to create a new collection for you by omitting the --collection_id option. This will ensure the newly set-up collection is configured correctly, and you can subsequently add items to this collection as needed.

For more information on Sentinel Hub hosting, see the [Orders API documentation](https://developers.planet.com/apis/orders/delivery/#delivery-to-sentinel-hub-collection) and the [Linking Planet User to Sentinel Hub User
](https://support.planet.com/hc/en-us/articles/16550358397469-Linking-Planet-User-to-Sentinel-Hub-User) support post.

### Save an Order Request

The above command just prints out the necessary JSON to create an order. To actually use it you can
save the output into a file:

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name "My First Order" \
    20220605_124027_64_242b \
    > request-1.json
```

Note that `\` just tells the command-line to treat the next line as the same one. It’s used here so it’s 
easier to read, but you can still copy and paste the full line into your command-line and it should work.

This saves the above JSON in a file called `request-1.json`

### Create an Order

From there you can create the order with the request you just saved: 

```sh
planet orders create request-1.json
```

The output of that command is the JSON returned from the server, that reports the status:

```json
{
  "_links": {
    "_self": "https://api.planet.com/compute/ops/orders/v2/2887c43b-26be-4bec-8efe-cb9e94f0ef3d"
  },
  "created_on": "2022-11-29T22:49:24.478Z",
  "error_hints": [],
  "id": "2887c43b-26be-4bec-8efe-cb9e94f0ef3d",
  "last_message": "Preparing order",
  "last_modified": "2022-11-29T22:49:24.478Z",
  "metadata": {
    "stac": {}
  },
  "name": "My First Order",
  "products": [
    {
      "item_ids": [
        "20220605_124027_64_242b"
      ],
      "item_type": "PSScene",
      "product_bundle": "analytic_sr_udm2"
    }
  ],
  "state": "queued"
}
```

Note the default output will be a bit more 'flat' - if you'd like the above formatting in your
command-line just use `jq` as above: `planet orders create request-1.json | jq` (but remember
if you run that command again it will create a second order).

#### Sentinel Hub Hosting

For convenience, `planet orders create` accepts the same `--hosting` and `--collection_id` options that [`planet orders request`](#sentinel-hub-hosting) does.

```sh
planet orders create request-1.json \
    --hosting sentinel_hub \
    --collection_id ba8f7274-aacc-425e-8a38-e21517bfbeff
```

### Create Request and Order in One Call

Using a unix command called a 'pipe', which looks like `|`, you can skip the step of saving to disk,
passing the output of the `orders request` command directly to be the input of the `orders create`
command:

```sh
planet orders request --item-type PSScene --bundle analytic_sr_udm2 --name 'Two Item Order' \
20220605_124027_64_242b,20220605_124025_34_242b | planet orders create -
```

The Planet CLI is designed to work well with piping, as it aims at small commands that can be 
combined in powerful ways, so you’ll see it used in a number of the examples.

### Download an order

To download all files in an order you use the `download` command:

```sh
planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30
```

Note this only works when the order is ready for download. To do that you can
keep running `orders get` until the `state` is `success`. Or for a better
way see the next example.

### Wait then download an order

The `wait` command is a small, dedicated command that polls the server to 
see if an order is ready for downloading, showing the status. It’s not
so useful by itself, but can be combined with the `download` command to
only start the download once the order is ready:

```sh
planet orders wait 65df4eb0-e416-4243-a4d2-38afcf382c30 \
&& planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30 
```

This uses the logical AND operator (`&&`) to say "don't run the second command
until the first is done".

### Save order ID

You can also use a unix variable to store the order id of your most recently placed order, 
and then use that for the wait and download commands:

```sh
orderid=$(planet orders list --limit 1 | jq -r .id)
planet orders wait $orderid
planet orders download $orderid
```

This can be nicer than copying and pasting it in.

You could also save the id right when you place the order:

```sh
orderid=`planet orders create request-1.json | jq -r .id`
```

To check the current value of `orderid` just run `echo $orderid`.

### Create an order and download when ready

You can then combine these all into one call, to create the order and
download it when it’s available:

```sh
id=`planet orders create request-1.json | jq -r '.id'` && \
    planet orders wait $id && planet orders download $id
```

### Download to a different directory

You can use the `--directory` flag to save the output to a specific directory. This
call saves it to a directory called `psscene`, at whatever location you are at
currently:

```sh
mkdir psscene
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --directory psscene
```

You can also specify absolute directories (in this case to my desktop):

```sh
planet orders download \
    782b414e-4e34-4f31-86f4-5b757bd062d7 \
    --directory /Users/cholmes/Desktop/
```

### Verify checksum

The `--checksum` command will do an extra step to make sure the file you got 
wasn't corrupted along the way (during download, etc). It checks that the bytes
downloaded are the same as the ones on the server. By default it doesn't show
anything if the checksums match.

```sh
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --checksum MD5
```

This command isn't often necessary in single download commands, but is quite 
useful if you are downloading thousands of files with a script, as the likelihood 
of at least one being corrupted in creases

## Tools with orders

Now we’ll dive into the variety of ways to customize your order. These can all be
combined with all the commands listed above.

### Clipping

The most used tool is the `clip` operation, which lets you pass a geometry to the
Orders API and it creates new images that only have pixels within the geometry you
gave it. The file given with the `--clip` option should contain valid [GeoJSON](https://geojson.org/).
It can be a Polygon geometry, a Feature, or a FeatureClass. If it is a FeatureClass,
only the first Feature is used for the clip geometry.

Example: `geometry.geojson`
```
{
    "geometry":
    {
        "type": "Polygon",
        "coordinates":
        [
            [
                [
                    -48.4974827,
                    -1.4967008
                ],
                [
                    -48.4225714,
                    -1.4702869
                ],
                [
                    -48.3998028,
                    -1.4756259
                ],
                [
                    -48.4146752,
                    -1.49898376
                ],
                [
                    -48.4737304,
                    -1.5277508
                ],
                [
                    -48.4974827,
                    -1.4967008
                ]
            ]
        ]
    }
}
```

We’ll work with a geojson that is already saved. You should download the 
[geometry](https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/cli/request-json/geometry.geojson)
(and you can see it [on github](https://github.com/planetlabs/planet-client-python/blob/main/docs/cli/request-json/geometry.geojson)
or it is also stored in the repo in the [request-json/](request-json/) directory. 

You can move that geometry to your current directory and use the following command, or
tweak the geometry.geojson to refer to where you downloaded it.

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --clip geometry.geojson \
    --name clipped-geom \
    20220605_124027_64_242b \
    | planet orders create -
```

### Additional Tools

Since clip is so heavily used it has its own dedicated command in the CLI. All
the other tools use the `--tools` option, that points to a file. The file should 
contain JSON that follows the format for a toolchain, the "tools" section of an order. 
The toolchain options and format are given in
[Creating Toolchains](https://developers.planet.com/apis/orders/tools/#creating-toolchains).

Example: `tools.json`
```
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
            "pixel_size": 2.7056277056e-05,
            "name_template": "C1232_30_30_{tilex:04d}_{tiley:04d}"
        }
    }
]
```

!!!note Note
    Future of the versions of the CLI will likely add `tools` convenience methods, 
    so composite, harmonize and other tools work like `--clip`. You can follow issue 
    [#601](https://github.com/planetlabs/planet-client-python/issues/601): 
    comment there if you'd like to see it prioritized

### Compositing

Ordering two scenes is easy, just add another id:

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'Two Scenes' \
    20220605_124027_64_242b,20220605_124025_34_242b \
    | planet orders create -
```

And then you can composite them together, using the 'tools' json. You can 
use this, just save it into a file called [tools-composite.json](https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/cli/request-json/tools-composite.json).

```json
[
    {
      "composite": {
        }
    }
]
```

Once you’ve got it saved you call the `--tools` flag to refer to the JSON file, and you 
can pipe that to `orders create`.

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'Two Scenes Composited' \
    20220605_124027_64_242b,20220605_124025_34_242b \
    --no-stac \
    --tools tools-composite.json \
    | planet orders create -
```

Note that we add the `--no-stac` option as [STAC Metadata](#stac-metadata) is not yet supported by the composite 
operation, but STAC metadata is requested by default with the CLI.

### Output as COG

If you'd like to ensure the above order is a Cloud-Optimized Geotiff then you can request it 
as COG in the file format tool.

```json
[
    {
    "file_format": {
        "format": "COG"
      }
    }
]
```

The following command just shows the output with [tools-cog.json](https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/cli/request-json/tools-cog.json):

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'COG Order' \
    20220605_124027_64_242b,20220605_124025_34_242b \
    --tools tools-cog.json
```

As shown above you can also pipe that output directly in to `orders create`. 

### Clip & Composite

To clip and composite you need to specify the clip in the tools (instead of `--clip`), as you can
not use `--clip` and `--tools` in the same call. There is not yet CLI calls to generate the `tools.json`,
so you can just use the [following json](https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/cli/request-json/tools-clip-composite.json):

```json
[
    {
        "composite": {}
    },
    {
        "clip": {
            "aoi": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            -48.492541,
                            -1.404126
                        ],
                        [
                            -48.512879,
                            -1.504392
                        ],
                        [
                            -48.398017,
                            -1.52127
                        ],
                        [
                            -48.380419,
                            -1.423805
                        ],
                        [
                            -48.492541,
                            -1.404126
                        ]
                    ]
                ]
            }
        }
    }
]
```

```sh
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --no-stac \
    --name 'Two Scenes Clipped and Composited' \
    20220605_124027_64_242b,20220605_124025_34_242b \
    --tools tools-clip-composite.json \
    | planet orders create -
```

One cool little trick is that you can even stream in the JSON directly with `curl`, piping it into the request:

```sh
curl -s https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/cli/request-json/tools-clip-composite.json \
    | planet orders request \
        --item-type PSScene \
        --bundle analytic_sr_udm2 \
        --name 'Streaming Clip & Composite' \
        --no-stac \
        20220605_124027_64_242b,20220605_124025_34_242b \
        --tools - \
    | planet orders create -
```

### Harmonize

The harmonize tool allows you to compare data to different generations of satellites by radiometrically harmonizing imagery captured by one satellite instrument type to imagery captured by another. To harmonize your data to a sensor you must define the sensor you wish to harmonize with in your `tools.json`. Currently, only "PS2" (Dove Classic) and "Sentinel-2" are supported as target sensors. The Sentinel-2 target only harmonizes PSScene surface reflectance bundle types (`analytic_8b_sr_udm2`, `analytic_sr_udm2`). The PS2 target only works on analytic bundles from Dove-R (`PS2.SD`).

```json
[
  {
    "harmonize": {
      "target_sensor": "Sentinel-2"
      }
    }
]
```

You may create an order request by calling [`tools-harmonize.json`](https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/cli/request-json/tools-harmonize.json) with `--tools`.

```sh
planet orders request --item-type PSScene --bundle analytic_sr_udm2 --name 'Harmonized data' 20200925_161029_69_2223 --tools tools-harmonize.json
```

## More options

### STAC Metadata

A relatively recent addition to Planet’s orders delivery is the inclusion of [SpatioTemporal Asset Catalog](https://stacspec.org/en)
(STAC) metadata in Orders. STAC metadata provides a more standard set of JSON fields that work with 
many GIS and geospatial [STAC-enabled tools](https://stacindex.org/ecosystem). The CLI `orders request` command currently requests
STAC metadata by default, as the STAC files are small and often more useful than the default JSON metadata.
You can easily turn off STAC output request with the `--no-stac` command:

```sh
planet orders request \
    --item-type PSScene \
    --bundle visual \
    --name 'No STAC' \
    --no-stac \
    20220605_124027_64_242b
```

Currently this needs to be done for any 'composite' operation, as STAC output from composites is not yet 
supported (but is coming). You can explicitly add `--stac`, but it is the default, so does not need to
be included. For more information about Planet’s STAC output see the [Orders API documentation](https://developers.planet.com/apis/orders/delivery/#stac-metadata).

Orders with Google Earth Engine delivery will force the STAC flag to false.

### Cloud Delivery

Another option is to deliver your orders directly to a cloud bucket, like AWS S3 or Google Cloud Storage.
The file given with the `--delivery` option should contain JSON that follows
the options and format given in
[Delivery to Cloud Storage](https://developers.planet.com/docs/orders/delivery/#delivery-to-cloud-storage).

An example would be:

Example: `delivery.json`

```json
{
    "amazon_s3": {
        "aws_access_key_id": "aws_access_key_id",
        "aws_secret_access_key": "aws_secret_access_key",
        "bucket": "bucket",
        "aws_region": "aws_region"
    },
    "archive_type": "zip"
}
```

*New in 2.1*

!!! note

    `--cloudconfig` was the name of this option in version 2.0 and can continue to be used as an alias for `--delivery`.

### Using Orders output as input

One useful thing to note is that the order JSON that reports status and location is a valid Orders API request.
It reports all the parameters that were used to make the previous order, but you can also use it directly as a
request. So the following call is a quick way to exactly redo a previous order request:

```sh
planet orders get <order-id> | planet orders create -
```

Realistically you'd more likely want to get a previous order and then change it in some way (new id’s, different 
tools, etc.). You can remove the 'extra' JSON fields that report on status if you'd like, but the Orders
API will just ignore them if they are included in a request.

There is planned functionality to make it easy to 'update' an existing order, so you can easily grab a past order
and use the CLI to customize it.

### Basemaps Orders

One of the newer features in Planet’s Orders API is the ability to [order basemaps](https://developers.planet.com/apis/orders/basemaps/).
The CLI does not yet support a 'convenience' method to easily create the JSON - you unfortunately
can't yet use `planet orders request` to help form an orders request. But all the other CLI functionality
supports ordering basemaps through the Orders API.

You’ll need to use a full orders request JSON.

```json
{
   "name": "basemap order with geometry",
   "source_type": "basemaps",
   "order_type":"partial",
   "products": [
       {
           "mosaic_name": "global_monthly_2022_01_mosaic",
           "geometry":{
               "type": "Polygon",
               "coordinates":[
                   [
                       [4.607406, 52.353994],
                       [4.680005, 52.353994],
                       [4.680005, 52.395523],
                       [4.607406, 52.395523],
                       [4.607406, 52.353994]
                   ]
               ]
           }
      }
  ],
    "tools": [
      {"merge": {}},
      {"clip": {}}
  ]
}
```

Once you’ve got the JSON, the other commands are all the same. Use create to submit it to the API:

```sh
planet orders create basemap-order.json
```

See the status of the order you just submitted:

```sh
planet orders list --limit 1
```

Extract the ID:

```sh
planet orders list --limit 1 | jq -r .id 
```

Use that ID to wait and download when it’s ready:

```sh
orderid=605b5472-de61-4563-88ae-d43417d3ed96
planet orders wait $orderid
planet orders download $orderid
```

You can also list only the orders you submitted that are for basemaps, using `jq` to filter client side:

```sh
planet orders list | jq -s '.[] | select(.source_type == "basemaps")'
```

#### Bringing it all together

The cool thing is you can combine the data and order commands, to make calls
like ordering the most recent skysat image that was published:

```sh
latest_id=$(planet data filter \
    | planet data search SkySatCollect \
        --sort 'acquired desc' \
        --limit 1 \
        --filter - \
    | jq -r .id)

planet orders request \
    --item-type SkySatCollect \
    --bundle analytic \
    --name 'SkySat Latest' \
    $latest_id \
    | planet orders create -
```

Or get the 5 latest cloud free images in an area and create an order that clips to that area, using 
[geometry.geojson](data/geometry.geojson) from above:

```sh
ids=$(planet data filter --geom geometry.geojson --range clear_percent gt 90 \
    | planet data search PSScene --limit 5 --filter - \
    | jq -r .id \
    | tr '\n' ',' \
    | sed 's/.$//'
)
planet orders request \
    --item-type PSScene \
    --bundle analytic_sr_udm2 \
    --name 'Clipped Scenes' \
    $ids \
    --clip geometry.geojson \
    | planet orders create -
```

This one uses some advanced unix capabilities like `sed` and `tr`, along with unix variables, so more
properly belongs in the [CLI Tips & Tricks](cli-tips-tricks.md), but we’ll leave it here to give a taste of what’s possible.
