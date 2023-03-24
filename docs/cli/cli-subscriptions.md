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

Since there is no UI to easily create subscriptions we'll start with making a new one. 

```
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

This is a full subscriptions JSON request, with the credentials redacted, so you'll have 
to replace your own for it to work. Below we'll show the convenience methods that will 
help create a custom one more easily, but if you'd just like to get things working then 
just replace the 'delivery' section with your cloud credentials, see the 
[core subscriptions delivery docs](https://developers.planet.com/docs/subscriptions/delivery/) 
for more information. 

To create a new subscription with the CLI you just use the `create` command:

```
planet orders subscriptions create my-subscription.json
```

The above command assumes that you've saved the subscriptions JSON as `my-subscription.json`.

### List Subscriptions

Now that you've got a subscription working you can make use of the other commands.

```
planet subscriptions list
```

Will output the JSON for your first 100 subscriptions. If you'd like more you can set the `--limit` 
parameter higher, or you can set it to 0 and there will be no limit. 

You can get nicer formatting with `--pretty` or pipe it into `jq`, just like the other Planet
CLI's.

The `list` command also supports filtering by the status of the subscription:

```
planet subscriptions list --status running
```

gives you just the currently active subscriptions. The other available statuses are:
`cancelled`, `preparing`, `pending`, `completed`, `suspended`, and `failed`.

### Describe Subscription

To get the full details on a single subscription you can take the id from your list and use the
`describe` command:

```
planet subscriptions describe cb817760-1f07-4ee7-bba6-bcac5346343f
```

### Subscription Results

To see what items have been delivered to your cloud bucket you can use the `results` command:

```
planet subscriptions results cb817760-1f07-4ee7-bba6-bcac5346343f
```

By default it will show the first 100 results, but as with other commands, you can use the `--limit` param to 
set a higher limit, or set it to 0 to see all results (this can be quite large with subscriptions results).

You can also filter by status:

```
planet subscriptions results --status processing
```

The available statuses are `created`, `queued`, `processing`, `failed`, and `success`. Note it's quite useful
to use `jq` to help filter out results as well.  

### Update Subscription

You can update a subscription that is running, for example to change the 'tools' it's using or to alter
its geometry. To do this you must submit the full subscription creation JSON, so the easiest way is to
get it with `describe` and then alter the values.

```
planet subscriptions update cb817760-1f07-4ee7-bba6-bcac5346343f my-updated-subscriptions.json
```

### Cancelling Subscription

Cancelling a subscription is simple with the CLI:

```
planet subscriptions cancel cb817760-1f07-4ee7-bba6-bcac5346343f
```

That will stop the subscription from producing any more results, but it will stay in the system so you can
continue to list and describe it.

## Subscription Request Conveniences

There are a couple of commands that can assist in creating the subscription JSON, used for creation and updates.
A subscription request is a pretty complicated command, consisting of a search, a cloud delivery, as well as 
tools to process the data plus notifications on the status. 

### Catalog Request

The first place to start is the `request-catalog` command, which generates all the JSON for the 
[catalog source](https://developers.planet.com/docs/subscriptions/source/#catalog-source-type) block. The core
of this is quite similar to a Data API search requests, though with more required fields. The minimal
required commands would be a request like:

```
planet subscriptions request-catalog --item-types PSScene --asset-types ortho_analytic_8b --geometry geometry.geojson \
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

```
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

```
planet subscriptions request-catalog --item-types PSScene --asset-types ortho_analytic_8b --geometry geometry.geojson \
--start-time 2023-03-17T04:08:00.0Z --rrule 'FREQ=MONTHLY;BYMONTH=3,4,5,6,7,8,9,10'
```

For more information on the `rrule` parameter see the [recurrance rules](https://developers.planet.com/docs/subscriptions/source/#rrules-recurrence-rules)
documentation.  

#### Filter

You can pass in a filter from the data API:

```
planet data filter --range clear_percent gt 90 > filter.json
planet subscriptions request-catalog --item-types PSScene --asset-types ortho_analytic_8b --geometry geometry.geojson \
--start-time 2022-08-24T00:00:00-07:00 --filter filter.json
```

And you can even pipe it in directly:

```
planet data filter --range clear_percent gt 90 | planet subscriptions request-catalog --item-types PSScene --asset-types ortho_analytic_8b --geometry geometry.geojson --start-time 2022-08-24T00:00:00-07:00 --filter -
```

Just note that you should not use geometry or date filters, as they will be ignored in favor of the `--start-time` and `--geometry` values that are required.

#### Saving the output

You'll likely want to save the output of your `request-catalog` call to disk, so that you can more easily use it in constructing the complete subscription
request. 

```
planet data filter --range clear_percent gt 90 > filter.json
planet subscriptions request-catalog --item-types PSScene --asset-types ortho_analytic_8b --geometry geometry.geojson \
--start-time 2022-08-24T00:00:00-07:00 --filter filter.json > request-catalog.json
```

### Subscription Tools

Now we'll dive into some of the tools options for subscriptions. These are quite similar to the tools for 
orders, but unfortunately the syntax is subtly different, and there are less tools supported. Just like 
for Orders, future of the versions of the CLI will likely add `tools` convenience methods, you can follow issue
[#601](https://github.com/planetlabs/planet-client-python/issues/601). 

#### Clipping

The most used tool is the `clip` operation, which lets you pass a geometry to the
Subscriptions API and it creates new images that only have pixels within the geometry you
gave it. We'll use the same geometry from [above](#geometry), as it is quite
typical to use the same subscription geometry as the clip geometry, so you don't get
any pixels outside of your area of interest (99.9% of all subscriptions use the clip
tool, so it's strongly recommended to also use clip). The proper 'clip' tool for it
would be:

```
[
    {
        "type": "clip",
        "parameters": {
            "aoi": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            -163.828125,
                            -44.59046718130883
                        ],
                        [
                            181.7578125,
                            -44.59046718130883
                        ],
                        [
                            181.7578125,
                            78.42019327591201
                        ],
                        [
                            -163.828125,
                            78.42019327591201
                        ],
                        [
                            -163.828125,
                            -44.59046718130883
                        ]
                    ]
                ]
            }
        }
    }
]
```

You can save this tools as `tools.json` to include in the `subscriptions request` 
command.

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

One other essential block is the `delivery` JSON. Like with tools there's as of yet
not convenience method, so you'll have to write out the JSON for this section, but we
hope to have one soon. You can find the full documentation for the delivery options in
the [Subscriptions Delivery documentation](https://developers.planet.com/docs/subscriptions/delivery/).

An example of a delivery.json file that you would save as a file to pass into the 
`subscriptions request` command is:

```
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

Once you've got all your sub-blocks of JSON saved you're ready to make a complete 
subscriptions request with the `subscriptions request` command:

```
planet subscriptions request --name 'First Subscription' --source request-catalog.json \
--tools tools.json --delivery cloud-delivery.json --pretty
```

The above will print it nicely out so you can see the full request. You can write it out
as a file, or pipe it directly into `subscriptions create` or `subscriptions update`:

```
planet subscriptions request --name 'First Subscription' --source request-catalog.json \
--tools tools.json --delivery cloud-delivery.json | planet subscriptiosn create -
```
