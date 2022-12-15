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
        "ortho_analytic_4b"
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
      "start_time": "2022-11-01T00:00:00Z"
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