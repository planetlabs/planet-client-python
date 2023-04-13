# Planet SDK for Python

[![Build Status](https://github.com/planetlabs/planet-client-python/actions/workflows/test.yml/badge.svg)](https://github.com/planetlabs/planet-client-python/actions/workflows/test.yml)

The [Planet](https://planet.com) Software Development Kit (SDK) for Python
provides both a Python API and a command-line interface (CLI)
to make use of [the Planet APIs](https://developers.planet.com/docs/apis/).
Everything you need to get started is found in our 
[online documentation](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/).

Version 2.0 includes support for the core workflows of the following APIs:

* [Data](https://developers.planet.com/docs/data/) - Search for imagery from Planet's data catalog.
* [Orders](https://developers.planet.com/docs/orders/) - Process and download or deliver imagery.
* [Subscriptions](https://developers.planet.com/docs/subscriptions/) - Set up a search to auto-process and deliver imagery.

After the initial 2.0 release there will be additional work to support the 
remaining Planet APIs: [basemaps](https://developers.planet.com/docs/basemaps/),
[tasking](https://developers.planet.com/docs/tasking/)) and 
[analytics](https://developers.planet.com/docs/analytics/).

## Versions and Stability

The default branch (main) of this repo is for the [Planet SDK for 
Python](https://github.com/planetlabs/planet-client-python/projects/2),
a complete rewrite and upgrade from the original [Planet Python 
Client](https://developers.planet.com/docs/pythonclient/). If you 
are looking for the source code to that library see the 
[v1](https://github.com/planetlabs/planet-client-python/tree/v1) branch.

The Planet SDK for Python is in 'pre-release' stages, working towards a solid
beta release in December. Upcoming milestones are tracked in the [Planet SDK 
for Python Milestones](https://github.com/planetlabs/planet-client-python/milestones).  

## Installation and Quick Start

The main installation path and first steps are found in the 
[Quick Start Guide](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/get-started/quick-start-guide/)
of the documentation.

### Installing from source

This option enables you to get all the latest changes, but things might also be a bit less stable.
To install you must [clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
the [planet-client-python](https://github.com/planetlabs/planet-client-python) repository 
to your local computer. After you have the repo local just navigate to the root
directory, where this readme lives.

Then you can install locally with pip:

```console
$ pip install . 
```

## Documentation

Documentation is currently [hosted online](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/)
It should be considered 'in progress', with many updates to come. It can also
be built and hosted locally (see [CONTRIBUTING.md](CONTRIBUTING.md)) or can be 
read from source in the [docs](/docs) directory.

## Authentication

Planet's APIs require an account for use. To get started you need to 
[Get a Planet Account](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/get-started/get-your-planet-account/).

## Development

To contribute or develop with this library, see
[CONTRIBUTING.md](CONTRIBUTING.md).
