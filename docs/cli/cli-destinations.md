---
title: CLI for Destinations API Tutorial
---

## Introduction
The `planet destinations` command enables interaction with the [Destinations API](https://docs.planet.com/develop/apis/destinations/), which enables the creation, listing, and modifying of destinations as well as using destinations in other services to streamline data delivery. This tutorial takes you through the main commands available in the CLI.

## Core Workflows

### Create a Destination
To discover the supported cloud destinations, run the command `planet destinations create --help`. Once you have chosen your target cloud destination type, run the command `planet destinations create <type> --help` to discover the required and supported parameters (eg: `planet destinations create s3 --help`).

Finally, submit the full request:
```sh
planet destinations create s3 my-bucket us-west-2 AKIA... SECRET... --name my-s3-destination
```

The newly created destination will be printed to standard out, with the destination reference under the key `pl:ref`, which can subsequently be used in Orders API and Subscriptions API requests as the delivery destination.

### List Destinations
Listing destinations can be accomplished with the command `planet destinations list`. This will return all destinations within your organization.

You can get nicer formatting with `--pretty` or pipe it into `jq`, just like the other Planet CLIs.

#### Filtering
The `list` command supports filtering on a variety of fields. You can discover all filterable fields by running the command `planet destinations list --help`.

* `--archived / --is-not-archived`: Filter by archive status. Use --archived to include only archived destinations, or --is-not-archived to list only active (not archived) destinations.
* `--is-owner / --is-not-owner`: Filter by ownership. Use --is-owner to include only destinations owned by the requesting user, or --is-not-owner to include destinations not owned by the user.
* `--can-write / --can-not-write`: Filter by write access. Use --can-write to include only destinations the user can modify, or --can-not-write to list destinations with read-only access for the user.

For example, to list destinations that are not archived and you can modify you would issue the following command:
```sh
planet destinations list --not-archived --can-write
```

### Update Destinations
The CLI conveniently moves all update actions to first class commands on the destination. The allowed update actions are archiving, unarchiving, renaming, and updating credentials. To discover all update actions run `planet destinations --help`.

To discover more information about a specific update action, use the `--help` flag (eg: `planet destinations rename --help`, `planet destinations update --help`).

Credential updating might be done if credentials expire or need to be rotated. For example, this is how s3 credentials would be updated.
```sh
planet destinations update parameters s3 my-destination-id NEW_ACCESS_KEY NEW_SECRET_KEY
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
