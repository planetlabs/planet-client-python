---
title: Python SDK for Subscriptions API Tutorial
---

TODO: Update narrative and snippets to be SDK instead of CLI.

## Introduction

The `SubscriptionsClient` enables interaction with the 
[Subscriptions API](https://developers.planet.com/apis/subscriptions/)
that make it possible to set up a recurring search criteria. Using the subscriptions api 
you can automatically process and deliver new imagery to a cloud bucket. It also 
has a powerful 'backfill' capability to bulk order historical imagery to your area of interest. 
This tutorial takes you through the main commands available for subscriptions in the SDK

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

To create a new subscription with the CLI, use the `create_subscription` method and the json file you just created:

TODO: Python snippet here:
```sh
planet subscriptions create my-subscription.json
```

!!!note "Note"
    The above command assumes that you’ve saved the subscriptions JSON as `my-subscription.json` and that you’ve replaced the delivery information with your own bucket and credentials.

### List Subscriptions

Now that you’ve got a subscription working you can make use of the other commands.

TODO: Python snippet here, should probably have it print too:
```sh
planet subscriptions list
```

outputs the JSON for your first 100 subscriptions. If you'd like more you can set the `--limit` 
parameter higher, or you can set it to 0 and there will be no limit. 

TODO: Update narrative here, maybe example? How do we get python to print json nicely? Or does it do it by default?

You can get nicer formatting with `--pretty` or pipe it into `jq`, just like the other Planet
CLI’s.

The `list_subscriptions` method also supports filtering by the status of the subscription:


TODO: Python snippet here:
```sh
planet subscriptions list --status running
```

gives you just the currently active subscriptions. The other available statuses are:
`cancelled`, `preparing`, `pending`, `completed`, `suspended`, and `failed`.

### Get Subscription

To get the full details on a single subscription you can take the id from your list and use the
`get_subscription` method:

TODO: Python snippet here:
```sh
planet subscriptions get cb817760-1f07-4ee7-bba6-bcac5346343f
```

### Subscription Results

To see what items have been delivered to your cloud bucket you can use the `get_results` method:

TODO: Python snippet here:
```sh
planet subscriptions results cb817760-1f07-4ee7-bba6-bcac5346343f
```

By default this displays the first 100 results. As with other commands, you can use the `--limit` param to 
set a higher limit, or set it to 0 to see all results (this can be quite large with subscriptions results).

You can also filter by status:

TODO: Python snippet here:
```sh
planet subscriptions results --status processing
```

The available statuses are `created`, `queued`, `processing`, `failed`, and `success`. 

### Update Subscription

You can update a subscription that is running, for example to change the 'tools' it’s using or to alter
its geometry. To do this you must submit the full subscription creation JSON, so the easiest way is to
get it with `get_subscription` and then alter the values.

TODO: Python snippet here - is there a way to programmatically update the resulting json? Could be nice to show that
like change the asset type from 8 band to 4 band

```sh
planet subscriptions update cb817760-1f07-4ee7-bba6-bcac5346343f \
    my-updated-subscriptions.json
```

### Cancel a subscription

Cancelling a subscription is simple with the SDK:

TODO: Python snippet here:
```sh
planet subscriptions cancel cb817760-1f07-4ee7-bba6-bcac5346343f
```

That will stop the subscription from producing any more results, but it will stay in the system so you can
continue to list and get it.

## Subscription Request Conveniences

There are a couple of commands that can assist in creating the subscription JSON, used for creation and updates.
A subscription request is a pretty complicated command, consisting of a search, a cloud delivery, as well as 
tools to process the data plus notifications on the status. 

### Catalog Source

The first place to start is the `catalog-source` command, which generates all the JSON for the 
[catalog source](https://developers.planet.com/docs/subscriptions/source/#catalog-source-type) block. The core
of this is quite similar to a Data API search request, though with more required fields. The minimal
required commands would be a request like:

TODO: Python snippet here:
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

TODO: Python snippet here:
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

TODO: Python snippet here:
```sh
planet data filter --range clear_percent gt 90 > filter.json
planet subscriptions request-catalog \
    --item-types PSScene \
    --asset-types ortho_analytic_8b \
    --geometry geometry.geojson \
    --start-time 2022-08-24T00:00:00-07:00 \
    --filter filter.json
```

Do not bother with geometry or date filters, as they will be ignored in favor of the `--start-time` and `--geometry` values that are required.

#### Saving the output

You may want to save the output of your `catalog-source` to disk, so that you can use it in the future to construct the complete subscription
request. 

TODO: Python snippet here:
```sh
planet data filter --range clear_percent gt 90 > filter.json
planet subscriptions request-catalog \
    --item-types PSScene \
    --asset-types ortho_analytic_8b \
    --geometry geometry.geojson \
    --start-time 2022-08-24T00:00:00-07:00 \
    --filter filter.json > request-catalog.json
```

### Subscription Tools

Now we’ll dive into some of the tools options for subscriptions. These are quite similar to the tools for 
orders, but unfortunately the syntax is subtly different, and there are less tools supported. Just like 
for Orders, future of the versions of the CLI will likely add `tools` convenience methods, you can follow issue
[#601](https://github.com/planetlabs/planet-client-python/issues/601). 

#### Clipping

The most used tool is the `clip` operation, which lets you pass a geometry to the
Subscriptions API and it creates new images that only have pixels within the geometry you
gave it. We’ll use the same geometry from [above](#geometry), as it is quite
typical to use the same subscription geometry as the clip geometry, so you don't get
any pixels outside of your area of interest (99.9% of all subscriptions use the clip
tool, so it’s strongly recommended to also use clip). 

TODO: Make the JSON just the geometry, and show python snippet for the clip tool

The proper 'clip' tool for it
would be:

```json
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

#### File Format Tool

TODO: Narrative on file format
TODO: Python snippet here:

#### Harmonize Tool

TODO: Narrative on file format
TODO: Python snippet here:

#### Reproject Tool

TODO: Narrative on file format
TODO: Python snippet here:

#### TOAR Tool

TODO: Narrative on file format
TODO: Python snippet here:

#### Band Math Tool

TODO: Narrative on file format
TODO: Python snippet here:

### Delivery

One other essential part of the request is the `delivery` - the cloud delivery. 
You can find the full documentation for the delivery options in
the [Subscriptions Delivery documentation](https://developers.planet.com/docs/subscriptions/delivery/).

#### S3 Delivery

TODO: Narrative on file format
TODO: Python snippet here:

#### Azure Delivery

TODO: Narrative on file format
TODO: Python snippet here:

#### Google Cloud Delivery

TODO: Narrative on file format
TODO: Python snippet here:

#### Oracle Cloud Delivery

TODO: Narrative on file format
TODO: Python snippet here:

### Subscriptions Request

TODO: Narrative on making a request that you've built up with convenience methods
TODO: Python snippet here: