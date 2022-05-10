# Planet CLI Interface

## Introduction

This document serves as the root document to outline the Command-Line Interface
(CLI). It includes the interface for the 'base' and 'auth' commands as well as
helper commands. and then links to other documents for orders, data and 
subscriptions. 

### CLI Sections

* [CLI Base](#cli-base)
* [Authentication](#authentication)
* [Helper](#Helper)
* [Orders](CLI-Orders.md)
* [Data](CLI-Data.md)
* [Subscriptions](CLI-Subscriptions.md)

## CLI Base

### General Interface

```
Usage: `planet [OPTIONS] COMMAND [ARGS]...`

 Planet Command Line Interface

Options:
  --verbosity [warning|info|debug|none]
                                  Logging verbosity level.
  --quiet                         Disable all reporting.
  --version                       Show the version and exit.
  --help                          Show this message and exit.

Commands:
  auth    Commands for working with Planet authentication
  data    Commands for interacting with the Data API
  orders  Commands for interacting with the Orders API
```

### Options

#### Verbosity

User Story: As a CLI user I would like to adjust the verbosity between warning, info, debug, and disabled.

Report warning logging (default)

`$ planet <command>`

Report info+ logging

`$ planet --verbosity info <command>`

Report debug+ logging

`$ planet --verbosity debug <command>`

Disable logging

$ `planet --verbosity none <command>`

#### Quiet

User Story: As a CLI user I would like to disable all reporting because I am using the CLI within a script.

$ `planet --quiet <command>`

## Authentication

### Group Interface

```
Usage: planet auth [OPTIONS] COMMAND [ARGS]...

  Commands for working with Planet authentication

Options:
  --help           Show this message and exit.

Commands:
  list       List authorization accounts
  login      Obtain and store authorization credentials
  login-key  Obtain and store api key authorization credentials
  print-key  Print the stored api key
```

### login-key [?]

NOTE: --account support is post-initial release


Logistics: The user is prompted for email and password (hidden) in the shell. 
The api key is downloaded and stored in a local secret file.

#### Interface

```
Usage: planet auth login-key [OPTIONS]

  Obtain and store api key authorization credentials

  If --account is specified, the active account is switched to the specified
  account. If valid credentials already exist for the account, the account is
  set to active without rerunning authorization.

Options:
  --account TEXT  Identifier for authorization account.
  --help          Show this message and exit.
```

#### Usage Examples

User Story: As a CLI user I would like to obtain and store my api key for authorization.

`$ planet auth login-key`

email:

Password:

Authorized

### print-key

#### Interface

```
Usage: planet auth print-key [OPTIONS]

  Print the stored api key.

  Returns nothing if no api key is stored.

Options:

  --help  Show this message and exit.
```

### store-key

#### Interface

```
Usage: planet auth store-key [OPTIONS]

  Store authorization API key.

  The API key can be obtained from the Planet account page at https://www.planet.com/account.

Options:
  --help  Show this message and exit.
```

## Helper

These commands are utility functions that assist in other functions in the CLI.

### Collect

#### Interface

```
planet collect SEQUENCE

Collect a sequence of JSON into a JSON blob. If the sequence is GeojSON, create a FeatureCollection.

Arguments:
SEQUENCE - sequence of JSON blobs.

Options:
--pretty - flag. Pretty-print output
```

#### Usage Examples

User Story: As a CLI user I want to create a FeatureCollection of PSScene 
scenes that intersect an AOI and were acquired in July 2021 .

```
$ planet data filter \
--geom aoi.geojson \
--date-range acquired gte 2021-07-01 \
--date-range acquired lt 2021-08-01 | \
planet data search-quick PSScene - | planet collect
{"type": "FeatureCollection", "features" [...]}
```