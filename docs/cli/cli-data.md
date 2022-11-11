---
title: CLI for Planet Data API Tutorial
---

## Introduction

The `planet data` commands enable interaction with the [Data API](https://developers.planet.com/docs/apis/data/),
which lets you search Planet's catalog (including select public datasets like Sentinel 2 and Landsat 8).
Most `data` cli commands are simple wrappers around the
[Planet Data API](https://developers.planet.com/docs/apis/data/reference/)
commands with the only difference being the addition of functionality to create
a search filter, activate an asset, poll for when activation is complete, and
download the asset.

### Filter

The search-related Data API CLI commands require a search filter. The `planet data filter`
command provides basic functionality for generating this filter. The command works similar to 
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

We'll explore the full `filter` CLI options below. Note that you do not *have* to use the filter command,
you can always just create the [filter json](https://developers.planet.com/docs/apis/data/searches-filtering/)
by any other means.

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