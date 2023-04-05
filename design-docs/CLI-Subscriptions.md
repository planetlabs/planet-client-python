# Subscriptions Command-Line Interface Specification

This documents lays out the command-line interface to interact with the 
Planet [Subscriptions API](https://developers.planet.com/docs/subscriptions/reference/)

A subscription connects catalog sources to a data processing pipeline. It can 
run those tools on new data when it is available. It can process existing data 
(backfilling). A subscription also specifies storage location for results and 
emits event notifications.

Unlike Orders, the Subscription CLI deals only with Subscriptions and their 
Results. Those are the only nouns. There is no downloader or waiter. It should 
be easier to design and implement.

**Major unknowns:**

* The org admin or superuser feature. Do we need it immediately? How is it going 
  to work with our new auth system?
* Request templates and parameterization. Which standards? How complete? The API
  requires full requests, so everything more surgical is up to the CLI.

**Essential reading:** 

https://developers.planet.com/docs/subscriptions/reference/
https://developers.planet.com/docs/subscriptions/

**Commands:**

The following 3 are backed by HTTP GET requests and are idempotent (run them as 
many times as you want and nothing changes on the server side). They return 
information about different resources in the subscriptions API.

```
planet subscriptions list
planet subscriptions describe
planet subscriptions results
```

The following 3 are backed by HTTP POST or PUT requests. They modify the state of individual subscriptions.

```
planet subscriptions create
planet subscriptions update
planet subscriptions cancel
```

`planet subscriptions list` has no arguments. `planet subscriptions create` 
takes text or a filename as its single argument and can also take text from 
stdin. The other commands all take a single string ID as a positional-only 
argument.

*Note:* `planet subscriptions cancel` doesn’t delete a subscription. It only 
stops it, permanently. The API and CLI have gaps. The gaps, if you squint, 
look a little like planet-subscriptions-delete and planet-subscriptions-resume. 
Addressing the gaps is not part of this work.

## List

### Interface

```
planet subscriptions list [OPTIONS]

Print JSON formatted descriptions of subscriptions.

Options:

–status (multi) running/completed etc. Default is all status.
–limit: optional limit to the number of results.
–pretty: option to pretty-print the output.

Output:
Sequence of JSON texts. Each describing a subscription and its current state. 
Like the result of “describe”.
```

See `planet-subscriptions-results` for implementation details of paging.

### Errors

In the case of invalid options, print an error message (stderr) and set the exit
code to 2. In the case of an API error response, print the response JSON and set
code to 1.

## Describe

### Interface

```
planet subscriptions describe [OPTIONS] ID

Print a JSON description of the subscription with ID.

Arguments:

ID: string. This is the identifier of a Subscription. It’s required. We won’t take identifiers from a file.

Options:
None.

Output:
One JSON text. Printing the JSON from the API response, verbatim, to stdout is 
one option. It seems to make sense to start with that.
```

### Errors

In the case of invalid options, print an error message (stderr) and set the exit
code to 2. In the case of an API error response, print the response JSON and 
set code to 1.

## Results

### Interface

```
planet subscriptions results [OPTIONS] ID

Arguments:

ID: string. This is the identifier of a Subscription. It’s required. We won’t take identifiers from a file.

Options:

–status: (multi) running/completed etc. Default is all status.
–created: timestamp instant or range.
–updated: timestamp instant or range.
–completed: timestamp instant or range.
–limit: optional limit to the number of results.

Output:
JSON text sequence. Default is to print all results from the API. As a starting point let’s print the API’s results verbatim.
```

### Implementation details 
Rhe API results are paged (default page size is 20, maximum is 10,000). The 
implementation is required to follow “next” links when there are more than fit 
in a page. Nice thing about using async Python internally is that the command 
can print one page of results to the terminal while the API is handling the 
request for the next page.

*Note: the org admin feature explained under `planet-subscriptions-list` applies
here. I think we can defer that for now, but will get a check from the API 
team.*

### Errors

In the case of invalid options, print an error message (stderr) and set the exit
code to 2. In the case of an API error response, print the response JSON and 
set code to 1.

## Create

### Interface

```
planet subscriptions create [OPTIONS] REQUEST

Create and launch a subscription.

Arguments

REQUEST: a string. This could be JSON text to be sent directly to the API. Alternatively, it may be a local file or “-” which means read the request from STDIN. Suggestion for the future, make “-” the default value.

Options:
None.

Output:
JSON description of the created Subscription, the API response verbatim, including its ID. 
```

### Errors

In the case of invalid options, print an error message (stderr) and set the exit
code to 2. In the case of an API error response, print the response JSON and 
set code to 1.

## Request

### Interface

```
planet subscriptions request [OPTIONS]

Generate a subscriptions request.

This command provides support for building the subscription request JSON used to create or
update a subscription. It outputs the subscription request.

Options:
  --name TEXT                     Subscription name. Does not need to be unique.
                                  [required]
  --source                        Source JSON. Can be a json string,
                                  filename, or '-' for stdin.
  --tools JSON                    Toolchain JSON. Can be a json string,
                                  filename, or '-' for stdin.
  --delivery JSON                 Credentials for cloud storage provider to
                                  enable cloud delivery of data. Can be a json
                                  string, filename, or '-' for stdin.
  --notifications JSON            Notification JSON to specify webhook topics.
                                  Can be a json string, filename, or '-' for
                                  stdin.
  --pretty                        Format JSON output.
  --help                          Show this message and exit.
```

### Usage Examples

```
planet subscription request \
    --name test \
    --source source.json \
    --delivery delivery.json | planet subscriptions create -
```

## Request-catalog

### Interface

```
planet subscriptions request-catalog [OPTIONS]

Generate a subscriptions request source JSON for a catalog.

Options:
  --asset-types TEXT              One or more comma-separated asset types. Required.
  --item-types TEXT               One or more comma-separated item-types. Required.
  --geometry JSON                 geometry of the area of interest of the subscription that will be used to determine matches.
                                  Can be a json string, filename, or '-' for stdin.
  --start-time DATETIME           Start date and time to begin subscription.
  --end-time DATETIME             Date and time to end the subscription.
  --rrule TEXT                    iCalendar recurrance rule to specify recurrances.
  --filter JSON                   A search filter can be specified a json string,
                                  filename, or '-' for stdin.
  --pretty                        Format JSON output.
  --help                          Show this message and exit.
```

### Usage Examples

```
planet subscriptions request-catalog \
        --item-types PSScene \
        --asset-types ortho_analytic_8b_sr,ortho_udm2 \
        --geometry aoi.geojson \
        --start-time 2022-01-01 > req_cat.json
```

## Request-other

### Interface

```
planet subscriptions request-other [OPTIONS]

Generate a subscriptions request source JSON for another product.

Options:
  --type                        Type.
  --id                          Id.
  --geometry JSON                      geometry of the area of interest of the subscription that will be used to determine matches.
                                  Can be a json string, filename, or '-' for stdin.
  --start-time DATETIME           Start date and time to begin subscription.
  --end-time DATETIME             Date and time to end the subscription.
  --rrule TEXT                    iCalendar recurrance rule to specify recurrances.
  --pretty                        Format JSON output.
  --help                          Show this message and exit.
```


## Update

Edit a subscription, such as one with a future start date, before it starts running.

https://developers.planet.com/docs/subscriptions/#edit-a-subscription mentions 
caveats and limitations:
 * Backfill cannot be updated.
 * After a subscription is running, only source items can be modified, and not 
   all of them.


### Interface

```

planet subscriptions update [OPTIONS] ID REQUEST

Update the subscription identified by ID.

Arguments:
ID: string. This is the identifier of a Subscription. It’s required. We won’t take identifiers from a file.

Options:
None.

Output:
JSON API response, verbatim.
```

### Errors

In the case of invalid options, print an error message (stderr) and set the exit
code to 2. In the case of an API error response, print the response JSON and 
set code to 1.

## Cancel

### Interface

```

planet subscriptions cancel [OPTIONS] ID

Permanently cancel the subscription identified by ID.

Arguments:
ID: string. This is the identifier of a Subscription. It’s required. We won’t take identifiers from a file.

Options:
None.

Output:

API response, verbatim.
```

### Errors

In the case of invalid options, print an error message (stderr) and set the exit
code to 2. In the case of an API error response, print the response JSON and set
code to 1.
