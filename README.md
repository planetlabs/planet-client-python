# Planet API Client

[![Build Status](https://travis-ci.org/planetlabs/planet-client-python.svg?branch=master)](https://travis-ci.org/planetlabs/planet-client-python)

Python client library and CLI for Planet's public APIs.

The client provides access to the following Planet APIs:
* [analytics](https://developers.planet.com/docs/analytics/)
* [basemaps](https://developers.planet.com/docs/basemaps/) (referred to in the client as `mosaics`) 
* [data](https://developers.planet.com/docs/data/)
* [orders](https://developers.planet.com/docs/orders/)

## Installation

### Prerequisites

* Python version 3.6+

### Install package

```console
$ pip install planet
```

The [--user](https://pip.pypa.io/en/stable/user_guide/#user-installs)
flag is highly recommended for those new to [pip](https://pip.pypa.io).

A PEX executable (Windows not supported) and source releases are
[here](https://github.com/planetlabs/planet-client-python/releases/latest).

## Documentation

Online documentation:
https://planetlabs.github.io/planet-client-python/index.html

Documentation is also provided for download
[here](https://github.com/planetlabs/planet-client-python/releases/latest).


## Development

To contribute or develop with this library, see
[CONTRIBUTING](https://github.com/planetlabs/planet-client-python/CONTRIBUTING.md)


## API Key

The API requires an account for use. [Signup here](https://www.planet.com/explorer/?signup).

This can be provided via the environment variable `PL_API_KEY` or the flag `-k` or `--api-key`.

Using `planet init` your account credentials (login/password) can be used to obtain the api key.


# Example CLI Usage

**Hint:** autocompletion can be enabled in some shells using:
```console
    $ eval "$(_PLANET_COMPLETE=source planet)"
```

Basics and help:

```console
    $ planet --help
```

Specific API client usage:
```console
    $ planet data
```    

Specific command help:
```console
    $ planet data download --help
```
