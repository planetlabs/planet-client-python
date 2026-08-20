---
title: CLI for Quota API Tutorial
---

## Introduction
The `planet quota` command provides an interface for inspecting quota-enabled products, reserving quota against areas of interest, and tracking bulk reservation jobs in the [Planet Quota Reservations API](https://docs.planet.com/develop/apis/quota/). This tutorial takes you through the main commands available in the CLI.

Quota reservations are made against *AOI feature references* — the `pl:features/...` refs produced by the [Features API](https://docs.planet.com/develop/apis/features/). See the [`planet features`](cli-reference.md) commands for creating and listing them.

## Core Workflows

### Find a Product
Every reservation is made against a product, identified by a numeric `product_id`. To see the products available to your organization:

```sh
planet quota products list
```

To narrow the list to products that actually support quota reservations:

```sh
planet quota products list --supports-reservation
```

The response can be long, so `--compact` trims each product down to the fields most useful for choosing one — `id`, `name`, `title`, `supports_reservation`, `quota_total`, `quota_used`, and `unlimited_quota`:

```sh
planet quota products list --supports-reservation --compact --pretty
```

The `id` from this listing is the value you pass as `--product-id` below.

### Estimate a Reservation
Before spending quota, you can ask what a reservation would cost:

```sh
planet quota reservations estimate \
  --aoi-ref pl:features/my/my-collection/feature-id \
  --product-id 123
```

This does not create anything — it only reports the estimated cost.

### Create a Reservation
Once you are happy with the estimate, create the reservation:

```sh
planet quota reservations create \
  --aoi-ref pl:features/my/my-collection/feature-id \
  --product-id 123
```

`--aoi-ref` may be repeated to reserve quota for several AOIs at once:

```sh
planet quota reservations create \
  --aoi-ref pl:features/my/my-collection/feature-one \
  --aoi-ref pl:features/my/my-collection/feature-two \
  --product-id 123
```

For larger lists, `--aoi-refs` accepts a JSON array as a string, a filename, or `-` for stdin — the same convention used elsewhere in the Planet CLI:

```sh
planet quota reservations create --aoi-refs refs.json --product-id 123
```

Where `refs.json` contains:
```json
[
  "pl:features/my/my-collection/feature-one",
  "pl:features/my/my-collection/feature-two"
]
```

The two options can be combined; the refs are concatenated. Use `--collection-id` to group the resulting reservations under a collection.

### List Reservations
List the quota reservations in your organization:

```sh
planet quota reservations list
```

You can get nicer formatting with `--pretty` or pipe it into `jq`, just like the other Planet CLIs.

#### Limiting, sorting, and filtering
* `--limit`: Maximum number of reservations to return. Defaults to 100; set to `0` for no maximum.
* `--sort`: Sort spec — `<field>` for ascending, `-<field>` for descending (eg: `-created_at`).
* `--fields`: Comma-separated list of fields to include in each result.
* `--filter`: A `KEY=VALUE` filter, where the key is a `{field}` or `{field}__{op}` pair. May be repeated.

For example, to fetch the 10 most recently created active reservations:

```sh
planet quota reservations list --limit 10 --sort -created_at --filter state=active
```

Because `--filter` may be repeated, several conditions can be combined:

```sh
planet quota reservations list --filter state=active --filter product_id=123
```

### Get a Single Reservation
Retrieve one reservation by its numeric ID:

```sh
planet quota reservations get 100
```

## Bulk Reservations
Reserving quota for a large number of AOIs is handled asynchronously. Submit the job with `bulk-reserve`, which takes the same AOI and product options as `create`:

```sh
planet quota reservations bulk-reserve --aoi-refs refs.json --product-id 123
```

Rather than the reservations themselves, this returns a payload containing a `job_id` and a `status`.

### Track a Bulk Job
Use the `job_id` returned above to poll for progress:

```sh
planet quota jobs get 7b7e3a3a-1234-5678-9abc-def012345678
```

To see all bulk reservation jobs, use `jobs list`, which supports the same `--limit`, `--sort`, `--fields`, and `--filter` options as `reservations list`:

```sh
planet quota jobs list --limit 10 --sort -id
```
