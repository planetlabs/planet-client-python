
## About

This tutorial is designed to show off the core Planet command-line interface (CLI) capabilities. 
The Planet depends on several more advanced command-line concepts, but this tutorial should let
you get a sense of what you can do, with enough examples that you should be able to adapt the
commands for what you want to do. If you're interested in deeper understanding what is going on
then check out our [CLI Concepts](cli-concepts.md) guide.

## Commands

### Auth

We start with the `auth` package of tools, to ensure you can get started.

#### Initialize

The main way to initialize the Planet CLI is to use `init`, which will prompt
you for your Planet username and password, and then store your API key.

```console
planet auth init
```

#### View API Key

You can easily see your API key that is being used for requests:

```console
planet auth value
```

This is a very convenient way to quickly grab your API key.

#### Set environment variable

You can also set an 'environment variable' in your terminal:

```
export PL_API_KEY=<your api key>
```

This currently will override your key set with 'init'. Be warned that if you have this 
set `planet auth value` won't report.


### Get Help

Most commands are pretty self-documenting, and you can use `--help` after any command to get usage info. 
Many will show the help text if you don't form a complete command.

```console
planet --help
planet
planet orders
planet orders list --help
```

### Orders

The orders command enables interaction with the [Orders API](https://developers.planet.com/apis/orders/),
that lets you activate and download Planet products in bulk, and apply various 'tools' to your processes.

#### See Recent Orders

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

#### Recent Orders with Formatting

You can also print the list of orders more nicely:

```console
planet orders list | jq
planet orders list --pretty
```

These are two different ways to do it. The `--pretty` tag is built into planet commands, while
the `jq` command will format any JSON more nicely, and can be used for more advanced processing.

This gives you a nicely formatted JSON. You can use `jq` to just show select information, which 
can be useful for getting a quick sense of the state of the state of things and pull out
id's for other operations:

```console
planet orders list | jq -rs '.[] | "\(.id) \(.created_on) \(.state) \(.name)"'
```

You can customize which fields you want to show.

#### Number of recent orders

You can use jq to process the output for more insight, like 
get a count of how many recent orders you've done. 

```console
planet orders list | jq -s length
```

This uses `-s` to collect the output into a single array, and `length` then tells the
length of the array.

#### Info on an Order

For a bit more information about an order, including the location of any downloads, use
the `get` command, using the order id.

```console
planet orders get 782b414e-4e34-4f31-86f4-5b757bd062d7
```

#### Create an Order Request

To create an order you need a name, a [bundle](https://developers.planet.com/apis/orders/product-bundles-reference/),
 one or more id's, and an [item type](https://developers.planet.com/docs/apis/data/items-assets/#item-types):

```console
planet orders request --name "My First Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b \
 --item-type PSScene
```

You should replace the `id` with a scene you have access to, using [Explorer](https://planet.com/explorer)
is probably the easiest way to do so.

Running the above command should output the JSON needed to create an order:

```json
{"name": "My First Order", "products": [{"item_ids": ["20220605_124027_64_242b"], "item_type": "PSScene", "product_bundle": "analytic_sr_udm2"}]}
```

Note that `\` just tells the command-line to treat the next line as the same one. It's used here so it's 
easier to read, but you can still copy and paste the full line into your command-line and it should work.

You can also use `jq` here to make it a bit more readable:

```console
planet orders request --name "My First Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b \
 --item-type PSScene | jq
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

#### Save an Order Request

The above command just prints out the necessary JSON to create an order. To actually use it you can
save the output into a file:

```console
planet orders request --name "My first Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b \
 --item-type PSScene > request-1.json
```

This saves the above JSON in a file called `request-1.json`

#### Create an Order

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
command-line just use `jq` as above: `planet orders create request-1.json` (but remember
if you run that command again it will create a second order).

#### Create Request and Order in One Call

Using a unix command called a 'pipe', which looks like `|`, you can skip the step of saving to disk,
passing the output of the `orders request` command directly to be the input of the `orders create`
command:

```console
planet orders request --name "My Second Order" --bundle analytic_sr_udm2 \ 
--id 20220605_124027_64_242b,20220605_124025_34_242b --item-type PSScene | planet orders create
```

The Planet CLI is designed to work well with piping, as it aims at small commands that can be 
combined in powerful ways, so you'll see it used in a number of the examples.

#### Download an order

To download all files in an order you use the `download` command:

```console
planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30
```
Note this only works when the order is ready for download. To do that you can
keep running `orders get` until the `state` is `success`. Or for a better
way see the next example.

#### Wait then download an order

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

#### Save order ID

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

#### Create an order and download when ready

You can then combine these all into one call, to create the order and 
download it when it's available:

```console
id=`planet orders create request-1.json | jq -r '.id'` && \
planet orders wait $id && planet orders download $id
```

#### Download to a different directory

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

#### Verify checksum

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

#### Create an order clipped to a geometry

Now we'll dive into the variety of ways to customize your order. These can all be
combined with all the commands listed above.

We'll work with a geojson saved online. You should download the 
[geometry](data/geometry.geojson). 

You can move that geometry to your current directory and use the following command, or
tweak the geometry.geojson to refer to where you downloaded it.

```console
planet orders request --item-type PSScene --clip geometry.geojson --name clipped-geom \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b | planet orders create
```

#### Two Scenes, composited

Ordering two scenes is easy, just add another id:

```console
planet orders request --item-type PSScene --name "Two Scenes" \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b,20220605_124025_34_242b | planet orders create
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
planet orders request --item-type PSScene --name "Two Scenes Composited" --bundle analytic_sr_udm2 \ 
--id 20220605_124027_64_242b,20220605_124025_34_242b --tools tools-composite.json | planet orders create
```

(We are working on adding `tools` convenience methods, so composite and other tools work like
`--clip`. You can follow issue [#601](https://github.com/planetlabs/planet-client-python/issues/601):
comment there if you'd like to see it prioritized)

#### Output as COG

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
planet orders request --item-type PSScene --name "Two Scenes Composited" \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools tools-cog.json
```

#### Clip & Composite

To clip and composite you need to specify the clip in the tools (instead of `--clip`), as you can
not use `--clip` and `--tools` in the same call. You can see the full JSON for the tools in 
[here](data/tools-clip-composite.json).

```console
planet orders request --item-type PSScene --name "Two Scenes Clipped and Composited" \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools tools-clip-composite.json
```

One cool little trick is that you can even stream in the JSON directly with `curl`, piping it into the request:

```console
curl -s https://gist.githubusercontent.com/cholmes/378d050a263ae433ddbbb91c3439994b/raw/ebcaa54cacdc6f696a0506705785f8ff8dae9af1/ \
tools-clip-composite.json | planet orders request --item-type PSScene --name "Streaming Clip & Composite" \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools - | planet orders create
```

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

### Data

Next up is the [Data API](https://developers.planet.com/docs/apis/data/), which lets you search Planet's catalog 
(including select public datasets like Sentinel 1 & 2, Landsat & MODIS).

#### Search latest Scenes

One of the commands you'll use most frequently is `planet data filter`, which works similar to 
`planet orders request` in that it is a convenience method to create the JSON you need to run
other commands. You can run it with no arguments to see how it works:

```console
planet data filter
```

The output says that by default it will only show you imagery that you have permission to actually download,
and that is of `standard` quality category. This provides some reasonable defaults, but they can be changed
with flags, for example if you wanted to search all of Planet's catalog, or to look for `test` data that 
is published by doesn't meet the standard quality level.

There are a lot of options for what you can do with the command, and we recommend running
`planet data filter --help` often to get a reference of how the commands work. And we'll try to 
give lots of examples below as well.

So you can run the filter command and save it, and then use that file with the `search`
command:

```console
planet data filter > filter.json
planet data search PSScene filter.json
```

Or the recommended route is to use a pipe (`|`), as mentioned above [above](#create-request-and-order-in-one-call):

```console
planet data filter | planet data search PSScene -
```

Note the dash (`-`), which explicitly tells the CLI to use the output from the call that is piped into it.

#### Search on Item Type

These first searches were done on the [PSScene](https://developers.planet.com/docs/data/psscene/) 'item type', but you
can use any [Item Type](https://developers.planet.com/docs/apis/data/items-assets/#item-types) that Planet offers in 
its catalog. The item type is the first argument of the `search` command, followed by the 'filter'. Note that
you can specify any number of item types here:

```console
planet data filter | planet data search PSScene,Sentinel2L1C,Landsat8L1G,SkySatCollect, -
```

This will search for all the most recent images captured by PlanetScope, SkySat, Sentinel 2 and Landsat 8 satellites. 
Note that you'll likely mostly see PlanetScope results, as they generate far more individual images than the others.
The filter you specify will apply to all item types, but not all filters work against all satellites, so you may 
inadvertently filter some out if you do some specific properties.

#### Run a search on a bounding box

Most searches you'll likely want to run on a geometry. To try this out you can use the following bounding box
of Iowa. You can copy it and save as a file called `geometry.json`

```json
{
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
              -93.7353,
              41.6236
            ],
            [
              -92.2741,
              41.6236
            ],
            [
              -92.2741,
              42.3747
            ],
            [
              -93.7353,
              42.3747
            ],
            [
              -93.7353,
              41.6236
            ]
          ]
        ]
      }
    }
  ]
}
```

And then run it with this command:

```console
planet data filter --geom geometry.json | planet data search PSScene -
```

Note that by default all searches with the command-line return 100 results, but you can easily increase that with
the `--limit` flag:

```console
planet data filter --geom geometry.json | planet data search --limit 500 PSScene -
```

Creating geometries for search can be annoying in a command-line workflow, but there are some ideas in the
[Advanced CLI Tutorial](cli-plus-tutorial.md#geometry-inputs).

#### Output as valid GeoJSON

By default the output of Planet's Data API is [newline-delimited GeoJSON](https://stevage.github.io/ndgeojson/), which
is much better for streaming. While more and more programs will understand the format, the CLI also provides 
the `planet collect` method to transform the output from the Data API to valid GeoJSON. You just pipe the end
output to it:

```console
planet data filter --geom geometry.json | planet data search PSScene - | planet collect -
```

If you want to visualize this you can save it as a file:

```console
planet data filter --geom geometry.json | planet data search PSScene - | planet collect - > planet-search.geojson
```

This you can then open with your favorite GIS program, or see this 
[geometry visualization](cli-plus-tutorial.md#geometry-inputs) section for some ideas that flow a bit better with 
the command-line.

#### Date Filter

Some of the most common filtering is by date. You could get all imagery acquired before August 2021:

```console
planet data filter --date-range acquired lt 2021-08-01 | planet data search PSScene -
```

The 'operator' in this case is 'less than' (`lt`). The options are:
 * `gt` - greater than
 * `gte` - greater than or equal to
 * `lt` - less than
 * `lte` - less than or equal to

You must specify which date field you want to use, either `acquired` or `published`.

You can use the flags multiple times, and they are logically 'AND'-ed together, so you can
do a search for all images in July of 2021:

```console
planet data filter --date-range acquired gte 2021-07-01 --date-range acquired lt 2021-08-01 | \
planet data search PSScene -
```

The date input understands [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) and 
[ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) formats. You can specify just the date,
or include the time, to search for all Planetscope images acquired within 5 seconds at a time
on July 1st 2021:

```console
planet data filter --date-range acquired gte 2021-07-01:06:20:10 --date-range acquired lt 2021-07-01:06:20:15 | \
planet data search PSScene - 
```

#### Range Filter

The range filter uses the same operators as the date filter, but works against any numerical property. The most useful
of these tend to be ones about cloudy pixels. For example you can search for data with clear pixels greater than 90%:

```console
planet data filter --range clear_percent gt 90
```

#### String-In Filter

For properties that are strings you can use the `string-in` filter. For example search for all planetscope imagery
with PS2 instrument:

```console
planet data filter --string-in instrument PS2 | planet data search PSScene -
```

You can specify multiple strings to match, with a comma:

```console
planet data filter --string-in instrument PS2,PSB.SD | planet data search PSScene -
```

Another example is to select all data in a single strip:

```console
planet data filter --string-in strip_id 5743640 | planet data search PSScene -
```

Note that in all these commands we are piping the results into the search. If you don't include the pipe then you'll
get the filter output, which can be interested to inspect to see exactly what is sent to the server.

#### Filter by asset

You can limit your search to only data with a particular asset, for example search just for 8-band analytic assets:

```console
planet data filter --asset ortho_analytic_8b_sr | planet data search PSScene -
```

Or 8-band assets that also have a UDM.

```console
planet data filter --asset ortho_analytic_8b_sr --asset udm2 | planet data search PSScene -
```

You can find the list of available assets in each Item Type Page, like 
[available assets](https://developers.planet.com/docs/data/psscene/#available-asset-types) for PSScene. You can see
[a table of all Item Types](https://developers.planet.com/docs/data/psscene/#available-asset-types), which links to 
the page for each with their list of asset types.

Note that the asset filter doesn't perform any validation, so if your searches aren't returning anything check to make
sure you got the asset right, and it's valid for the item-types you're searching.

#### Permission Filter

The 'permission filter' is set to true by default, since most people want to search only for data they have access to
and are able to download. But if you'd like to just get search Planet's catalog and get a sense of what is out there
you can set the permission filter to false:

```console
planet data filter --permission false --asset ortho_analytic_8b_sr | planet data search PSScene -
```

#### Sort

You can also specify the sorting with your searches. The default sort is ordered by the most recent published
images. But you can also sort by `acquired`, which is often more useful. You can sort in ascending or 
descending order. The options are are:

 * 'acquired asc'
 * 'acquired desc'
 * 'published asc'
 * 'published desc'

The lets you do things like get the id of the most recent skysat image taken (that you have download access to):

```console
planet data filter | planet data search SkySatCollect --sort 'acquired desc' --limit 1 - 
```

And you can also just get the ID, using `jq`

```console
planet data filter | planet data search SkySatCollect --sort 'acquired desc' --limit 1 - | jq -r .id
```

#### Bringing it all together

The cool thing is you can combine the data and order commands, to make calls like ordering the most recent skysat
image that was published:


```console
planet orders request --name "SkySat Latest" --item-type SkySatCollect --bundle analytic \
--id `planet data filter | planet data search SkySatCollect --sort 'acquired desc' --limit 1 - | jq -r .id` \
| planet orders create
```

Or get the 5 latest cloud free images in an area and create an order that clips to that area, using 
[geometry.geojson](data/geometry.json) from above:

```console
ids=`planet data filter --geom geometry.geojson --range clear_percent gt 90 | planet data \
search PSScene --limit 5 - | jq -r .id | tr '\n' , | sed 's/.$//'`
planet orders request --name "Clipped Scenes" --item-type PSScene --bundle analytic_sr_udm2  \
--id $ids --clip geometry.geojson | planet orders create -
```

This one uses some advanced unix capabilities like `sed` and `tr`, along with unix variables, so more
properly belongs in the [Advanced CLI Tutorial](cli-plus-tutorial.md), but we'll leave it here to give a taste
of what's possible.


### Future workflows to support

* Get the last 5 strips for an AOI, clipped & composited to the AOI (need either 'composite by strip' or some client-side code
  to sort which results are in the same strip)
* STAC output
* Cloud delivery (could do this today with editing JSON, but should wait till we have it a bit better)


