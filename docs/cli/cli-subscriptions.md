---
title: CLI for Subscriptions API Tutorial
---

## Introduction

The `planet subscriptions` command enables interaction with the
[Subscriptions API](https://developers.planet.com/apis/subscriptions/)
that make it possible to set up a recurring search criteria. Using `planet subscriptions`, you can automatically process
and deliver new imagery to a cloud bucket. It also has a powerful 'backfill' capability
to bulk order historical imagery to your area of interest. This tutorial takes you
through the main commands available in the CLI.

## Core Workflows

### Create a Subscription

Since there is no UI to easily create subscriptions we’ll start with making a new one.

```json
{
  "name": "First Subscription",
  "source": {
    "type": "catalog",
    "parameters": {
      "asset_types": [
        "ortho_analytic_8b"
      ],
      "end_time": "2023-11-01T00:00:00Z",
      "geometry": {
        "coordinates": [
          [
            [
              139.5648193359375,
              35.42374884923695
            ],
            [
              140.1031494140625,
              35.42374884923695
            ],
            [
              140.1031494140625,
              35.77102915686019
            ],
            [
              139.5648193359375,
              35.77102915686019
            ],
            [
              139.5648193359375,
              35.42374884923695
            ]
          ]
        ],
        "type": "Polygon"
      },
      "item_types": [
        "PSScene"
      ],
      "start_time": "2023-03-17T04:08:00.0Z"
    }
  },
  "tools": [
    {
      "type": "clip",
      "parameters": {
        "aoi": {
          "coordinates": [
            [
              [
                139.5648193359375,
                35.42374884923695
              ],
              [
                140.1031494140625,
                35.42374884923695
              ],
              [
                140.1031494140625,
                35.77102915686019
              ],
              [
                139.5648193359375,
                35.77102915686019
              ],
              [
                139.5648193359375,
                35.42374884923695
              ]
            ]
          ],
          "type": "Polygon"
        }
      }
    }
  ],
  "delivery": {
    "type": "google_cloud_storage",
    "parameters": {
      "bucket": "pl-sub-bucket",
      "credentials": "<REDACTED>"
    }
  }
}
```

This is a full subscriptions JSON request, with the credentials redacted, so you’ll have
to replace your own for it to work. Below we’ll show the convenience methods that will
help create a custom one more easily. If you'd like to get things working for now then
just replace the 'delivery' section with your cloud credentials, see the
[core subscriptions delivery docs](https://developers.planet.com/docs/subscriptions/delivery/)
for more information.

To create a new subscription with the CLI, use the `create` command and the json file you just created:

```sh
planet subscriptions create my-subscription.json
```

**Note:** The above command assumes that you’ve saved the subscriptions JSON as `my-subscription.json` and that you’ve replaced the delivery information with your own bucket and credentials.

### List Subscriptions

Now that you’ve got a subscription working you can make use of the other commands.

```sh
planet subscriptions list
```

outputs the JSON for your first 100 subscriptions. If you'd like more you can set the `--limit`
parameter higher, or you can set it to 0 and there will be no limit.

You can get nicer formatting with `--pretty` or pipe it into `jq`, just like the other Planet
CLI’s.

#### Filtering

The `list` command supports filtering on a variety of fields:
* `--created`: Filter on the subscription creation time or an interval of creation times.
* `--end-time`: Filter on the subscription end time or an interval of end times.
* `--hosting`: Filter on subscriptions containing a hosting location (e.g. SentinelHub). Accepted values are `true` or `false`.
* `--name-contains`: Filter on subscriptions with a name that contains the provided string.
* `--name`: Filter on subscriptions with a specific name
* `--source-type`: Filter by the source type of the subscription. For the full list of available source types, see [Subscription Source Types](https://developers.planet.com/docs/subscriptions/source/#subscription-source-types). Multiple source type args are allowed.
* `--start-time`: Filter on the subscription start time or an interval of start times.
* `--status`: Filter on the status of the subscription. Status options include `running`, `cancelled`, `preparing`, `pending`, `completed`, `suspended`, and `failed`. Multiple status args are allowed.
* `--updated`: Filter on the subscription update time or an interval of updated times.

Datetime args (`--created`, `end-time`, `--start-time`, and `--updated`) can either be a date-time or an interval, open or closed. Date and time expressions adhere to RFC 3339. Open intervals are expressed using double-dots.
* A date-time: `2018-02-12T23:20:50Z`
* A closed interval: `2018-02-12T00:00:00Z/2018-03-18T12:31:12Z`
* Open intervals: `2018-02-12T00:00:00Z/..` or `../2018-03-18T12:31:12Z`

To list currently active subscriptions:
```sh
planet subscriptions list --status running
```

To list subscriptions with the `catalog` source type:
```sh
planet subscriptions list --source-type catalog
```

To list subscriptions that were created in 2024:
```sh
planet subscriptions list --created 2024-01-01T00:00:00Z/2025-01-01T00:00:00Z
```

To list subscriptions with an end time after Jan 1, 2025:
```sh
planet subscriptions list --end-time 2025-01-01T00:00:00Z/..
```

To list subscriptions with a hosting location:
```sh
planet subscriptions list --hosting true
```

#### Sorting

The `list` command also supports sorting the subscriptions on one or more fields: `name`, `created`, `updated`, `start_time`, and `end_time`. The sort direction can be specified by appending ` ASC` or ` DESC` to the field name (default is ascending).

When multiple fields are specified, the sort order is applied in the order the fields are listed.

Sorting examples:
* `--sort-by name`: sorts subscriptions by name alphabetically.
* `--sort-by "created DESC"`: sorts subscriptions by most recently created.
* `--sort-by "updated DESC"`: sorts subscriptions by most recently updated.
* `--sort-by "start_time ASC"`: sorts subscriptions by start time (earliest to latest)
* `--sort-by "end_time DESC"`: sorts subscriptions by end time (latest to earliest)
* `--sort-by "name,start_time DESC"`: sorts subscriptions by name ascending first, and start time descending second.

### Get Subscription

To get the full details on a single subscription you can take the id from your list and use the
`get` command:

```sh
planet subscriptions get cb817760-1f07-4ee7-bba6-bcac5346343f
```

### Subscription Results

To see what items have been delivered to your cloud bucket you can use the `results` command:

```sh
planet subscriptions results SUBSCRIPTION_ID
```

`SUBSCRIPTION_ID` above is a placeholder for a unique subscription identifier, which will be a UUID like `cb817760-1f07-4ee7-bba6-bcac5346343f`.

By default this displays the first 100 results. As with other commands, you can use the `--limit` param to
set a higher limit, or set it to 0 to see all results (this can be quite large with subscriptions results).

You can also filter by status:

```sh
planet subscriptions results SUBSCRIPTION_ID --status processing
```

See the Subscriptions API documentation for the [official list of available statuses](https://developers.planet.com/docs/subscriptions/#subscription-status).

#### Results as comma-separated values (CSV)

Planetary Variable subscribers can benefit from retrieving results as a CSV. The results contain variable statistics and can serve as data for time series analysis and visualization.

```sh
planet subscriptions results SUBSCRIPTION_ID --csv
```

### Update Subscription

You can update a subscription that is running, for example to change the 'tools' it’s using or to alter
its geometry. To do this you must submit the full subscription creation JSON, so the easiest way is to
get it with `get` and then alter the values.

```sh
planet subscriptions update cb817760-1f07-4ee7-bba6-bcac5346343f \
    my-updated-subscriptions.json
```

### Update Subscription Via Patch

To update a running subscription with *only* the attributes to be updated, use the `patch` method.

```sh
planet subscriptions patch cb817760-1f07-4ee7-bba6-bcac5346343f \
    patched-attributes.json
```

### Cancel Subscription

Cancelling a subscription is simple with the CLI:

```sh
planet subscriptions cancel cb817760-1f07-4ee7-bba6-bcac5346343f
```

That will stop the subscription from producing any more results, but it will stay in the system so you can
continue to list and get it.

## Subscription Request Conveniences

There are a couple of commands that can assist in creating the subscription JSON, used for creation and updates.
A subscription request is a pretty complicated command, consisting of a search, a cloud delivery, as well as
tools to process the data plus notifications on the status.

### Catalog Request

The first place to start is the `request-catalog` command, which generates all the JSON for the
[catalog source](https://developers.planet.com/docs/subscriptions/source/#catalog-source-type) block. The core
of this is quite similar to a Data API search request, though with more required fields. The minimal
required commands would be a request like:

```sh
planet subscriptions request-catalog \
    --item-types PSScene \
    --asset-types ortho_analytic_8b \
    --geometry geometry.geojson \
    --start-time 2023-03-17T04:08:00.0Z
```

You request which item types you want to deliver, and the asset types for it. Note that the `asset-types` are a bit
different than the `--bundle` command in Orders, a bundle is a set of asset-types. You can see the list of asset types
for [PSScene](https://developers.planet.com/docs/data/psscene/#available-asset-types), [SkySatCollect](https://developers.planet.com/docs/data/skysatcollect/),
and [SkySatScene](https://developers.planet.com/docs/data/skysatscene/#available-asset-types). The other item-types
also have similar listings of their asset types. For the required `start-time` and optional `end-time` you must
use dates formatted as RFC 3339 or ISO 8601 formats. A nice time converter is available at [time.lol](https://time.lol/).
Just select 'ISO 8601' (third one on the list), or 'RFC 3339' (8th on the list).

#### Geometry

In this case we are using a locally saved `geometry.geojson`, which would look like the following if you wanted
it to match the subscription creation request at the top of this documentation page:

```json
{
    "coordinates":
    [
        [
            [
                139.5648193359375,
                35.42374884923695
            ],
            [
                140.1031494140625,
                35.42374884923695
            ],
            [
                140.1031494140625,
                35.77102915686019
            ],
            [
                139.5648193359375,
                35.77102915686019
            ],
            [
                139.5648193359375,
                35.42374884923695
            ]
        ]
    ],
    "type": "Polygon"
}
```

Note this is just the coordinates of either a polygon or multipolygon - the operation
is not flexible to input like the orders command.

#### RRule

RRule lets you specify a subscription that repeats at various time intervals:

```sh
planet subscriptions request-catalog \
    --item-types PSScene \
    --asset-types ortho_analytic_8b \
    --geometry geometry.geojson \
    --start-time 2023-03-17T04:08:00.0Z \
    --rrule 'FREQ=MONTHLY;BYMONTH=3,4,5,6,7,8,9,10'
```

For more information on the `rrule` parameter see the [recurrence rules](https://developers.planet.com/docs/subscriptions/source/#rrules-recurrence-rules)
documentation.

#### Filter

You can pass in a filter from the data API:

```sh
planet data filter --range clear_percent gt 90 > filter.json
planet subscriptions request-catalog \
    --item-types PSScene \
    --asset-types ortho_analytic_8b \
    --geometry geometry.geojson \
    --start-time 2022-08-24T00:00:00-07:00 \
    --filter filter.json
```

And you can even pipe it in directly:

```sh
planet data filter --range clear_percent gt 90 \
    | planet subscriptions request-catalog \
        --item-types PSScene \
        --asset-types ortho_analytic_8b \
        --geometry geometry.geojson \
        --start-time 2022-08-24T00:00:00-07:00 \
        --filter -
```

Do not bother with geometry or date filters, as they will be ignored in favor of the `--start-time` and `--geometry` values that are required.

#### Publishing stages and time range types

By using the `--time-range-type` you can choose to temporally filter by
acquisition or publication time. The `--publishing-stage` option allows you to
receive the earliest preview imagery or wait until finalized imagery is
available. See [Catalog Source
Types:Parameters](https://developers.planet.com/docs/subscriptions/source/#parameters)
for more details.

```sh
planet subscriptions request-catalog \
    --item-types PSScene \
    --asset-types ortho_analytic_8b \
    --geometry geometry.geojson \
    --start-time 2022-08-24T00:00:00-07:00 \
    --time-range-type acquired \
    --publishing-stage finalized \
    --filter filter.json
```

*New in version 2.1*

#### Saving the output

You’ll likely want to save the output of your `request-catalog` call to disk, so that you can more easily use it in constructing the complete subscription
request.

```sh
planet data filter --range clear_percent gt 90 > filter.json
planet subscriptions request-catalog \
    --item-types PSScene \
    --asset-types ortho_analytic_8b \
    --geometry geometry.geojson \
    --start-time 2022-08-24T00:00:00-07:00 \
    --filter filter.json > request-catalog.json
```

### Planetary Variable Request

Subscribing to Planetary Variables is much like subscribing to imagery from
Planet's catalog. The `planet subscriptions request-pv` command can construct the source
part of a Planetary Variable request like `request-catalog` does for cataloged
imagery. Planetary Variable subscriptions come in 4 types and are further
subdivided within these types by an identifier. See [Subscribing to Planetary
Variables](https://developers.planet.com/docs/subscriptions/pvs-subs/#planetary-variables-types-and-ids)
for details. To constrain data delivery by space and time, you will use the
`--geometry`, `start-time`, and `end-time` options described above.

```sh
planet subscriptions request-pv \
    --var-type biomass_proxy \
    --var-id BIOMASS-PROXY_V3.0_10 \
    --geometry geometry.geojson \
    --start-time 2022-08-24T00:00:00-07:00 > request-pv.json
```

### Subscription Tools

Now we’ll dive into some of the tools options for subscriptions. These are quite similar to the tools for
orders, but unfortunately the syntax is subtly different, and there are less tools supported. Just like
for Orders, future of the versions of the CLI will likely add `tools` convenience methods, you can follow issue
[#601](https://github.com/planetlabs/planet-client-python/issues/601).

#### Clipping

The most used tool is the `clip` operation, which lets you pass a geometry to the
Subscriptions API and it creates new images that only have pixels within the geometry you
gave it. 99% of the time you will want to clip to the subscription geometry. The easiest way to do this is to use the `--clip-to-source` option added to the `subscriptions request` command in version 2.1.

```sh
planet subscriptions request \
    --name 'Clipped Subscription' \
    --source request-catalog.json \
    --delivery cloud-delivery.json \
    --clip-to-source
```

*New in version 2.1*


#### Additional Tools

There are some other tools that are often good to include. To use more than one tool
just put them in an array in the JSON:

The toolchain options and format are given in
[Supported Tools](https://developers.planet.com/docs/subscriptions/tools/#supported-tools)
section of the subscriptions docs:

Example: `more-tools.json`
```
[
    {
        "type": "toar",
        "parameters":
        {
            "scale_factor": 10000
        }
    },
    {
        "type": "reproject",
        "parameters":
        {
            "projection": "WGS84",
            "kernel": "cubic"
        }
    },
    {
        "type": "harmonize",
        "parameters":
        {
            "target_sensor": "Sentinel-2"
        }
    },
    {
        "type": "file_format",
        "parameters":
        {
            "format": "COG"
        }
    }
]
```

### Delivery

One other essential block is the `delivery` JSON. Like with tools there is no convenience
method, as of yet. You must write out the JSON for this section.
You can find the full documentation for the delivery options in
the [Subscriptions Delivery documentation](https://developers.planet.com/docs/subscriptions/delivery/).

An example of a delivery.json file that you would save as a file to pass into the
`subscriptions request` command is:

```json
{
    "type": "azure_blob_storage",
    "parameters":
    {
        "account": "accountname",
        "container": "containername",
        "sas_token": "sv=2017-04-17u0026si=writersr=cu0026sig=LGqc",
        "storage_endpoint_suffix": "core.windows.net"
    }
}
```

The main documentation page also has the parameters for Google Cloud, AWS and Oracle.

### Subscriptions Request

Once you’ve got all your sub-blocks of JSON saved you’re ready to make a complete subscriptions request with the `subscriptions request` command:

The above will print it nicely out so you can see the full request. You can write it out
as a file, or pipe it directly into `subscriptions create` or `subscriptions update`:

```sh
planet subscriptions request \
    --name 'First Subscription' \
    --source request-catalog.json \
    --tools tools.json \
    --delivery cloud-delivery.json \
    | planet subscriptions create -
```

#### Sentinel Hub Hosting

When creating a new subscription, you can include hosting options directly using the --hosting and --collection-id flags.

- The --hosting option is optional and currently supports sentinel_hub as its only value.
- The --collection_id is also optional. If you decide to use this, ensure that the subscription request and the collection have matching bands. If you're unsure, allow the system to create a new collection for you by omitting the --collection_id option. This will ensure the newly set-up collection is configured correctly, and you can subsequently add items to this collection as needed.
- You may also input --hosting as a JSON file. The file should be formatted:

```sh
planet subscriptions request \
    --name 'First Subscription' \
    --source request-catalog.json \
    --tools tools.json \
    --hosting sentinel_hub \
    | planet subscriptions create -
```

For more information on Sentinel Hub hosting, see the [Subscriptions API documentation](https://developers.planet.com/docs/subscriptions/delivery/#delivery-to-sentinel-hub-collection) and the [Linking Planet User to Sentinel Hub User
](https://support.planet.com/hc/en-us/articles/16550358397469-Linking-Planet-User-to-Sentinel-Hub-User) support post.