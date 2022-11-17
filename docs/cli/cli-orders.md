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
If you're interested in deeper understanding what is going on
then check out our [CLI Concepts](cli-intro.md) guide.


### See Recent Orders

You can use the `list` command to show your recent orders:

```console
planet orders list
```

If you've not placed any orders with Explorer, the CLI or the API directly, then the results
of this call will be blank, so you may want to try out some of the create order commands below.

Sometimes that list gets too long, so you can put a limit on how many are returned:

```console
planet orders list --limit 5
```

You can also filter orders by their `state`, which can be useful to just see orders in 
progress:

```console
planet orders --state running
```

The other options are queued, failed, success, partial and cancelled.

Note you can also get a nice list online as well, at https://www.planet.com/account/#/orders

### Recent Orders with Formatting

You can also print the list of orders more nicely:

```console
planet orders list --pretty
```

The `--pretty` flag is built into most Planet CLI commands, and it formats the JSON to be
more readable.

You can also use `jq`, a powerful command-line JSON-processing tool, that is mentioned in 
the [CLI introduction]((cli-intro.md#jq).

```console
planet orders list | jq
```

Piping any output through jq will format it nicely and do syntax highlighting. You can 
also `jq` to just show select information, which can be useful for getting a quick sense 
of the state of the state of things and pull out id's for other operations:

```console
planet orders list | jq -rs '.[] | "\(.id) \(.created_on) \(.state) \(.name)"'
```

You can customize which fields you want to show by changing the values.

### Number of recent orders

You can use jq to process the output for more insight, like 
get a count of how many recent orders you've done. 

```console
planet orders list | jq -s length
```

This uses `-s` to collect the output into a single array, and `length` then tells the
length of the array.

### Info on an Order

For a bit more information about an order, including the location of any downloads, use
the `get` command, using the order id.

```console
planet orders get 782b414e-4e34-4f31-86f4-5b757bd062d7
```

### Create an Order Request

To create an order you need a name, a [bundle](https://developers.planet.com/apis/orders/product-bundles-reference/),
 one or more id's, and an [item type](https://developers.planet.com/docs/apis/data/items-assets/#item-types):

First lets get the ID of an item you have download access to, using the Data API: 

```
planet data filter | planet data search PSScene --limit 1 - | jq -r .id
```

If you don't have access to PlanetScope data then replace PSScene with SkySatCollect.
Then make the following call:

```console
planet orders request PSScene visual --name "My First Order" --id 20220605_124027_64_242b 
```

Running the above command should output the JSON needed to create an order:

```json
{"name": "My First Order", "products": [{"item_ids": ["20220605_124027_64_242b"], "item_type": "PSScene", "product_bundle": "analytic_sr_udm2"}]}
```

You can also use `jq` here to make it a bit more readable:

```console
planet orders request PSScene analytic_sr_udm2 --name "My First Order" --id 20220605_124027_64_242b | jq
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
  ]
}
```

### Save an Order Request

The above command just prints out the necessary JSON to create an order. To actually use it you can
save the output into a file:

```console
planet orders request PSScene analytic_sr_udm2 --name "My first Order" --id 20220605_124027_64_242b \
 > request-1.json
```

Note that `\` just tells the command-line to treat the next line as the same one. It's used here so it's 
easier to read, but you can still copy and paste the full line into your command-line and it should work.

This saves the above JSON in a file called `request-1.json`

### Create an Order

From there you can create the order with the request you just saved: 

```console
planet orders create request-1.json
```

The output of that command is the JSON returned from the server, that reports the status:

```json
{
  "_links": {
    "_self": "https://api.planet.com/compute/ops/orders/v2/3b1f250e-72a0-41bb-94ea-8109b6b34e44"
  },
  "created_on": "2022-07-16T05:04:36.998Z",
  "error_hints": [],
  "id": "3b1f250e-72a0-41bb-94ea-8109b6b34e44",
  "last_message": "Preparing order",
  "last_modified": "2022-07-16T05:04:36.998Z",
  "name": "My Second Order",
  "products": [
    {
      "item_ids": [
        "20220605_124027_64_242b",
        "20220605_124025_34_242b"
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

### Create Request and Order in One Call

Using a unix command called a 'pipe', which looks like `|`, you can skip the step of saving to disk,
passing the output of the `orders request` command directly to be the input of the `orders create`
command:

```console
planet orders request PSScene analytic_sr_udm2 --name "My Second Order" \
--id 20220605_124027_64_242b,20220605_124025_34_242b | planet orders create
```

The Planet CLI is designed to work well with piping, as it aims at small commands that can be 
combined in powerful ways, so you'll see it used in a number of the examples.

### Download an order

To download all files in an order you use the `download` command:

```console
planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30
```
Note this only works when the order is ready for download. To do that you can
keep running `orders get` until the `state` is `success`. Or for a better
way see the next example.

### Wait then download an order

The `wait` command is a small, dedicated command that polls the server to 
see if an order is ready for downloading, showing the status. It's not
so useful by itself, but can be combined with the `download` command to
only start the download once the order is ready:

```console
planet orders wait 65df4eb0-e416-4243-a4d2-38afcf382c30 \
&& planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30 
```

This uses the logical AND operator (`&&`) to say "don't run the second command
until the first is done".

### Save order ID

You can also use a unix variable to store the order id of your most recently placed order, 
and then use that for the wait and download commands:

```console
orderid=`planet orders list --limit 1 | jq -r .id`
planet orders wait $orderid && planet orders download $orderid
```

This can be nicer than copying and pasting it in.

You could also save the id right when you place the order:

```console
orderid=`planet orders create request-1.json | jq -r .id`
```

To check the current value of `orderid` just run `echo $orderid`.

### Create an order and download when ready

You can then combine these all into one call, to create the order and 
download it when it's available:

```console
id=`planet orders create request-1.json | jq -r '.id'` && \
planet orders wait $id && planet orders download $id
```

### Download to a different directory

You can use the `--directory` flag to save the output to a specific directory. This
call saves it to a directory called `psscene`, at whatever location you are at
currently:

```console
mkdir psscene
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --directory psscene
```

You can also specify absolute directories (int his case to my desktop):

```console
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --directory /Users/cholmes/Desktop/
```

### Verify checksum

The `--checksum` command will do an extra step to make sure the file you got 
wasn't corrupted along the way (during download, etc). It checks that the bytes
downloaded are the same as the ones on the server. By default it doesn't show
anything if the checksums match.

```console
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --checksum MD5
```

This command isn't often necessary in single download commands, but is quite 
useful if you are downloading thousands of files with a script, as the likelihood 
of at least one being corrupted in creases

## Tools with orders

Now we'll dive into the variety of ways to customize your order. These can all be
combined with all the commands listed above.


### Clipping

The most used tool is the `clip` operation, which lets you pass a geometry to the
Orders API and it creates new images that only have pixels within the geometry you
gave it. The file given with the `--clip` option should contain valid [GeoJSON](https://geojson.org/).
It can be a Polygon geometry, a Feature, or a FeatureClass. If it is a FeatureClass,
only the first Feature is used for the clip geometry.

Example: `aoi.geojson`
```
{
    "type": "Polygon",
    "coordinates": [
        [
            [
                37.791595458984375,
                14.84923123791421
            ],
            [
                37.90214538574219,
                14.84923123791421
            ],
            [
                37.90214538574219,
                14.945448293647944
            ],
            [
                37.791595458984375,
                14.945448293647944
            ],
            [
                37.791595458984375,
                14.84923123791421
            ]
        ]
    ]
}
```

We'll work with a geojson that is already saved. You should download the 
[geometry](https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/data/geometry.geojson)
(and you can see it [on github](https://github.com/planetlabs/planet-client-python/blob/main/docs/data/geometry.geojson)
or it is also stored in the repo in the [data/](data/) directory. 

You can move that geometry to your current directory and use the following command, or
tweak the geometry.geojson to refer to where you downloaded it.

```console
planet orders request PSScene analytic_sr_udm2 --clip geometry.geojson --name clipped-geom \
 --id 20220605_124027_64_242b | planet orders create
```

### Additional Tools

Since clip is so heavily used it has its own dedicated command in the CLI. All
the other tools use the `--tools` option, that points to a file. The file should 
contain JSON that follows the format for a toolchain, the "tools" section of an order. 
The toolchain options and format are given in
[Creating Toolchains](https://developers.planet.com/docs/orders/tools-toolchains/#creating-toolchains).

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

```console
planet orders request PSScene analytic_sr_udm2 --name "Two Scenes" \
 --id 20220605_124027_64_242b,20220605_124025_34_242b | planet orders create
```

And then you can composite them together, using the 'tools' json. You can 
use this, just save it into a file called tools-composite.json.

```json
[
    {
      "composite": {
        }
    }
]
```

Once you've got it saved you call the `--tools` flag to refer to the JSON file, and you 
can pipe that to `orders create`.

```console
planet orders request PSScene analytic_sr_udm2 --name "Two Scenes Composited" \
--id 20220605_124027_64_242b,20220605_124025_34_242b --tools tools-composite.json | planet orders create
```

### Output as COG

If you'd like the above order as a COG you Get the output as a cloud-optimized GeoTIFF:


```json
[
    {
      "composite": {
        }
    },
    {
    "file_format": {
        "format": "COG"
      }
    }
]
```

The following command just shows the output, you can pipe into orders create if you'd like:

```console
planet orders request PSScene analytic_sr_udm2 --name "Two Scenes Composited" \
 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools tools-cog.json
```

### Clip & Composite

To clip and composite you need to specify the clip in the tools (instead of `--clip`), as you can
not use `--clip` and `--tools` in the same call. There is not yet CLI calls to generate the `tools.json`,
so you can just grab the [full tools.json](https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/data/tools-clip-composite.json)

```console
planet orders request PSScene analytic_sr_udm2 --name "Two Scenes Clipped and Composited" \
 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools tools-clip-composite.json
```

One cool little trick is that you can even stream in the JSON directly with `curl`, piping it into the request:

```console
curl -s https://raw.githubusercontent.com/planetlabs/planet-client-python/main/docs/data/tools-clip-composite.json \
| planet orders request PSScene analytic_sr_udm2 --name "Streaming Clip & Composite" \
 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools - | planet orders create
```

### Harmonize

TODO

### STAC Metadata

TODO

### Cloud Delivery

Another option is to 
The file given with the `--cloudconfig` option should contain JSON that follows
the options and format given in
[Delivery to Cloud Storage](https://developers.planet.com/docs/orders/delivery/#delivery-to-cloud-storage).

An example would be:

Example: `cloudconfig.json`
```
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

#### Basemaps Orders

TODO


#### Using Orders output as input

One useful thing to note is that the order JSON that reports status and location is a valid Orders API request.
It reports all the parameters that were used to make the previous order, but you can also use it directly as a
request. So the following call is a quick way to exactly redo a previous order request:

```console
planet orders get <order-id> | planet orders create -
```

Realistically you'd more likely want to get a previous order and then change it in some way (new id's, different 
tools, etc.). You can remove the 'extra' JSON fields that report on status if you'd like, but the Orders
API will just ignore them if they are included in a request.

There is planned functionality to make it easy to 'update' an existing order, so you can easily grab a past order
and use the CLI to customize it.


#### Bringing it all together

The cool thing is you can combine the data and order commands, to make calls like ordering the most recent skysat
image that was published:


```console
planet orders request SkySatCollect analytic --name "SkySat Latest" \
--id `planet data filter | planet data search SkySatCollect --sort 'acquired desc' --limit 1 - | jq -r .id` \
| planet orders create
```

Or get the 5 latest cloud free images in an area and create an order that clips to that area, using 
[geometry.geojson](data/geometry.geojson) from above:

```console
ids=`planet data filter --geom geometry.geojson --range clear_percent gt 90 | planet data \
search PSScene --limit 5 - | jq -r .id | tr '\n' , | sed 's/.$//'`
planet orders request PSScene analytic_sr_udm2 --name "Clipped Scenes"  \
--id $ids --clip geometry.geojson | planet orders create -
```

This one uses some advanced unix capabilities like `sed` and `tr`, along with unix variables, so more
properly belongs in the [CLI Tips & Tricks]](cli-tips-tricks.md), but we'll leave it here to give a taste
of what's possible.


### Future workflows to support

* Get the last 5 strips for an AOI, clipped & composited to the AOI (need either 'composite by strip' or some client-side code
  to sort which results are in the same strip)



