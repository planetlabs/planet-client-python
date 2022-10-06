# Orders Command-Line Interface Specification

This document lays out the command-line interface to interact with the Planet
[Orders API](https://developers.planet.com/docs/orders/).

## list

### Interface

Usage: planet orders list [OPTIONS]

  List orders

  This command outputs a sequence of the returned order descriptions. If --pretty is specified, each order description is pretty-printed.

Options:
  --state CHOICE   Filter orders to given state.
  --limit INTEGER  Maximum number of results to return. Default is 100. A
                   value of 0 means no maximum.
  --pretty         Format JSON output.
  --help           Show this message and exit.


### Usage Examples

User Story: As a CLI user I would like to get a json blob that describes up to the last 100 of my orders so that I can use jq to get their dates.

```
$ planet orders list
```
```
{"_links": …}
{"_links": …}
{"_links": …}
…
```

User Story: As a CLI user I would like to get a json blob that describes all of my orders so that I can use jq to get their dates.
```
$ planet orders list --limit 0
```
```
{"_links": …}
{"_links": …}
{"_links": …}
…
```

User Story: As a CLI user I would like to get a json blob that describes my last 5 successful orders so that I can use jq to get their order dates.
```
$ planet orders list --state success --limit 1
```
response (pretty-printed)
```
{
  "_links": {
    "_self": "https://api.planet.com/compute/ops/orders/v2/193e5bd1-dedc-4c65-a539-6bc70e55d928"
  },
  "created_on": "2022-05-04T01:01:57.864Z",
  "error_hints": [],
  "id": "193e5bd1-dedc-4c65-a539-6bc70e55d928",
  "last_message": "Manifest delivery completed",
  "last_modified": "2022-05-04T01:09:36.037Z",
  "name": "test",
  "products": [
    {
      "item_ids": [
        "20210821_161925_80_2453"
      ],
      "item_type": "PSScene",
      "product_bundle": "visual"
    }
  ],
  "state": "success"
}
```

## get

### Interface
Usage: planet orders get [OPTIONS] ORDER_ID

  Get order

  This command outputs the order description, optionally pretty-printed.

Options:  
  --pretty  Format JSON output.



### Usage Examples

User Story: As a CLI user I would like to get a json blob that describes a
certain order so I can determine its status.

```
$ planet orders get 193e5bd1-dedc-4c65-a539-6bc70e55d928
{"_links": …}
```
response (pretty-printed)

**Note the `results` key in the `_links` section is present here but was not
a part of the response from `planet orders list`**
```
{
  "_links": {
    "_self": "https://api.planet.com/compute/ops/orders/v2/193e5bd1-dedc-4c65-a539-6bc70e55d928",
    "results": [
      {
        "delivery": "success",
        "expires_at": "2022-06-30T02:57:15.492Z",
        "location": "https://api.planet.com/compute/ops/download/?token={TOKEN}",
        "name": "193e5bd1-dedc-4c65-a539-6bc70e55d928/manifest.json"
      },
      {
        "delivery": "success",
        "expires_at": "2022-06-30T02:57:15.495Z",
        "location": "https://api.planet.com/compute/ops/download/?token={TOKEN}",
        "name": "193e5bd1-dedc-4c65-a539-6bc70e55d928/PSScene/20210821_161925_80_2453_metadata.json"
      },
      {
        "delivery": "success",
        "expires_at": "2022-06-30T02:57:15.498Z",
        "location": "https://api.planet.com/compute/ops/download/?token={TOKEN}",
        "name": "193e5bd1-dedc-4c65-a539-6bc70e55d928/PSScene/20210821_161925_80_2453_3B_Visual.tif"
      }
    ]
  },
  "created_on": "2022-05-04T01:01:57.864Z",
  "error_hints": [],
  "id": "193e5bd1-dedc-4c65-a539-6bc70e55d928",
  "last_message": "Manifest delivery completed",
  "last_modified": "2022-05-04T01:09:36.037Z",
  "name": "test",
  "products": [
    {
      "item_ids": [
        "20210821_161925_80_2453"
      ],
      "item_type": "PSScene",
      "product_bundle": "visual"
    }
  ],
  "state": "success"
}

```

## cancel

### Interface

Usage: planet orders cancel [OPTIONS] ORDER_ID

  Cancel order

  This command outputs the cancelled order details, optionally pretty-printed.

Options:  
  --pretty  Format JSON output.


### Usage Examples
User Story: As a CLI user I would like to cancel a certain order.

```
$ planet orders cancel 65df4eb0-e416-4243-a4d2-38afcf382c30
{"_links": …}
```

## wait

### Interface
Usage: planet orders wait [OPTIONS] ORDER_ID

  Wait for order to reach the desired state.

  Polls the service for order status and completes when the order has reached
  the desired state. By default, the desired state is any completed state.
  This can be overridden to any order state with the --state option. The
  polling period is one second, this can be overridden with the --period
  option.

  This command outputs the order details at the end of the wait, optionally
  pretty-printed.

Options:  
  --state TEXT   Stop waiting when order reaches this state  
  --period TEXT  Duration of time for one polling cycle, in seconds.  
  --pretty       Format JSON output.  


### Usage Examples

User Story: As a CLI user I would like to wait for an order to be ready for
download so I can send a message to another machine to do the download.

`$ planet orders wait 65df4eb0-e416-4243-a4d2-38afcf382c30`

User Story: As a CLI user I would like to wait for an order to be ready for
download and then I would like to download the order.

```
$ planet orders wait 65df4eb0-e416-4243-a4d2-38afcf382c30 \
&& planet orders download 65df4eb0-e416-4243-a4d2-38afcf382c30
```

User Story: As a CLI user I would like to create an order, wait for it to be
ready to download, then download the order.

```
$ id=`planet orders create request-1.json | jq -r '.id'` \
&& planet orders wait $id && planet orders download $id
<ANSI download status reporting>
```


## download


### Interface


Usage: planet orders download [OPTIONS] ORDER_ID

  Download order

  If --checksum is provided, the associated checksums given in the manifest
  are compared against the downloaded files to verify that they match.

Options:
  --checksum [MD5|SHA1]  Verify that checksums match.
  --directory DIRECTORY  Base directory for file download.
  --overwrite            Overwrite files if they already exist.
  --help                 Show this message and exit.


### Usage Examples

User Story: As a CLI user I would like to download an order to the current
directory for local processing.

Basic usage:

```
$ planet orders download 49b8d32e-2fba-4924-bd38-f7344aa48d91
<ANSI download status reporting>
```

User Story: As a CLI user I would like to download an order without ANSI reporting

```
$ planet –quiet orders download 49b8d32e-2fba-4924-bd38-f7344aa48d91
```

User Story: As a CLI user I would like to download an order to a custom
directory to support local file organization.

```
$ planet orders download \
--directory data \
49b8d32e-2fba-4924-bd38-f7344aa48d91
<ANSI download status reporting>
```

User Story: As a CLI user I would like to download an order, overwriting the
files if they exist to fix any corrupted files.

```
$ planet orders download \
--overwrite \
49b8d32e-2fba-4924-bd38-f7344aa48d91
<ANSI download status reporting>
```

User Story: As a CLI user I would like to download an order and check the md5
checksums against the manifest to ensure that no files are corrupt.

```
$ planet orders download \
--checksum md5 \
49b8d32e-2fba-4924-bd38-f7344aa48d91
<ANSI download status reporting>
<Error if check fails>
```

## create


### Interface

Usage: planet orders create [REQUEST]

  Create an order.

This command creates an order from an order request. It outputs the created order description, optionally pretty-printed.

REQUEST is the full description of the order to be created. It must be JSON
and can be specified a json string, filename, or '-' for stdin.
It defaults to reading from stdin.

Options:
  -pp, --pretty     Format JSON output.

### Usage Examples

User Story: As a CLI user I would like to create an order from a file.

```
$ planet orders create order_request.json
{"_links": …}
```

User Story: As a CLI user I would like to create an order from stdin.

```
$ cat order_request.json | planet orders create
{"_links": …}
```

User Story: As a CLI user I would like to duplicate an order.

```
$ planet orders get 65df4eb0-e416-4243-a4d2-38afcf382c30 | planet orders create
{"_links": …}
```

## request

### Interface

Usage: planet orders request NAME BUNDLE ITEM_TYPE IDS

NAME: Order name. Does not need to be unique.
BUNDLE: Product bundle.
ITEM_TYPE: Item Type.
IDS: One or more comma-separated item IDs.

Generate an order request.

This command builds an order description for use in creating an order. It
outputs the order request, optionally pretty-printed.

Support for building an order description is provided however it
has many limitations compared to what the Orders API supports. For creation
of more advanced order requests, create the order description manually or
use the Python library to aid in creating the order description.

Note that only one of --clip or --tools can be specified.

Options:

  --clip JSON        -              Clip feature GeoJSON. Can be a json string,
                                  filename, or '-' for stdin.
  --tools JSON         -           Toolchain JSON. Can be a json string,
                                  filename, or '-' for stdin.
  --email BOOLEAN         -          Send email notification when order is
                                  complete.
  --cloudconfig JSON     -         Credentials for cloud storage provider to
                                  enable cloud delivery of data. Can be a json
                                  string, filename, or '-' for stdin.
  --pretty                -        Format JSON output.


### Usage Examples

User Story: As a CLI user I would like to create a request for a basic order for
multiple scenes.

```
$ planet orders request test_order PSScene analytic_sr \
    20200922_183724_23_106a,20200922_183722_17_106a
```

User Story: As a CLI user I would like to create a request for an order with
email notification.

```
$ planet orders request test_order PSScene analytic_sr \
  20200922_183724_23_106a,20200922_183722_17_106a \
  –-email
```

NOT UPDATED BELOW

User Story: As a CLI user I would like to create a request for an order which
clips the scenes to a geojson geometry specified in a file.

```
$ planet orders request test_order PSScene analytic_sr \
    20200922_183724_23_106a,20200922_183722_17_106a \
    --clip aoi.geojson

{"name":"test_order",...}
```

User Story: As a CLI user I would like to create an order which clips the scenes
to a geojson geometry entered on the command line.

```
$ planet orders request test_order PSScene analytic_sr \
    20200922_183724_23_106a,20200922_183722_17_106a \
    --clip - < aoi.geojson

{"name":"test_order",...}
```

User Story: As a CLI user I would like to create a request for an order with a
toolchain specified in a file. NOTE: --tools and --clip cannot both be used.

```
$ planet orders request test_order PSScene analytic_sr \
    20200922_183724_23_106a,20200922_183722_17_106a \
    --tools tools.json

{"name":"test_order",...}
```

User Story: As a CLI user I would like to create a request for an order with a
cloud configuration specified in a file.

```
$ planet orders request test_order PSScene analytic_sr \
    20200922_183724_23_106a,20200922_183722_17_106a \
    --cloudconfig cloudconfig.json

{"name":"test_order",...}
```

## request-update

It is a common use case to want to create an order that is just slightly
different from another order. Maybe the order has the same toolchain but just
new ids. Maybe the order has the same ids but just a different clip AOI. It
would be nice to just update the old order request with the new information
instead of having to start from scratch.

Making this its own command frees the `request` command from having a ton of
required options, which are a bit annoying from a user's perspective.


### Interface

Usage: planet orders request-update [OPTIONS] REQUEST

REQUEST: order request to be updated. Can be string, filename, or '-' for stdin.

Update an order request.

This command creates a new order description from an existing order description,
with certain entries changed according to the options specified. It outputs the
updated order request, optionally pretty-printed.

Support for updating an order description is provided however it
has many limitations compared to what the Orders API supports. For creation
of more advanced order requests, create the order description manually or
use the Python library to aid in creating the order description.

Note that if the order description contains a tool chain with more tools
than just clip, using --clip will override the entire tool chain, not just
the clip tool.

Options:

  --clip JSON        -              Clip feature GeoJSON. Can be a json string,
                                  filename, or '-' for stdin.
  --tools JSON         -           Toolchain JSON. Can be a json string,
                                  filename, or '-' for stdin.  
  --email BOOLEAN         -          Send email notification when order is
                                  complete.
  --cloudconfig JSON     -         Credentials for cloud storage provider to
                                  enable cloud delivery of data. Can be a json
                                  string, filename, or '-' for stdin.  
  --pretty                -        Format JSON output.

### Usage Examples

To create an order using an order id and override the item IDs:

```
$ planet orders get 49b8d32e-2fba-4924-bd38-f7344aa48d91 | \
  planet orders request-update \
  --id 20200922_183724_23_106a,20200922_183722_17_106a -
```
  To create an order using an order id and clip to an AOI:
```
$ planet orders get 49b8d32e-2fba-4924-bd38-f7344aa48d91 | \
  planet orders request-update --clip aoi.geojson -
```

User Story: As a CLI user I would like to create a request for an order from a
template, overriding the name.

```
$ planet orders request-update --name IAmACopy -  < request.json
```

User Story: As a CLI user I would like to create a new order that is just like
an order that has already been submitted but has an updated name.

```
$ planet orders get 49b8d32e-2fba-4924-bd38-f7344aa48d91 | \
planet orders request-update --name IAmACopy - 
```
