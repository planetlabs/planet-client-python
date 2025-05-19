---
title: Upgrade from Version 2 to Version 3
---

Version 3 of the Planet SDK for Python is a major update of the SDK offering
new features, not all of which are backwards compatible with version 2.

## Authentication
Version 3 of the SDK removed support for Planet's legacy authentication network
protocols in favor of OAuth2 based authentication mechanisms.  The legacy protocols
were never a [documented API](https://docs.planet.com/develop/apis/), but could
easily be understood by inspection of the SDK code.

Specifically, what is being deprecated in version 3 are the paths where the SDK
handled a username and password to obtain the user's API key for forward
operations.  Users may still operate with an API key by retrieving it from the
Planet user interface under [My Settings](https://www.planet.com/account/#/user-settings)
and providing it to the SDK, but OAuth2 mechanisms should be preferred
where the use case allows for it.

Users may also continue to initialize SDK and CLI sessions with their username
and password, but rather than being processed by the SDK itself a browser must
be invoked to complete an OAuth2 based authentication and authorization exchange.
This new method is intended to offer a number of long term benefits, including:

* The new method provides the SDK and the CLI with access tokens that may be
  used with both `api.planet.com` and `sentinel-hub.com` endpoints.  The methods
  used by version 2 of the SDK were specific to `api.planet.com` endpoints.
* This method extends (currently optional) multifactor authentication (MFA)
  to SDK and CLI platform use cases.
* This method is compatible with other platform enhancements currently under
  development by Planet's software engineering team.

For complete details on the new mechanisms, see the [Client Authentication Guide](../python/sdk-client-auth.md).

### CLI
#### Usage
The [`planet auth`](../../cli/cli-reference/#auth) command has been substantially
revised to align to the new authentication mechanisms.  For migration, the following
changes are the most important to note:

* The `planet auth init` command has been replaced with [`planet auth login`](../../cli/cli-reference/#login).
  By default, this command will open a browser window to allow the user to log
  in to their Planet account and authorize the SDK or CLI to access their account.
  Other options are available to support a variety of use cases.
* The `planet auth value` command has been deprecated.  Depending on whether the SDK
  has been initialized with OAuth2 or API key authentication,
  [`planet auth print-access-token`](../../cli/cli-reference/#print-access-token)
  or [`planet auth print-api-key`](../../cli/cli-reference/#print-api-key) may
  be used.  The OAuth2 based `print-access-token` should be preferred where possible.
* The `planet auth store` command has been deprecated. The various invocations
  of the `planet auth login` command should be suitable for all use cases.
  OAuth2 sessions should be favored for user interactive use cases, such as CLI usage.
  `planet auth login --auth-api-key YOUR_API_KEY` may be used to initialize the SDK
  with API key based authentication where the use case requires it.

#### CLI Session Persistence
Both version 2 and version 3 of the SDK used the file `~/.planet.json` in the user's
home directory to store user API key.  If this file is present and was configured
by version 2 of the SDK, it should continue to work.

While the `~/.planet.json` file continues to be used by version 3, version 3
will not write the same information to this file that version 2 did. Version 3
uses this file in conjunction with the `~/.planet` directory and subdirectories
to store OAuth2 tokens and additional session information needed for a smooth
user experience.

Version 3 of the SDK provides a `planet auth reset` command to reset all saved state
should it become corrupted.  When this command is run, the old files are moved aside
rather than deleted.

### SDK Session Initialization
See the [Client Authentication Guide](../python/sdk-client-auth.md) for a complete
discussion of all the options available.

By default, the most simple SDK code level use cases should work by default with
no alterations, as long as the user has initialized a saved authentication session
using the [`planet auth login`](../../cli/cli-reference/#login) command.

----
