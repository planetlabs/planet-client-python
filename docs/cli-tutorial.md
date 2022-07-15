
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

Note you can also get a nice list online as well, at https://www.planet.com/account/#/orders

#### Recent Orders with Formatting

You can also print the list of orders more nicely:

```console
planet orders list | jq
planet orders list --pretty
```

These are two different ways to do it. The `--pretty` tag is built into planet commands, while
the `jq` command will format any JSON more nicely, and can be used for more advanced processing.

#### Number of recent orders

You can use jq to process the output for more insight, like 
get a count of how many recent orders you've done. 

```console
planet orders list | jq -s length
```

This uses `-s` to collect the output into a single array, and `length` then tells the
length of the array.



Get more info on a single order

```console
planet orders get 782b414e-4e34-4f31-86f4-5b757bd062d7
```

Download the order

```console
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7
```

Download it to a different directory (relative to where the command is run)


```console
mkdir psscene
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --directory psscene
```

Download to a directory specified absolutely (in this case to my desktop)

```console
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --directory /Users/cholmes/Desktop/
```

Verify the checksum to make sure the file I got wasn't corrupted along the way (during download, etc)

```console
planet orders download 782b414e-4e34-4f31-86f4-5b757bd062d7 --checksum MD5
```

Create a new order request from a scene ID found in Explorer
(Note that \ just tells the console to treat the next line as the same one - used here to be a bit easier to read)

```console
planet orders request --name "My First Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b \
 --item-type PSScene
```

Save to a file in the directory where the command was run

```console
planet orders request --name "My First Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b \
 --item-type PSScene > request-1.json
```

