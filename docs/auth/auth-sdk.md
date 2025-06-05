# Authentication with the SDK

## Overview
The [`planet.Auth`](../../python/sdk-reference/#planet.auth.Auth) class is the
main class that is responsible for managing how clients built with the SDK
authenticate to the Planet Insights Platform API services.  By default,
API clients provided by the SDK will create an `Auth` instance that is connected
to login sessions managed by the [`planet auth`](../../cli/cli-reference/#auth)
CLI utility, with state saved to the `.planet.json` file and `.planet`
directory in the user's home directory.

When applications require more control over the authentication process,
constructor methods on the [`planet.Auth`](../../python/sdk-reference/#planet.auth.Auth)
class may be used to create instances with specific configurations.
`Auth` instances may then be wrapped in [`planet.Session`](../../python/sdk-reference/#planet.http.Session)
objects so they can be attached to the
[`planet.Planet`](../../python/sdk-reference/#planet.client.Planet) synchronous
client, or various [asynchronous API clients](../../python/async-sdk-guide/) provided by the SDK.

## Configuration

When determining how to authenticate requests made against the Planet
APIs, the default behavior of the SDK and the Planet CLI is to load
configuration from a number of sources at runtime:

- Highest priority is given to arguments passed to the [`Auth`](../../python/sdk-reference/#planet.auth.Auth)
  class (when using the SDK) or via the command line (when using the CLI).
  When saving preferences using the CLI, configuration is saved to
  configuration files (below).
- Next, environment variables are checked.
  Of these, `PL_API_KEY` has been used by Planet software for many years,
  and is the most likely to be set in a user's environment.
  The other environment variables are new to version 3 of the Planet Python SDK.
  **Note**: This means that environment variables override configuration
  saved by the `planet` CLI program.  See [Environment Variables](#environment-variables)
  below.
- Then, the configuration file `.planet.json` and files underneath
  the `.planet` directory in the user's home directory are consulted.
  These configuration files may be managed with the
  [`planet auth profile`](../../cli/cli-reference/#profile) CLI command.
- Finally, built-in defaults will be used.

### Environment Variables
When the SDK is not otherwise explicitly configured by an application,
or behavior is not overridden by command-line arguments, the following
environment variables will be used:

| Variable                    | Description                                                                                                                   |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| **`PL_AUTH_PROFILE`**       | Specify a custom CLI managed auth client profile by name.  This must name a valid CLI managed profile or an error will occur. |
| **`PL_AUTH_CLIENT_ID`**     | Specify an OAuth2 M2M client ID.  `PL_AUTH_CLIENT_SECRET` must also be specified, or this will be ignored.                    |
| **`PL_AUTH_CLIENT_SECRET`** | Specify an OAuth2 M2M client secret. `PL_AUTH_CLIENT_ID` must also be specified, or this will be ignored.                     |
| **`PL_AUTH_API_KEY`**       | Specify a legacy Planet API key.                                                                                              |

When multiple conflicting environment variables are set, `PL_AUTH_PROFILE` is
preferred over `PL_AUTH_CLIENT_ID` and `PL_AUTH_CLIENT_SECRET`, which are
preferred over `PL_AUTH_API_KEY`.

### Reset User Configuration
The following commands may be used to clear an environment of any
previously configured settings:

```sh title="Clear saved authentication settings"
unset PL_API_KEY
unset PL_AUTH_PROFILE
unset PL_AUTH_CLIENT_ID
unset PL_AUTH_CLIENT_SECRET
planet auth reset
```

## Profiles
Collectively, the configuration of the SDK to use a specific authentication
protocol (see [overview](../auth-overview#authentication-protocols)) and a
working set of session state information is termed a _profile_ by the SDK 
and the CLI.  Profiles are an abstraction of the SDK and the CLI, and are 
not inherent to authentication to the Planet platform generally.

The [`planet auth profile`](../../cli/cli-reference/#profile) CLI command
is provided to manage persistent profiles and sessions in the user's home
directory. These home directory persisted profiles are shared between the CLI
and applications built using the SDK.

Applications built using the SDK may be configured to bypass home directory
profile and session storage, if this better suits the needs of the application.
See [Applicaiton Managed Sessions](../auth-dev-app-managed-oauth) for detailed
examples.

## Sessions

Before any calls can be made to a Planet API using the SDK, it is
necessary for the user to login and establish an authentication session.
Exactly how this should be done with the SDK depends on the
application's complexity and needs.

In simple cases, this may be managed external to the application
by using the [`planet auth`](../../cli/cli-reference/#auth)
command-line utility.  See [CLI Managed Sessions](../auth-dev-cli-managed)
for examples.

In more complex cases, an application may need to manage the
stored session itself independent of utilities provided by the CLI. In such
cases, the application will be responsible for instantiating a `planet.Auth`
object, initiating user login, and saving the resulting session information.
Session information may contain sensitive information such as access and
refresh tokens, and must be stored securely by the application.  Session
information will also be regularly updated during SDK operations, so the
application must handle callbacks to store updated session information.
See [Application Managed Sessions](../auth-dev-app-managed-oauth)
for examples.

### Session Persistence

Once a user login session is established using any method, the state should be
saved to secure persistent storage to allow for continued access to the Planet
platform without the need to perform the login repeatedly.  If state cannot
be persisted in the application environment, the application can operate in
in-memory mode, but will be forced to create a new login session every time the
application is run.  If the rate of repeated logins is too great, this may
result in throttling by the authorization service.  Particular attention should
be paid to this when creating automated processes that utilize service users.

The SDK provides the option to save session state in the user's
home directory in a way that is compatible with the CLI.
When [CLI Managed Sessions](../auth-dev-cli-managed) are used, no additional
steps should be required of the application developer.

The SDK also provides a way for the application to provide its own secure
storage.  Applications needing to use their own storage will do so by
providing the `Auth` layer in the SDK with a custom implementation of the
[`planet_auth.ObjectStorageProvider`](https://planet-auth.readthedocs.io/en/latest/api-planet-auth/#planet_auth.ObjectStorageProvider)
abstract base class.

----
