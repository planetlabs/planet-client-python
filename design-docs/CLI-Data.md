# Data Command-Line Interface Specification

This document lays out the command-line interface to interact with the Planet
[Data API](https://developers.planet.com/docs/apis/data/).

## Meta: Errors

All commands have the same general error behavior:

In the case of invalid options, print an error message (stderr) and set the exit
code to 2. In the case of an API error response, print the response JSON and
set code to 1. In the case of an error occurring in the SDK, print the error
message and set code to 1.

## filter

### Interface

planet data filter [OPTIONS]

Create a structured item search filter.

This command provides basic functionality for specifying a filter by
creating an AndFilter with the filters identified with the options as
inputs. This is only a subset of the complex filtering supported by the API.
For advanced filter creation, either create the filter by hand or use the
Python API.

Options:
- asset TEXT -
Filter to items with one or more of
specified assets. VALUE is a comma-separated
list of entries. When multiple entries are
specified, an implicit 'or' logic is
applied.

- date-range FIELD COMP VALUE -
Filter by date range in field. FIELD is the
name of the field to filter on. COMP can be
lt, lte, gt, or gte. DATETIME can be an
RFC3339 or ISO 8601 string.
 Filter field by date. COMP can be lt, lte, gt, or gte. VALUE is an RFC 3339 date.

- geom JSON -
Filter to items that overlap a given
geometry. Can be a json string, filename, or
'-' for stdin.

- number-in FIELD VALUE -
Filter field by numeric in. FIELD is the
name of the field to filter on. VALUE is a
comma-separated list of entries. When
multiple entries are specified, an implicit
'or' logic is applied.

- permission BOOLEAN -
Filter to assets with download permissions.
[default: True]

- range FIELD COMP FLOAT -
Filter by number range in field. FIELD is
the name of the field to filter on. COMP can
be lt, lte, gt, or gte.

- std-quality BOOLEAN - Filter to standard quality.  [default: True]

- string-in FIELD TEXT -
Filter field by numeric in. FIELD is the
name of the field to filter on. TEXT is a
comma-separated list of entries. When
multiple entries are specified, an implicit
'or' logic is applied.

- update FIELD COMP DATETIME -
Filter to items with changes to a specified
field value made after a specified date.
FIELD is the name of the field to filter on.
COMP can be gt or gte. DATETIME can be an
RFC3339 or ISO 8601 string.

Output:

A full JSON description of the search criteria.


### Usage Examples

User Story: As a CLI user I want to create a filter for items within an aoi that
have both the analytic_sr and udm2 assets.

```console
$ planet data filter \
--geom aoi.geojson \
--asset analytic_sr --asset udm2
```
response (pretty-printed)
```
{
  "config": [
    {
      "config": [
        "udm2"
      ],
      "type": "AssetFilter"
    },
    {
      "config": {
        "coordinates": [
          [
            [
              7.05322265625,
              46.81509864599243
            ],
            [
              7.580566406250001,
              46.81509864599243
            ],
            [
              7.580566406250001,
              47.17477833929903
            ],
            [
              7.05322265625,
              47.17477833929903
            ],
            [
              7.05322265625,
              46.81509864599243
            ]
          ]
        ],
        "type": "Polygon"
      },
      "field_name": "geometry",
      "type": "GeometryFilter"
    },
    {
      "config": [
        "assets:download"
      ],
      "type": "PermissionFilter"
    },
    {
      "config": [
        "standard"
      ],
      "field_name": "quality_category",
      "type": "StringInFilter"
    }
  ],
  "type": "AndFilter"
}
```

User Story: As a CLI user I want to create a filter for items with clear pixel
percent greater than 98% acquired in July 2021.

```console
$ planet data filter \
--range clear_percent gt 98 \
--date-range acquired gte 2021-07-01 \
--date-range acquired lt 2021-08-01
```
response (pretty-printed)
```
{
  "config": [
    {
      "config": {
        "gte": "2021-07-01T00:00:00Z"
      },
      "field_name": "acquired",
      "type": "DateRangeFilter"
    },
    {
      "config": {
        "lt": "2021-08-01T00:00:00Z"
      },
      "field_name": "acquired",
      "type": "DateRangeFilter"
    },
    {
      "config": {
        "gt": 98.0
      },
      "field_name": "clear_percent",
      "type": "RangeFilter"
    },
    {
      "config": [
        "assets:download"
      ],
      "type": "PermissionFilter"
    },
    {
      "config": [
        "standard"
      ],
      "field_name": "quality_category",
      "type": "StringInFilter"
    }
  ],
  "type": "AndFilter"
}
```

## search

### Interface

planet data search [OPTIONS] ITEM_TYPES [FILTER]

Execute a structured item search.

Quick searches are stored for approximately 30 days and the --name parameter will be applied to the stored quick search.

Arguments:
ITEM_TYPES - string. Comma-separated item type identifier(s).
FILTER - string. A full JSON description of search criteria. Supports file, str, and stdin.
Defaults to reading from stdin.

Options:
--pretty - flag. Pretty-print output
--limit - int. Maximum number of results to return. Defaults to 100.
--name - string. Name of the saved search.

Output:
A series of GeoJSON descriptions for each of the returned items.


### Usage Examples

User Story: As a CLI user I want to create a filter and then search for items
with clear pixel percent greater than 98% acquired in July 2021.

```
$ planet data filter \
--range clear_percent gt 98 \
--date-range acquired gte 2021-07-01 \
--date-range acquired lt 2021-08-01 | planet data search --limit 1 PSScene
```
response (pretty-printed)
```
{
  "_links": {
    "_self": "https://api.planet.com/data/v1/item-types/PSScene/items/20210709_175710_72_105e",
    "assets": "https://api.planet.com/data/v1/item-types/PSScene/items/20210709_175710_72_105e/assets/",
    "thumbnail": "https://tiles.planet.com/data/v1/item-types/PSScene/items/20210709_175710_72_105e/thumb"
  },
  "_permissions": [
    "assets.basic_analytic_4b:download",
    "assets.basic_analytic_4b_rpc:download",
    "assets.basic_analytic_4b_xml:download",
    "assets.basic_udm2:download",
    "assets.ortho_analytic_4b:download",
    "assets.ortho_analytic_4b_sr:download",
    "assets.ortho_analytic_4b_xml:download",
    "assets.ortho_udm2:download",
    "assets.ortho_visual:download",
    "assets.ps3b_analytic:download",
    "assets.ps3b_analytic_dn:download",
    "assets.ps3b_analytic_dn_xml:download",
    "assets.ps3b_analytic_xml:download",
    "assets.ps3b_basic_analytic:download",
    "assets.ps3b_basic_analytic_dn:download",
    "assets.ps3b_basic_analytic_dn_rpc:download",
    "assets.ps3b_basic_analytic_dn_xml:download",
    "assets.ps3b_basic_analytic_rpc:download",
    "assets.ps3b_basic_analytic_xml:download",
    "assets.ps3b_basic_udm:download",
    "assets.ps3b_udm:download",
    "assets.ps3b_visual_xml:download",
    "assets.ps4b_analytic:download",
    "assets.ps4b_analytic_dn:download",
    "assets.ps4b_analytic_dn_xml:download",
    "assets.ps4b_analytic_sr:download",
    "assets.ps4b_analytic_xml:download",
    "assets.ps4b_basic_analytic:download",
    "assets.ps4b_basic_analytic_dn:download",
    "assets.ps4b_basic_analytic_dn_nitf:download",
    "assets.ps4b_basic_analytic_dn_rpc:download",
    "assets.ps4b_basic_analytic_dn_rpc_nitf:download",
    "assets.ps4b_basic_analytic_dn_xml:download",
    "assets.ps4b_basic_analytic_dn_xml_nitf:download",
    "assets.ps4b_basic_analytic_nitf:download",
    "assets.ps4b_basic_analytic_rpc:download",
    "assets.ps4b_basic_analytic_rpc_nitf:download",
    "assets.ps4b_basic_analytic_xml:download",
    "assets.ps4b_basic_analytic_xml_nitf:download",
    "assets.ps4b_basic_udm:download",
    "assets.ps4b_udm:download"
  ],
  "assets": [
    "basic_analytic_4b",
    "basic_analytic_4b_rpc",
    "basic_analytic_4b_xml",
    "basic_udm2",
    "ortho_analytic_4b",
    "ortho_analytic_4b_sr",
    "ortho_analytic_4b_xml",
    "ortho_udm2",
    "ortho_visual",
    "ps3b_analytic",
    "ps3b_analytic_dn",
    "ps3b_analytic_dn_xml",
    "ps3b_analytic_xml",
    "ps3b_basic_analytic",
    "ps3b_basic_analytic_dn",
    "ps3b_basic_analytic_dn_rpc",
    "ps3b_basic_analytic_dn_xml",
    "ps3b_basic_analytic_rpc",
    "ps3b_basic_analytic_xml",
    "ps3b_basic_udm",
    "ps3b_udm",
    "ps3b_visual_xml",
    "ps4b_analytic",
    "ps4b_analytic_dn",
    "ps4b_analytic_dn_xml",
    "ps4b_analytic_sr",
    "ps4b_analytic_xml",
    "ps4b_basic_analytic",
    "ps4b_basic_analytic_dn",
    "ps4b_basic_analytic_dn_nitf",
    "ps4b_basic_analytic_dn_rpc",
    "ps4b_basic_analytic_dn_rpc_nitf",
    "ps4b_basic_analytic_dn_xml",
    "ps4b_basic_analytic_dn_xml_nitf",
    "ps4b_basic_analytic_nitf",
    "ps4b_basic_analytic_rpc",
    "ps4b_basic_analytic_rpc_nitf",
    "ps4b_basic_analytic_xml",
    "ps4b_basic_analytic_xml_nitf",
    "ps4b_basic_udm",
    "ps4b_udm"
  ],
  "geometry": {
    "coordinates": [
      [
        [
          -90.29653391265096,
          65.41358418134989
        ],
        [
          -90.41598325057312,
          65.27385324441894
        ],
        [
          -89.91560785061391,
          65.19794655099538
        ],
        [
          -89.79334184267987,
          65.33769971680782
        ],
        [
          -90.29653391265096,
          65.41358418134989
        ]
      ]
    ],
    "type": "Polygon"
  },
  "id": "20210709_175710_72_105e",
  "properties": {
    "acquired": "2021-07-09T17:57:10.722684Z",
    "anomalous_pixels": 0,
    "clear_confidence_percent": 93,
    "clear_percent": 100,
    "cloud_cover": 0,
    "cloud_percent": 0,
    "ground_control": true,
    "gsd": 3.8,
    "heavy_haze_percent": 0,
    "instrument": "PS2.SD",
    "item_type": "PSScene",
    "light_haze_percent": 0,
    "pixel_resolution": 3,
    "provider": "planetscope",
    "published": "2021-09-20T03:03:40Z",
    "publishing_stage": "finalized",
    "quality_category": "standard",
    "satellite_azimuth": 285.7,
    "satellite_id": "105e",
    "shadow_percent": 0,
    "snow_ice_percent": 0,
    "strip_id": "4673073",
    "sun_azimuth": 176.4,
    "sun_elevation": 46.9,
    "updated": "2021-09-20T09:21:14Z",
    "view_angle": 3.1,
    "visible_confidence_percent": 72,
    "visible_percent": 100
  },
  "type": "Feature"
}

```

## search-create

### Interface

```
planet data search-create [OPTIONS] NAME ITEM_TYPES [FILTER]

Create a new saved structured item search.

Arguments:
NAME - string. The name to give the saved search.
ITEM_TYPES - string. Comma-separated item type identifier(s).
FILTER - string. A full JSON description of search criteria. Supports file and stdin. Defaults to stdin.

Options:
--daily-email - flag. Send a daily email when new results are added.
--pretty - flag. Pretty-print output

Output:
A full JSON description of the created search.
```

### Usage Examples

User Story: As a CLI user I want to create a filter and then create a saved
search for items with clear pixel percent greater than 98% acquired in July 2021.

```
$ planet data filter \
--range clear_percent gt 98 \
--date-range acquired gte 2021-07-01 \
--date-range acquired lt 2021-08-01 | planet data search-create test PSScene
```
response (pretty-printed)
```
{
  "__daily_email_enabled": false,
  "_links": {
    "_self": "https://api.planet.com/data/v1/searches/ebd2eaf451d24d6f91a8d721fdeb6a1b",
    "results": "https://api.planet.com/data/v1/searches/ebd2eaf451d24d6f91a8d721fdeb6a1b/results"
  },
  "created": "2022-06-28T18:05:56.763106Z",
  "filter": {
    "config": [
      {
        "config": {
          "gte": "2021-07-01T00:00:00Z"
        },
        "field_name": "acquired",
        "type": "DateRangeFilter"
      },
      {
        "config": {
          "lt": "2021-08-01T00:00:00Z"
        },
        "field_name": "acquired",
        "type": "DateRangeFilter"
      },
      {
        "config": {
          "gt": 98.0
        },
        "field_name": "clear_percent",
        "type": "RangeFilter"
      },
      {
        "config": [
          "assets:download"
        ],
        "type": "PermissionFilter"
      },
      {
        "config": [
          "standard"
        ],
        "field_name": "quality_category",
        "type": "StringInFilter"
      }
    ],
    "type": "AndFilter"
  },
  "id": "ebd2eaf451d24d6f91a8d721fdeb6a1b",
  "item_types": [
    "PSScene"
  ],
  "last_executed": null,
  "name": "test",
  "search_type": "saved",
  "updated": "2022-06-28T18:05:56.763106Z"
}
```

## search-update

### Interface

```
planet data search-update [OPTIONS] SEARCH_ID NAME ITEM_TYPES FILTER

Update a saved search with the given search request.

Arguments:
SEARCH_ID - string. A saved search identifier.
NAME - string. The name to give the saved search.
ITEM_TYPES - string. Comma-separated item type identifier(s).
FILTER - string. A full JSON description of search criteria. Supports file and stdin.

Options:
--daily-email - flag. Send a daily email when new results are added.
--pretty - flag. Pretty-print output

Output:
A full JSON description of the updated search.
```

## search-delete

### Interface

```
planet data search-delete SEARCH_ID

Delete the existing saved search.

Arguments:
SEARCH_ID - string. A saved search identifier.

Output:
None.
```

## search-get

### Interface

```
planet data search-get [OPTIONS] SEARCH_ID

Get the existing saved search.

Arguments:
SEARCH_ID - string. A saved search identifier.

Options:
--pretty - flag. Pretty-print output

Output:
A full JSON description of the identified search.
```

## search-list

### Interface

```
planet data search-list [OPTIONS]

Options:
--pretty - flag. Pretty-print output
--limit - int. Maximum number of results to return. Defaults to 100.
--search-type - choice. Filter to a specific search type.
--sort - string. Sort order (created_asc, created_desc)

Output:
A series of JSON descriptions for each of the returned items.
```

## search-run

### Interface

```
planet data search-run SEARCH_ID

Execute a saved search.

Arguments:
REQUEST - string. A full JSON description request.

Options:
--pretty - flag. Pretty-print output
--limit - int. Maximum number of results to return. Defaults to 100.

Output:
A series of GeoJSON descriptions for each of the returned items.
```

## item-get

### Interface

```
planet data item-get [OPTIONS] ID ITEM_TYPE

Get an item.

Arguments:
ID - string. Item identifier.
ITEM_TYPE - string. Item type identifier.


Options:
--pretty - flag. Pretty-print output

Output:
A full GeoJSON description of the returned item.
```

### Usage Examples

User Story: As a CLI user I would like to get the details of an item

```
$ planet data item-get 20210819_162141_68_2276 PSScene

{"_links": {...}, ..., "type": "Feature"}
```

## asset-activate

### Interface

```
planet data asset-activate ID ITEM_TYPE ASSET_TYPE

Activate an asset.

Arguments:
ID - string. Item identifier.
ITEM_TYPE - string. Item type identifier.
ASSET_TYPE - string. Asset type identifier.

Output:
None.
```

### Usage Examples

User Story: As a CLI user I would like to activate an asset for download.

```
$ planet data asset-activate 20210819_162141_68_2276 PSScene analytic
```

User Story: As a CLI user I would like to activate, wait, and then download an
asset.

```
$ ID=20210819_162141_68_2276 && \
ITEM_TYPE=PSScene && \
ASSET_TYPE=analytic && \
planet data asset-activate $ID $ITEM_TYPE $ASSET_TYPE && \
planet data asset-wait $ID $ITEM_TYPE $ASSET_TYPE && \
planet data asset-download --directory data \
$ID $ITEM_TYPE $ASSET_TYPE

data/<psscene_naming 20210819_162141_68_2276>.tif
```

## asset-wait

### Interface

```
planet data asset-wait ID ITEM_TYPE ASSET_TYPE

Wait for an asset to be activated.

Returns when the asset state has reached ‘activated’ and the asset is available.

Arguments:
ID - string. Item identifier.
ITEM_TYPE - string. Item type identifier.
ASSET_TYPE - string. Asset type identifier.

Output:
None.
```

## asset-download

### Interface

```
planet data asset-download [OPTIONS] ID ITEM_TYPE ASSET_TYPE

Download an activated asset.

Will fail if the asset state is not activated. Consider calling `asset-wait` before this command to ensure the asset is activated.

Arguments:
ID - string. Item identifier.
ITEM_TYPE - string. Item type identifier.
ASSET_TYPE - string. Asset type identifier.

Options:
--directory - string. Download directory.
--overwrite - flag. Overwrite file if it already exists.

Output:
The full path of the downloaded file. If the quiet flag is not set, this also provides ANSI download status reporting.
```

### Usage Examples

User Story: As a CLI user I would like to download one asset into the data
directory, overwriting if the file already exists, and silencing reporting.

```
$ planet --quiet data asset-download \
--directory data \
--overwrite \
20210819_162141_68_2276 PSScene analytic
data/<psscene_naming 20210819_162141_68_2276>.tif
```

## stats

### Interface

```
planet data stats [OPTIONS] ITEM_TYPES INTERVAL FILTER

Get a bucketed histogram of items matching the filter.

Arguments:
ITEM_TYPES - string. Comma-separated item type identifier(s).
INTERVAL - string. The size of the histogram buckets (<hour, day, week, month, year>)
FILTER - string. A full JSON description filter. Supports file and stdin.

Output:
A full JSON description of the returned statistics result.
```

### Usage Examples

User Story: As a CLI user I would like to get the stats of multiple item types
with a utc offset using a file to specify the filter.

```
$ planet data stats --utc-offset +1:00 \
PSScene,PSOrthoTile day filter-desc.json

<unedited API response json>
```