Make a new order with that request (should be the same as 
[this one](https://gist.githubusercontent.com/cholmes/892f851d5c55f7cf93e210595750ecfe/raw/4c255dcdf0973e0f72d43d82c776d8251fb7545e/request-1.json))

```console
planet orders create request-1.json
```

Create the request and make a new order with it all in one call

```console
planet orders request --name "My First Order" --bundle analytic_sr_udm2 --id 20220605_124027_64_242b \
 --item-type PSScene | planet orders create
```

Download the order. Note this only works when the order is ready:

```console
planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30
```

Wait until the order is ready for download, then order it:

```console
planet orders wait 65df4eb0-e416-4243-a4d2-38afcf382c30 \
&& planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30 
```

You can also use a unix variable to store the order id of your most recently placed order, 
and then use that for the wait and download commands:

```console
orderid=`planet orders list --limit 1 | jq -r .id`
planet orders wait $orderid && planet orders download $orderid
```

Create an order from a request, wait for it and download when ready 

```console
id=`planet orders create request-1.json | jq -r '.id'` && planet orders wait $id && planet orders download $id
```

Create an order clipped to a geometry

(download [raw json](https://gist.githubusercontent.com/cholmes/c7736ac5241d77605524d01ed2dc57a1/raw/7d24e02ba894e64c4c737c253a0cce4cac54167c/geometry.geojson) 
from github, or [preview](https://gist.github.com/cholmes/c7736ac5241d77605524d01ed2dc57a1))

```console
planet orders request --item-type PSScene --clip geometry.geojson --name clipped-geom \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b | planet orders create
```

Order Two Scenes in one order

```console
planet orders request --item-type PSScene --name "Two Scenes" \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b,20220605_124025_34_242b | planet orders create
```

Composite them together

Use this, save as tools-composite.json

```json
[
    {
      "composite": {
        }
    }
]
```

Then create command and order

```console
planet orders request --item-type PSScene --name "Two Scenes Composited" \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools tools-composite.json | planet orders create
```

Get the output as a cloud-optimized GeoTIFF:
(save as tools-cog.json)

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

To clip and composite you need to specify the clip in the tools (instead of `--clip`).
Can get it from [this gist](https://gist.github.com/cholmes/378d050a263ae433ddbbb91c3439994b)

```console
planet orders request --item-type PSScene --name "Two Scenes Clipped and Composited" \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools tools-clip-composite.json
```

Or can even stream that in:

```console
curl -s https://gist.githubusercontent.com/cholmes/378d050a263ae433ddbbb91c3439994b/raw/ebcaa54cacdc6f696a0506705785f8ff8dae9af1/ \
tools-clip-composite.json | planet orders request --item-type PSScene --name "Streaming Clip & Composite" \
 --bundle analytic_sr_udm2 --id 20220605_124027_64_242b,20220605_124025_34_242b --tools - | planet orders create
```

TODO: STAC Output

One useful thing to note is that the order JSON that reports status and location is a valid Orders API request.
It reports all the parameters that were used to make the previous order, but you can also use it directly as a
request. So the following call is a quick way to exactly redo a previous order request:

```console
planet orders get <order-id> | planet orders create -
```

Realistically you'd more likely want to 

### Data

Run a search for all the latest planetscope scenes that you have download access to:

```console
planet data filter > filter.json
planet data search-quick PSScene filter.json
```

Or using piping (recommended)

```console
planet data filter | planet data search-quick PSScene -
```

Run a search for all the latest PS Scenes in a bounding box in Iowa:

Save this as geometry.json

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

```console
planet data filter --geom geometry.json | planet data search-quick PSScene -
```

And turn into GeoJSON (many gis programs do better with 'real' geojson, the default output is newline delimited geojson)

```console
planet data filter --geom geometry.json | planet data search-quick PSScene - | planet collect -
```

Search just for 8-band assets

```console
planet data filter --asset ortho_analytic_8b_sr | planet data search-quick PSScene -
```

Search for 8-band assets that also have a UDM

```console
planet data filter --asset ortho_analytic_8b_sr --asset udm2 | planet data search-quick PSScene -
```

Search for any 8 band data, not just ones that you have download access to (default is only those you have access to)

```console
planet data filter --permission false --asset ortho_analytic_8b_sr | planet data search-quick PSScene -
```

Make a filter for data acquired in July 2021

```console
planet data filter --date-range acquired gte 2021-07-01 --date-range acquired lt 2021-08-01
```

Make a filter for data with clear pixels greater than 90%

```console
planet data filter --range clear_percent gt 90
```

Make a filter for all data in a single strip:

```console
planet data filter --string-in strip_id 5743640
```

Search for all landsat 8, sentinel 2 and planetscope images in an area of interest

```console
planet data filter --geom geometry.json  | planet data search-quick PSScene,Sentinel2L1C,Landsat8L1G -
```

Get the id of the most recent skysat image taken (that you have download access to)

```console
planet data filter | planet data search-quick SkySatCollect --limit 1 - | jq -r .id
```

Order the most recent skysat image published.

```console
planet orders request --name "SkySat Latest" --item-type SkySatCollect --bundle analytic \
--id `planet data filter | planet data search-quick SkySatCollect --sort 'acquired desc' --limit 1 - | jq -r .id` \
| planet orders create
```

Get the 5 latest cloud free images in an area and create an order that clips to that area, using 
[geometry.geojson](https://gist.github.com/cholmes/378d050a263ae433ddbbb91c3439994b) from above:
(this one uses variables in unix)
(note that you need the tr and sd to format the output of jq into the comma delimited list we need as input. There is likely some better way to do this...)


```console
ids=`planet data filter --geom geometry.geojson --range clear_percent gt 90 | planet data \
search-quick PSScene --limit 5 - | jq -r .id | tr '\n' , | sed 's/.$//'`
planet orders request --name "Clipped Scenes" --item-type PSScene --bundle analytic_sr_udm2  \
--id $ids --clip geometry.geojson | planet orders create -
```



### Future workflows to support

* Get the last 5 strips for an AOI, clipped & composited to the AOI (need either 'composite by strip' or some client-side code
  to sort which results are in the same strip)
* STAC output
* Cloud delivery (could do this today with editing JSON, but should wait till we have it a bit better)
* Get most recent acquired (using sort)

