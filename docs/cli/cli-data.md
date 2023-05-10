---
title: CLI for Data API Tutorial
---

## Introduction

The `planet data` CLI commands enable interaction with the [Data API](https://developers.planet.com/docs/apis/data/),
which lets you search Planet’s catalog (including select public datasets like Sentinel 2 and Landsat 8).
Currently the CLI has focused on the core search functionality, implementing
[Quick Search](https://developers.planet.com/docs/apis/data/reference/#tag/Item-Search/operation/QuickSearch)
and [stats](https://developers.planet.com/docs/apis/data/reference/#tag/Item-Stats/operation/Stats) plus some
partial saved search functionality.

## `data search` command basics

At this point you should have completed [Step 5](../get-started/quick-start-guide.md#step-5-search-for-planet-imagery)
of the quick start guide, and run your first full data search command:

```sh
planet data search PSScene --filter filter.json > recent-psscene.json
```

This saves the descriptions of the latest 100 standard-quality scenes you have permissions to download in a file, that you can open and look at.

### Pretty printing

You will likely notice that this file is quite wide, with one very long line for each Planet 
item returned. You can make for a more readable file by using the `--pretty` flag:

```sh
planet data search --pretty PSScene --filter filter.json > recent-psscene.json
```

The `--pretty` flag is built into most of the CLI calls. But you can also achieve the
same effect by using another CLI program: `jq`. It is a very powerful library, providing
extensive manipulation of JSON, but simply
piping any JSON output through it prints it in a more readable form. So the following
command will do the same thing as the previous one:

```sh
planet data search PSScene --filter filter.json | jq > recent-psscene.json
```

You can read a bit [more about jq]((cli-intro.md#jq) in the CLI intro.

### Output to stdin

You also don't have to save the output to a file. If you don't redirect it into a file then
it will just print out on the console.

```sh
planet data search PSScene --filter filter.json
```

If you enter this command you’ll see the output stream by. Here you can use jq again, and
it’ll often give you nice syntax highlighting in addition to formatting.

```sh
planet data search PSScene --filter filter.json | jq
```

### Create filter and search in one call

Using a unix command called a 'pipe', which looks like `|`, you can skip the step of saving to disk,
passing the output of the `data filter` command directly to be the input of the `data search`
command:

```sh
planet data filter --permission --std-quality | planet data search --pretty PSScene --filter -
```

Note the dash (`-`), which explicitly tells the CLI to use the output from the call that is piped into it.

You can learn more about the pipe command, as well as the `>` command above in the 
[Piping & redirection section](cli-intro.md#piping-redirection) of the CLI Introduction.

### Search without filtering

If no filtering is required, the search command can be called directly:

```sh
planet data search PSScene
```

This outputs the last 100 scenes.


### Search on Item Type

These first searches were done on the [PSScene](https://developers.planet.com/docs/data/psscene/) 'item type', but you
can use any [Item Type](https://developers.planet.com/docs/apis/data/items-assets/#item-types) that Planet offers in 
its catalog. The item type is the first argument of the `search` command, followed by the 'filter'. Note that
you can specify any number of item types here:

```sh
planet data search PSScene,Sentinel2L1C,Landsat8L1G,SkySatCollect
```

This will search for all the most recent images captured by PlanetScope, SkySat, Sentinel 2 and Landsat 8 satellites. 
Note that you’ll likely mostly see PlanetScope results, as they generate far more individual images than the others.
The filter you specify will apply to all item types, but not all filters work against all satellites, so you may 
inadvertently filter some out if you are filtering specific properties.

### Limits

By default the `search` command returns only the 100 first scenes. But with the CLI you can set any limit, and the SDK
under the hood will automatically page through all the results from the API. 

```sh
planet data search --limit 3000 PSScene
```

Note you can also do a call with no limits if you set the limit to `0`. Though don't use this haphazardly, or you’ll be
generating a lot of JSON from your request. It’s best to use it with a number of filters to constrain the search, so
you don't get hundreds of millions of results.

### Output as valid GeoJSON

By default the output of Planet’s Data API is [newline-delimited GeoJSON](https://stevage.github.io/ndgeojson/), which
is much better for streaming. While more and more programs will understand the format, the CLI also provides 
the `planet collect` method to transform the output from the Data API to valid GeoJSON. You just pipe the end
output to it:

```sh
planet data search PSScene | planet collect -
```

If you want to visualize this you can save it as a file:

```sh
planet data search PSScene | planet collect - > planet-search.geojson
```

This you can then open with your favorite GIS program, or see this 
[geometry visualization](cli-tips-tricks.md#geometry-inputs) section for some ideas that flow a bit better with 
the command-line.

### Sort

You can also specify the sorting with your searches. The default sort is ordered by the most recent published
images. But you can also sort by `acquired`, which is often more useful. You can sort in ascending or 
descending order. The options are are:

 * 'acquired asc'
 * 'acquired desc'
 * 'published asc'
 * 'published desc'

This lets you do things like get the ID of the most recent SkySat image taken (and that you have permissions to download):

```sh
planet data search SkySatCollect --sort 'acquired desc' --limit 1
```

And you can also just get the ID, using `jq`

```sh
planet data search SkySatCollect --sort 'acquired desc' --limit 1 - | jq -r .id
```

## Filtering

### Run a search on a bounding box

Most searches you’ll likely want to run on a geometry. To try this out you can use the following bounding box
of Iowa. You can copy it and save as a file called `geometry.geojson`

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

!!!note ".geojson and .json files both work"
    Here we save it as .geojson, but you can also save it as .json. The CLI is happy with any file
    extension, even .txt, but different extensions may make it easier to open the files with other
    programs. What’s important is that the text inside the file is valid geojson.

And then run it with this command:

```sh
planet data filter --geom geometry.geojson | planet data search PSScene --filter -
```

Note that by default all searches with the command-line return 100 results, but you can easily increase that with
the `--limit` flag:

```sh
planet data filter --geom geometry.geojson | planet data search --limit 500 PSScene --filter -
```

Creating geometries for search can be annoying in a command-line workflow, but there are some ideas in the
[Advanced CLI Tutorial](cli-tips-tricks.md#geometry-inputs).

### Date Filter

Some of the most common filtering is by date. You could get all imagery acquired before August 2021:

```sh
planet data filter --date-range acquired lt 2021-08-01 \
    | planet data search PSScene --filter -
```

The 'operator' in this case is 'less than' (`lt`). The options are:
 * `gt` - greater than
 * `gte` - greater than or equal to
 * `lt` - less than
 * `lte` - less than or equal to

You must specify which date field you want to use, either `acquired` or `published`.

You can use the flags multiple times, and they are logically 'AND'-ed together, so you can
do a search for all images in July of 2021:

```sh
planet data filter \
    --date-range acquired gte 2021-07-01 \
    --date-range acquired lt 2021-08-01 | \
planet data search PSScene --filter -
```

The date input understands [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) and 
[ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) formats. You can specify just the date,
or include the time, to search for all Planetscope images acquired within 5 seconds at a time
on July 1st 2021:

```sh
planet data filter \
    --date-range acquired gte 2021-07-01:06:20:10 \
    --date-range acquired lt 2021-07-01:06:20:15 \
    | planet data search PSScene --filter -
```

### Range Filter

The range filter uses the same operators as the date filter, but works against any numerical property. The most useful
of these tend to be ones about cloudy pixels. For example you can search for data with clear pixels greater than 90%:

```sh
planet data filter --range clear_percent gt 90 \
    | planet data search PSScene --filter -
```

### String-In Filter

For properties that are strings you can use the `string-in` filter. For example search for all planetscope imagery
with PS2 instrument:

```sh
planet data filter --string-in instrument PS2 \
    | planet data search PSScene --filter -
```

You can specify multiple strings to match, with a comma:

```sh
planet data filter --string-in instrument PS2,PSB.SD \
    | planet data search PSScene --filter -
```

Another example is to select all data in a single strip:

```sh
planet data filter --string-in strip_id 5743640 \
    | planet data search PSScene --filter -
```

Note that in all these commands we are piping the results into the search. If you don't include the pipe then you’ll
get the filter output, which can be interesting to inspect to see exactly what is sent to the server.

### Filter by asset

You can limit your search to only data with a particular asset, for example search just for 8-band analytic assets:

```sh
planet data filter --asset ortho_analytic_8b_sr \
    | planet data search PSScene --filter -
```

Or 8-band assets that also have a UDM.

```sh
planet data filter --asset ortho_analytic_8b_sr --asset udm2 \
    | planet data search PSScene --filter -
```

You can find the list of available assets in each Item Type Page, like 
[available assets](https://developers.planet.com/docs/data/psscene/#available-asset-types) for PSScene. You can see
[a table of all Item Types](https://developers.planet.com/docs/data/psscene/#available-asset-types), which links to 
the page for each with their list of asset types.

Note that the asset filter doesn't perform any validation, so if your searches aren't returning anything check to make
sure you got the asset right, and it’s valid for the item-types you’re searching.

### Permission Filter

By default, no search filters are applied. However, many people want to search only for data they have access to download
that are of standard (aka not test) quality. Therefore, these filters can be easily added with the `--permission` and
`--std-quality` flags. To use the permission and standard quality filters:

```sh
planet data filter --permission --std-quality --asset ortho_analytic_8b_sr \
    | planet data search PSScene --filter -
```

## Stats

One command that can be quite useful for getting a sense of a search is the `stats` command. It works with the
exact same filters as the main `search` command, but it just returns a count of the results, which can be 
binned by different time periods. 

This can be used for things like getting the number of items in a strip:

```sh
planet data filter --string-in strip_id 5743640 \
    | planet data stats PSScene --interval day --filter -
```

Or the number of PlanetScope scenes collected in California each year:

```
curl -s https://raw.githubusercontent.com/ropensci/geojsonio/main/inst/examples/california.geojson \
    | planet data filter --geom - \
    | planet data stats PSScene --interval year --filter - \
    | jq
```

Will result in output like:

```json
{
  "buckets": [
    {
      "count": 5261,
      "start_time": "2014-01-01T00:00:00.000000Z"
    },
    {
      "count": 34377,
      "start_time": "2015-01-01T00:00:00.000000Z"
    },
    {
      "count": 112331,
      "start_time": "2016-01-01T00:00:00.000000Z"
    },
    {
      "count": 504377,
      "start_time": "2017-01-01T00:00:00.000000Z"
    },
    {
      "count": 807086,
      "start_time": "2018-01-01T00:00:00.000000Z"
    },
    {
      "count": 806945,
      "start_time": "2019-01-01T00:00:00.000000Z"
    },
    {
      "count": 776757,
      "start_time": "2020-01-01T00:00:00.000000Z"
    },
    {
      "count": 684095,
      "start_time": "2021-01-01T00:00:00.000000Z"
    },
    {
      "count": 323557,
      "start_time": "2022-01-01T00:00:00.000000Z"
    },
    {
      "count": 56733,
      "start_time": "2023-01-01T00:00:00.000000Z"
    }
  ],
  "interval": "year",
  "utc_offset": "+0h"
}
```

You can see how the yearly output of Planet has gone up, though it actually went down in 2022 as the upgrade to SuperDove meant much larger swaths, so the number of individual items went down even as we captured the whole earth.

The API does not support an 'all time' interval to get the total of all collections for an area, but
you can easily use [jq]((cli-intro.md#jq) to total up the results of an interval count:

```sh
curl -s https://raw.githubusercontent.com/ropensci/geojsonio/main/inst/examples/california.geojson \
    | planet data filter --geom - \
    | planet data stats PSScene --interval year --filter - \
    | jq '.buckets | map(.count) | add'

```

Just pipe the results to `jq '.buckets | map(.count) | add'` and it’ll give you the total of all the values.

## Asset Activation and Download

While we recommend using the Orders or Subscriptions API’s to deliver Planet data, the Data API has the capability
to activate and download data. Only one asset can be activated at once, and there is no clipping or additional 
processing of the data like the great 'tools' of Subscriptions & Orders. But the advantage is that it can often
be faster for working with a small number of items & assets. 

### Activate an Asset

All items in the Data API have a list of assets. This includes the main imagery geotiff files, usually in a few
different formats, and also accompanying files like the [Usable Data Mask](https://developers.planet.com/docs/data/udm-2/)
 (UDM) and JSON metadata. You can't immediately download them, as they must first be created in the cloud, known as
'activated'. To activate data you need to get its item id, plus the name of the asset - the available ones
can be seen by looking at the Item’s JSON. Once you have the item id and asset type you can run the CLI

```sh
planet data asset-activate PSScene 20230310_083933_71_2431 ortho_udm2
```

This will kick off the activation process, and the command should return immediately. In this example
we’re activating the UDM, which is one of the most common things to do through the Data API, to 
first get a sense of where there are clouds before placing a proper clipping order.

### Download an Asset

Once an asset is ready you can use `asset-download` with a similar command:

```sh
planet data asset-download PSScene 20230310_083933_71_2431 ortho_udm2
```

While some assets activate almost immediately (if another user has requested
it recently), some can take a few minutes. If you try to download it before it’s active
you’ll get a message like: `Error: asset missing ["location"] entry. Is asset active?`

Thankfully the CLI has the great `asset-wait` command will complete when the asset is activated:

```sh
planet data asset-wait PSScene 20230310_083933_71_2431 ortho_udm2
```

And you can pair with download so that as soon as the asset is active it’ll be downloaded:

```sh
planet data asset-wait PSScene 20230310_083933_71_2431 ortho_udm2 && \
planet data asset-download PSScene 20230310_083933_71_2431 ortho_udm2
```

Download has a few different options:

 * `--directory` lets you specify a base directory to put the asset in.
 * `--filename` assigns a custom name to the downloaded file.
 * `--overwrite` will overwrite files if they already exist.
 * `--checksum` checks to make sure the file you downloaded is the exact same as the one on the server. This can be useful if you script thousands of files to download to detect any corruptions in that process.

## Saved Searches

The core `planet data search` command uses what is called a 'quick search' in the API. The API 
also supports what we call a '[saved searches](https://developers.planet.com/docs/apis/data/quick-saved-search/#saved-search)',
and the CLI supports this as well. 

### List Searches

You can easily get a list of all the searches you’ve made:

```sh
planet data search-list
```

This defaults to returning 100 results, but you can use `--limit` to return the number you 
specify, and set it to 0 to return all your searches. By default this returns both
your quick searches and saved searches, but you can also limit to to only return
your saved searches:

```sh
planet data search-list --search-type saved
```

If you’ve not created any saved searches it may be an empty list. You can create
saved searches with Planet Explorer, or it’s also easy with the command-line.

### Create Search

To make a new saved search you can use the exact same filter syntax as the regular `search` command,
but you must also add a 'name' to refer to the search by:

```sh
planet data filter --geom geometry.geojson \
    | planet data search-create PSScene --name 'my saved search' --filter -
```

### Run Search

When you save a new search you’ll get back the JSON describing the search. If you grab the 'id' field from it then
you can get the current results for that search:

```sh
planet data search-run da963039dbe94573a3ac9e4629d065b6
```

This is just like running a normal (quick) search, and takes similar arguments: `--limit` and `--pretty`, 
and also the same [sort](#sort) parameter (`--sort`). You can also run any previous `quick` search. 
They don't have names (the ID is just used as the name), but they are saved in the system and can be 
executed again. Searches (except those with an end date that has passed) show new results
if run later and match newly acquired imagery. 

### Update Search

You can also update an existing search to have a different set of values. This takes similar arguments, and
will overwrite the previous values.

```sh
planet data filter --string-in instrument PS2,PSB.SD \
    | planet data search-update da963039dbe94573a3ac9e4629d065b6 \
        --name 'my updated search' \
        --filter - SkySatCollect
```

### Delete Search

If you’re no longer using a search you can delete it:

```sh
planet data search-delete da963039dbe94573a3ac9e4629d065b6
```

If the deletion was successful the command-line won't print out anything except a new line. If the
search didn't exist it will say `Error: {"general": [{"message": "The requested search id does not exist"}], "field": {}}`.
You can also delete `quick` searches, which would remove them from your history.
