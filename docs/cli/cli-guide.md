---
title: No-Code CLI Guide
---


## Authentication

The `auth` command allows the CLI to authenticate with Planet servers. Before
any other command is run, the CLI authentication should be initiated with

```console
$ planet auth init
```

To store the authentication information in an environment variable, e.g.
for passing into a Docker instance:

```console
$ export PL_API_KEY=$(planet auth value)
```


## Collecting Results

Some API calls, such as searching for imagery and listing orders, return a
varying, and potentially large, number of results. These API responses are
paged. The SDK manages paging internally and the associated cli commands
output the results as a sequence. These results can be converted to a JSON blob
using the `collect` command. When the results
represent GeoJSON features, the JSON blob is a GeoJSON FeatureCollection.
Otherwise, the JSON blob is a list of the individual results.

```console
$ planet data search PSScene filter.json | planet collect -
```

contents of `filter.json`:

```json
{
   "type":"DateRangeFilter",
   "field_name":"acquired",
   "config":{
      "gt":"2019-12-31T00:00:00Z",
      "lte":"2020-01-31T00:00:00Z"
   }
}
```

## Orders API

Most `orders` cli commands are simple wrappers around the
[Planet Orders API](https://developers.planet.com/docs/orders/reference/#tag/Orders)
commands.


### Create Order File Inputs

Creating an order supports JSON files as inputs and these need to follow certain
formats.


#### --cloudconfig
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

#### --clip
The file given with the `--clip` option should contain valid [GeoJSON](https://geojson.org/).
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

#### --tools
The file given with the `--tools` option should contain JSON that follows the
format for a toolchain, the "tools" section of an order. The toolchain options
and format are given in
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

## Data API

Most `data` cli commands are simple wrappers around the
[Planet Data API](https://developers.planet.com/docs/apis/data/reference/)
commands with the only difference being the addition of functionality to create
a search filter, activate an asset, poll for when activation is complete, and
download the asset.


### Filter

The search-related Data API CLI commands require a search filter. The filter
CLI command provides basic functionality for generating this filter. For
more advanced functionality, use the Python API `data_filter` commands.

The following is an example of using the filter command to generate a filter
that specifies an aquired date range and AOI:

```console
$ planet data filter \
    --date-range acquired gte 2022-01-01 \
    --date-range acquired lt 2022-02-01 \
    --geom aoi.json
```

This can be fed directly into a search command e.g.:

```console
$ planet data filter --geom aoi.json | planet data search PSScene -
```
