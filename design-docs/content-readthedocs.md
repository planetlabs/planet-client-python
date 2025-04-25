# _ReadTheDocs.io_ Content Management

## Overview
Pursuant to the [Content Plan](./content-plan.md) developed as part of the
v2.0 release of the SDK, [_ReadTheDocs.io_](https://planet-sdk-for-python.readthedocs.io/)
is used to host the single source of truth for SDK documentation.  SDK documentation
is largely confined to the specifics of using the SDK.  More general Planet Platform
narrative and HTTP API documentation should be hosted on the Planet documentation site
at [docs.planet.com](https://docs.planet.com/).

## Version Management
_ReadTheDocs.io_ hosts multiple versions of the documentation simultaneously.
All versions of the documentation will be published under a _ReadTheDocs.io_
URL that explicitly includes the SDK version so that PyPi published packages
will always have corresponding _ReadTheDocs.io_ documentation for users.

Additionally, the following symbolic names are maintained:
* [**default**](https://planet-sdk-for-python.readthedocs.io/) - Should point to same version as `stable`.
* [**stable**](https://planet-sdk-for-python.readthedocs.io/en/stable/) - Should point to the highest stable release version.
* [**latest**](https://planet-sdk-for-python.readthedocs.io/en/latest/) - Should point to the most recent build from the current mainline major version branch.

Version management is handled by _ReadTheDocs.io_ [automation rules](https://app.readthedocs.org/dashboard/planet-sdk-for-python/rules/).

## _ReadTheDocs.io_ Planet PBC Account
Planet currently publishes to _ReadTheDocs.io_ as a [community](https://about.readthedocs.com/pricing/#/community)
project.  It is understood that this means that ads may be displayed on hosted documentation.  (Ref: cleared
with Planet Engineering Management in April 2025.)

----
