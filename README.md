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
[tasking](https://developers.planet.com/docs/tasking/) and
[analytics](https://developers.planet.com/docs/analytics/).

## Versions and Stability

The SDK follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and therefore only major releases should break compatibility. Minor versions may include new functionality and patch versions address bugs or trivial changes (like documentation).

If depending upon official packages from PyPI, a developer should feel comfortable specifying `planet == 2.*` unless depending on a specific feature introduced at a minor version, in which case `planet == 2.x.*` (where x is the minor version of the new feature) should suffice.

The default branch is always `main` and should be considered in-development but with tests and other build steps succeeding.

## Installation and Quick Start

The Planet SDK for Python is [hosted on PyPI](https://pypi.org/project/planet/) and can simply be installed via:

```console
pip install planet
```

To install from source, first clone this repository, then navigate to the root directory (where `setup.py` lives) and run:

```console
pip install .
```

Note that the above commands will install the Planet SDK into the global system Python unless a virtual environment is enabled.  For more information on configuring a virtual environment from system Python, see the official Python [venv](https://docs.python.org/3/library/venv.html) documentation.  For users who are running multiple versions of Python via [pyenv](https://github.com/pyenv/pyenv), see the [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) extension documentation.

Detailed installation instructions for the Planet SDK can be found in the [Quick Start Guide](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/get-started/quick-start-guide/) of the documentation.

## Contributing and Development

To contribute or develop with this library, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation

Documentation is currently [hosted online](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/)
It should be considered 'in progress', with many updates to come. It can also
be built and hosted locally (see [CONTRIBUTING.md](CONTRIBUTING.md)) or can be
read from source in the [docs](/docs) directory.

## Authentication

Planet's APIs require an account for use. To get started you need to
[Get a Planet Account](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/get-started/get-your-planet-account/).
