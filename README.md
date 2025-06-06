# Planet SDK for Python

[![Build Status](https://github.com/planetlabs/planet-client-python/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/planetlabs/planet-client-python/actions/workflows/test.yml)
[![PyPI Downloads](https://static.pepy.tech/badge/planet)](https://pepy.tech/projects/planet)

The [Planet](https://planet.com) Software Development Kit (SDK) for Python
provides both a Python API and a command-line interface (CLI)
to make use of [the Planet APIs](https://docs.planet.com/develop/apis/).
Everything you need to get started is found in our
[online documentation](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/).

Version 2.0 includes support for the core workflows of the following APIs:

* [Data](https://docs.planet.com/develop/apis/data/) - Search for imagery from Planet's data catalog.
* [Orders](https://docs.planet.com/develop/apis/orders/) - Process and download or deliver imagery.
* [Subscriptions](https://docs.planet.com/develop/apis/subscriptions/) - Set up a search to auto-process and deliver imagery.
* [Features](https://docs.planet.com/develop/apis/features/) - Upload areas of interest to the Planet platform.

After the initial 2.0 release there will be additional work to support the
remaining Planet APIs: [basemaps](https://docs.planet.com/develop/apis/basemaps/),
[tasking](https://docs.planet.com/develop/apis/tasking/) and
[analytics](https://docs.planet.com/develop/apis/analytics/).

## Versions and Stability

The SDK follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and therefore only major releases
should break compatibility. Minor versions may include new functionality and
patch versions address bugs or trivial changes (like documentation).

Packages will be released to [PyPi / Planet](https://pypi.org/project/planet/)
with semantic version identifiers that comply with [PEP 440](https://peps.python.org/pep-0440/).

The Semantic Versioning stability scheme only applies to APIs that
are considered part of the public API.  This includes library APIs exported
from the `planet` package and documented in our
[SDK developer documentation](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/),
and the `planet` CLI interface used for scripts.  It does not include
library interfaces below the top level `planet` Python package which are
considered internal and subject to change without notice.

SDK semantic versioning does not apply to the underlying
[Planet APIs](https://docs.planet.com/develop/apis/),
which follow their own independent version and release lifecycles.

If depending upon official packages from PyPI, a developer should feel
comfortable specifying `planet == 2.*` unless depending on a specific feature
introduced at a minor version, in which case `planet == 2.x.*` (where x is the
minor version of the new feature) should suffice.

## Versions and Support Status

Major versions are supported according to their designated support status,
as defined below.  Planet Labs PBC makes no formal commitment
to a specific schedule, but will make every effort to provide reasonable
notice of upcoming changes to the support status of major versions.

* **`development`** - Unstable. Under active development.  Not recommended
  for production use.  API stability not guaranteed.  New features from active
  versions will be ported forward to the extent allowed by the scope of the
  new major version under development.
* **`active`** - Actively maintained and supported. New features and bug fixes.
  Suitable for production use.  API stability guaranteed according to semantic
  versioning, but subject to changes in the underlying Planet APIs.
* **`maintenance`** - Critical bug fixes only.
* **`end-of-life`** - No longer supported.  Software packages will remain available.
* **`removed`** - No longer available.  Removed from distribution channels.

### Python Version Support
`Active` minor versions will support Python versions that have not reached
end-of-life at the time of release.

See https://devguide.python.org/versions/ for current Python versions.

## Branches

The default branch is always `main`, and will correspond to the current stable
major release version. This branch should be considered in-development but
with tests and other build steps kept in a passing state.

See [CONTRIBUTING.md](CONTRIBUTING.md#branches) for more information on branches.

##### Current Mainline Versions and Branches

| Version | Status        | Branch                                                                                 | Documentation                                                                                                | Initial Release | End of Active Development | End of Maintenance | Notes                                                                                           |
|---------|---------------|----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|-----------------|---------------------------|--------------------|-------------------------------------------------------------------------------------------------|
| 3.x     | `development` | [`main-3.0-dev`](https://github.com/planetlabs/planet-client-python/tree/main-3.0-dev) | [Planet Labs Python Client on ReadTheDocs.io](https://planet-sdk-for-python.readthedocs.io/en/latest/)       | TBD             | TBD                       | TBD                | See [3.0.0 Release Milestone](https://github.com/planetlabs/planet-client-python/milestone/31). |
| 2.x     | `active`      | [`main`](https://github.com/planetlabs/planet-client-python/tree/main)                 | [Planet Labs Python Client v2 on ReadTheDocs.io](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/) | April 2023      | TBD                       | TBD                |                                                                                                 |
| 1.x     | `end-of-life` | [`v1`](https://github.com/planetlabs/planet-client-python/tree/v1)                     | [Planet Labs Python Client v1 on Github.io](https://planetlabs.github.io/planet-client-python/)              | April 2017      | April 2023                | TBD                |                                                                                                 |

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
