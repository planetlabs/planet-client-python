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

```console
planet data filter [OPTIONS]

Create a structured search criteria. This command provides basic functionality for specifying a filter by creating an AndFilter with the filters identified with the options as inputs. This is only a subset of the complex filtering supported by the API. For advanced filter creation, either create the filter by hand or use the Python API.

Options:
- asset TEXT    Filter to items with one or more of
                                  specified assets. VALUE is a comma-separated
                                  list of entries. When multiple entries are
                                  specified, an implicit 'or' logic is
                                  applied.
- date-range FIELD COMP VALUE (str, str, str). Filter field by date. COMP can be lt, lte, gt, or gte. VALUE is an RFC 3339 date.
- geom GEOM (json). Specify a geometry filter as geojson.
- number-in FIELD VALUES... (str, list of float) Filter field by numeric in.
- permission, boolean. Filter to assets with download permissions. Defaults to true
- range FIELD COMP VALUE... (str, str, float) Filter field by numeric range. COMP can be lt, lte, gt, or gte.
- string-in FIELD VALUES... (str, list of str) Filter field by string in.
- update FIELD COMP VALUE (str, str, str) Filter to items with changes to a specified field value made after a specified date. COMP can be gt or gte. VALUE is an RFC 3339 date.

Output:
A full JSON description of the search criteria.
```

### Usage Examples

User Story: As a CLI user I want to create a filter for items within an aoi that
have both the analytic_sr and udm2 assets.

```
$ planet data filter \
--geom aoi.geojson \
--asset analytic_sr --asset udm2 

{"filter": {"type":"AndFilter", "config":[{"type":"GeometryFilter", …}]}}
```

User Story: As a CLI user I want to create a filter for items with clear pixel 
percent greater than 98% acquired in July 2021.

```
$ planet data filter \
--range clear_percent gt 98 \
--date-range acquired gte 2021-07-01 \
--date-range acquired lt 2021-08-01

{"filter": {"type":"AndFilter", "config":[{"type":"DateRangeFilter", …}]}}
```

## search-quick

### Interface

```
planet data search-quick [OPTIONS] ITEM_TYPES FILTER

Execute a structured item search.

Quick searches are stored for approximately 30 days and the --name parameter will be applied to the stored quick search.

Arguments:
ITEM_TYPES - string. Comma-separated item type identifier(s).
FILTER - string. A full JSON description of search criteria. Supports file and stdin.

Options:
--pretty - flag. Pretty-print output
--limit - int. Maximum number of results to return. Defaults to 100.
--name - string. Name of the saved search.

Output:
A series of GeoJSON descriptions for each of the returned items.
```

### Usage Examples

User Story: As a CLI user I want to create a filter and then search for items 
with clear pixel percent greater than 98% acquired in July 2021.

```
$ planet data filter \
--range clear_percent gt 98 \
--date-range acquired gte 2021-07-01 \
--date-range acquired lt 2021-08-01 | planet data search-quick -
{"_links": {...}, ..., "type": "Feature"}
{"_links": {...}, ..., "type": "Feature"}
{"_links": {...}, ..., "type": "Feature"}
```

## search-create

### Interface

```
planet data search-create [OPTIONS] NAME ITEM_TYPES FILTER

Create a new saved structured item search.

Arguments:
NAME - string. The name to give the saved search.
ITEM_TYPES - string. Comma-separated item type identifier(s).
FILTER - string. A full JSON description of search criteria. Supports file and stdin.

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
--date-range acquired lt 2021-08-01 | planet data search-create -
{“_links”: …}
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

Options:
--utc-offset - string. A "ISO 8601 UTC offset" (e.g. +01:00 or -08:00) that can be used to adjust the buckets to a users time zone.

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
