# Destinations Command-Line Interface Specification

This document lays out the command-line interface to interact with the Planet
[Destinations API](https://docs.planet.com/develop/apis/destinations/).

## Overview

The `planet destinations` command group allows you to list, create, update, archive, unarchive, and rename cloud storage destinations, including Amazon S3, S3-compatible, Google Cloud Storage, Azure Blob Storage, and Oracle Cloud Storage.

---

## Global Options

- `-u, --base-url TEXT`  
  Assign custom base Destinations API URL.

---

## Commands

### List Destinations

```sh
planet destinations list [OPTIONS]
```

**Options:**
- `--archived [true|false]`  
  Include only archived destinations (`true`) or exclude them (`false`).
- `--is-owner [true|false]`  
  Include only destinations owned by the requesting user (`true`) or exclude them (`false`).
- `--can-write [true|false]`  
  Include only destinations the user can modify (`true`) or exclude them (`false`).

**Example:**
```sh
planet destinations list --archived false --is-owner true --can-write true
```

---

### Get Destination

```sh
planet destinations get DESTINATION_ID [OPTIONS]
```

Retrieve detailed information about a specific destination.

**Example:**
```sh
planet destinations get my-destination-id
```

---

### Create Destinations

#### Amazon S3

```sh
planet destinations create s3 --bucket BUCKET --region REGION --access-key-id KEY --secret-access-key SECRET [--explicit-sse] [--name NAME]
```

**Options:**
- `--bucket` (required): S3 bucket name.
- `--region` (required): AWS region.
- `--access-key-id` (required): AWS access key ID.
- `--secret-access-key` (required): AWS secret access key.
- `--explicit-sse`: Explicitly set headers for server-side encryption (SSE).
- `--name`: Optional name for the destination.

#### S3-Compatible

```sh
planet destinations create s3-compatible --bucket BUCKET --endpoint ENDPOINT --region REGION --access-key-id KEY --secret-access-key SECRET [--use-path-style] [--name NAME]
```

**Options:**
- `--bucket` (required): Bucket name.
- `--endpoint` (required): Endpoint URL.
- `--region` (required): Region.
- `--access-key-id` (required): Access key ID.
- `--secret-access-key` (required): Secret access key.
- `--use-path-style`: Use path-style addressing.
- `--name`: Optional name for the destination.

#### Google Cloud Storage (GCS)

```sh
planet destinations create gcs --bucket BUCKET --credentials BASE64_JSON [--name NAME]
```

**Options:**
- `--bucket` (required): GCS bucket name.
- `--credentials` (required): Base64-encoded service account credentials (JSON).
- `--name`: Optional name for the destination.

#### Azure Blob Storage

```sh
planet destinations create azure --container CONTAINER --account ACCOUNT --sas-token SAS_TOKEN [--storage-endpoint-suffix SUFFIX] [--name NAME]
```

**Options:**
- `--container` (required): Blob storage container name.
- `--account` (required): Azure account.
- `--sas-token` (required): Shared-Access Signature token.
- `--storage-endpoint-suffix`: Custom Azure Storage endpoint suffix.
- `--name`: Optional name for the destination.

#### Oracle Cloud Storage (OCS)

```sh
planet destinations create ocs --bucket BUCKET --access-key-id KEY --secret-access-key SECRET --namespace NAMESPACE --region REGION [--name NAME]
```

**Options:**
- `--bucket` (required): Oracle bucket name.
- `--access-key-id` (required): Oracle account access key.
- `--secret-access-key` (required): Oracle account secret key.
- `--namespace` (required): Oracle Object Storage namespace.
- `--region` (required): Oracle region.
- `--name`: Optional name for the destination.

---

### Update Destinations

#### Amazon S3

```sh
planet destinations update s3 DESTINATION_ID --access-key-id KEY --secret-access-key SECRET [--explicit-sse]
```

#### S3-Compatible

```sh
planet destinations update s3-compatible DESTINATION_ID --access-key-id KEY --secret-access-key SECRET [--use-path-style]
```

#### Google Cloud Storage (GCS)

```sh
planet destinations update gcs DESTINATION_ID --credentials BASE64_JSON
```

#### Azure Blob Storage

```sh
planet destinations update azure DESTINATION_ID --sas-token SAS_TOKEN
```

#### Oracle Cloud Storage (OCS)

```sh
planet destinations update ocs DESTINATION_ID --access-key-id KEY --secret-access-key SECRET
```

---

### Archive/Unarchive Destinations

#### Archive

```sh
planet destinations archive DESTINATION_ID
```

#### Unarchive

```sh
planet destinations unarchive DESTINATION_ID
```

---

### Rename Destination

```sh
planet destinations rename DESTINATION_ID NEW_NAME
```

---

## Notes

- For GCS, the `--credentials` argument must be the base64-encoded JSON of your Google Cloud service account key.  
  To encode a JSON file to base64:
  ```sh
  cat my_creds.json | base64 | tr -d '\n'
  ```

- All commands support the `--base-url` option for custom API endpoints.

---
