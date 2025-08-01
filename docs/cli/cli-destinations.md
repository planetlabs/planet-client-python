---
title: CLI for Destinations API Tutorial
---

## Introduction
The `planet destinations` command provides an interface for creating, listing, and modifying destinations in the [Planet Destinations API](https://docs.planet.com/develop/apis/destinations/). This tutorial takes you through the main commands available in the CLI.

## Core Workflows

### Create a Destination
To discover supported cloud destinations, run the command `planet destinations create --help`. Once you have chosen your target cloud destination type, run the command `planet destinations create <type> --help` to discover the required and supported parameters (eg: `planet destinations create s3 --help`).

Finally, submit the full request:
```sh
planet destinations create s3 --bucket my-bucket --region us-west-2 --access-key-id AKIA... --secret-access-key SECRET... --name my-s3-destination
```

The newly created destination will be printed to stdout, with the destination reference under the key `pl:ref`, which can subsequently be used in Orders API and Subscriptions API requests as the delivery destination.

### List Destinations
List all destinations within your organization with command `planet destinations list`.

You can get nicer formatting with `--pretty` or pipe it into `jq`, just like the other Planet CLIs.

#### Filtering
The `list` command supports filtering on a variety of fields. You can discover all filterable fields by running the command `planet destinations list --help`.

* `--archived`: Set to true to include only archived destinations,
                false to exclude them.
* `--is-owner`: Set to true to include only destinations owned by the
                requesting user, false to exclude them.
* `--can-write`: Set to true to include only destinations the user can
                 modify, false to exclude them.

For example, issue the following command to list destinations that are not archived and you as the user have permission to modify:
```sh
planet destinations list --archived false --can-write true
```

### Modify Destinations
The CLI conveniently moves all modify actions to first class commands on the destination. The supported actions are archive, unarchive, rename, and update credentials. To discover all update actions run `planet destinations --help`.

To discover more information about a specific update action, use the `--help` flag (eg: `planet destinations rename --help`, `planet destinations update --help`).

Credential updating might be done if credentials expire or need to be rotated. For example, this is how s3 credentials would be updated.
```sh
planet destinations update s3 my-destination-id --access-key-id NEW_ACCESS_KEY --secret-access-key NEW_SECRET_KEY
```

## Using destinations in Subscriptions API
After creating a destination, it can be used as the delivery location for subscriptions. Use the destination reference in the delivery block instead of credentials.

The subsequent examples will use the destination ref `pl:destinations/my-s3-destination-6HRjBcW74jeH9SC4VElKqX`.
```json
{
  "name": "Subscription using a destination",
  "source": {
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
  "delivery": {
    "type": "destination",
    "parameters": {
      "ref": "pl:destinations/my-s3-destination-6HRjBcW74jeH9SC4VElKqX",
    }
  }
}
```

Then create the subscription, with the json above saved to a file.
```sh
planet subscriptions create my-subscription.json
```

The results of the created subscription will be delivered to the destination provided.

To retrieve all subscriptions created with a specific destination, issue the following command:
```sh
planet subscriptions list --destination-ref pl:destinations/my-s3-destination-6HRjBcW74jeH9SC4VElKqX
```

## Using destinations in Orders API
After creating a destination, it can be used as the delivery location for orders. Use the destination reference in the delivery block instead of credentials.

The subsequent examples will use the destination ref `pl:destinations/my-s3-destination-6HRjBcW74jeH9SC4VElKqX`.
```json
{
  "name": "Order using a destination",
  "products": [
    {
      "item_ids": [
        "20220605_124027_64_242b"
      ],
      "item_type": "PSScene",
      "product_bundle": "analytic_sr_udm2"
    }
  ],
  "delivery": {
    "destination": {
      "ref": "pl:destinations/cp-gcs-6HRjBcW74jeH9SC4VElKqX"
    }
  }
}
```

Then create the order, with the json above saved to a file.
```sh
planet orders create my-order.json
```

The results of the created order will be delivered to the destination provided.

To retrieve all orders created with a specific destination, issue the following command:
```sh
planet orders list --destination-ref pl:destinations/my-s3-destination-6HRjBcW74jeH9SC4VElKqX
```
