---
title: CLI for Subscriptions API Tutorial
---

## Introduction

The `planet subscriptions` command enables interaction with the 
[Subscriptions API](https://developers.planet.com/apis/subscriptions/),
which enables you to set up a recurring search criteria to automatically process
and deliver new imagery to a cloud bucket. It also has a powerful 'backfill' capability
to bulk order historical imagery to your area of interest. This tutorial takes you
through the main commands available in the CLI. Note that there is not yet any
'helper' methods like `planet orders request` or `planet data filter`, so for now 
you'll have to write your own JSON requests. But we hope to add helper methods
soon, sound in on [this issue](https://github.com/planetlabs/planet-client-python/issues/614)
if you have ideas or just want to encourage its prioritization.

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

will give you just the currently active subscriptions. The other available status's are:
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






