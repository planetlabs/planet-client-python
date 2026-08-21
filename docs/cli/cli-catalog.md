---
title: CLI for Catalog API Tutorial
---

## Introduction

The `planet catalog` command provides an interface for browsing and searching the
[Planet Catalog API](https://docs.planet.com/develop/apis/catalog/), an
implementation of the [STAC](https://stacspec.org/) (SpatioTemporal Asset
Catalog) specification. This tutorial takes you through the main commands
available in the CLI.

## Authentication

!!! note

    Unlike the other Planet APIs, the Catalog API is not served from
    `api.planet.com`. It is hosted by Sentinel Hub and authenticates with an
    OAuth bearer token, so a **plain Planet API key will not work**.

Log in with an OAuth profile before using these commands:

```sh
planet auth login
```

See the [client authentication documentation](../auth/auth-overview.md) for the
available profiles and for machine-to-machine (M2M) credentials.

## Deployments

The API has two regional deployments. The CLI defaults to `eu-central-1`; use
`--base-url` to target `us-west-2`:

```sh
planet catalog --base-url https://services-uswest2.sentinel-hub.com/catalog/v1 collections list
```

## Core Workflows

### Explore the Catalog

The landing page is the root STAC Catalog. It lists the conformance classes the
server implements and links to the collections and search endpoints.

```sh
planet catalog landing-page --pretty
```

To see just the specifications the API conforms to:

```sh
planet catalog conformance
```

### List Collections

Every item in the catalog belongs to a collection. To see the collections
available to your account:

```sh
planet catalog collections list
```

You can get nicer formatting with `--pretty` or pipe it into `jq`, just like the
other Planet CLIs. For example, to list only the collection IDs:

```sh
planet catalog collections list | jq -r '.[].id'
```

To describe a single collection, including its spatial and temporal extents and
its `summaries`:

```sh
planet catalog collections get sentinel-2-l2a
```

### Discover Filterable Properties

Before writing a filter, check which properties a collection can be filtered on.
The `queryables` command returns a JSON Schema of the valid terms:

```sh
planet catalog collections queryables sentinel-2-l2a --pretty
```

### List the Items in a Collection

The `items list` command pages through a collection, printing one item per line:

```sh
planet catalog items list sentinel-2-l2a \
  --bbox 13,45,14,46 \
  --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \
  --limit 5
```

The `--datetime` option accepts an RFC 3339 instant or an interval. Open
intervals use double-dots, e.g. `2018-02-12T00:00:00Z/..`.

To fetch one known item:

```sh
planet catalog items get sentinel-2-l2a \
  S2B_MSIL2A_20201229T101329_N0214_R022_T33TUK_20201229T115442
```

### Search

There are two search commands, matching the two operations the API exposes.

#### `search` (full-featured)

`planet catalog search` uses `POST /search`. It searches multiple collections and
accepts CQL2 JSON filters and include/exclude field objects.

```sh
planet catalog search \
  --collections sentinel-2-l2a \
  --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \
  --bbox 13,45,14,46 \
  --filter 'eo:cloud_cover>90' \
  --limit 5
```

To supply a CQL2 JSON filter instead of CQL2 text, pass `--filter-lang cql2-json`:

```sh
planet catalog search \
  --collections sentinel-2-l2a \
  --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \
  --filter '{"op": ">", "args": [{"property": "eo:cloud_cover"}, 90]}' \
  --filter-lang cql2-json
```

Trim the response payload with `--fields`, which takes a JSON object with
`include` and/or `exclude` lists:

```sh
planet catalog search \
  --collections sentinel-2-l2a \
  --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \
  --fields '{"include": ["id", "bbox"], "exclude": ["geometry", "links", "assets"]}'
```

Search an area given as a GeoJSON geometry rather than a bounding box with
`--intersects`, which accepts a JSON string, a filename, or `-` for stdin:

```sh
planet catalog search \
  --collections sentinel-2-l2a \
  --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \
  --intersects aoi.geojson
```

#### `simple-search` (shorthand)

`planet catalog simple-search` uses `GET /search`. It takes exactly one
collection, a CQL2 **text** filter, and a comma-separated `--fields` string:

```sh
planet catalog simple-search \
  --collections sentinel-2-l2a \
  --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \
  --bbox 13,45,14,46 \
  --fields 'id,type,-geometry,bbox,properties,-links,-assets'
```

### Distinct Values

Both search commands support `--distinct`, which returns the unique values of a
single property instead of full item metadata. This is a cheap way to find out
which acquisition dates exist in an area and time range:

```sh
planet catalog search \
  --collections sentinel-2-l2a \
  --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \
  --bbox 13,45,14,46 \
  --distinct date
```

As with `--filter`, the properties you can request depend on the collection.

## Paging

The listing and search commands page automatically and print one result per
line, so you can stream them straight into `jq` or a file.

* `--limit` caps the **total** number of results returned. Set it to `0` for no
  maximum. It defaults to 100.
* `--page-size` controls how many results are fetched per request. The API
  accepts 1-100.

For example, to pull every matching item rather than the first 100:

```sh
planet catalog search \
  --collections sentinel-2-l2a \
  --datetime 2020-12-10T00:00:00Z/2020-12-30T00:00:00Z \
  --bbox 13,45,14,46 \
  --limit 0 > items.ndjson
```
