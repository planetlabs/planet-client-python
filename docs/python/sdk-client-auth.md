# Client Authentication Guide

## Introduction
All calls to Planet APIs must be authenticated.  Only authorized clients may
use Planet Platform APIs.

For general information on how to authenticate to Planet APIs, please see
the [Authentication](https://docs.planet.com/develop/authentication) section of Planet's platform documentation.
This documentaiton is focused on use of the Planet Python SDK and
[`planet`](../../cli/cli-reference) CLI.

!!! info
    Work to unify authentication practices between `api.planet.com` and `services.sentinel-hub.com`
    is ongoing and being rolled out in phases over time. Documentation that may
    refer to work in progress is marked as such 🚧.

    Of particular note is general shift towards OAuth2 based authentication,
    and a corresponding move away from Planet API keys.

----

## Authentication Protocols
At the HTTP protocol level underneath the SDK, there are several distinct
ways a client may authenticate to the Planet APIs, depending on the use case.
See [Authentication Protocols](http://docs.planet.com/develop/authentication/#authentication-protocols) for a
complete discussion of when to chose a particular method.

* **OAuth2 user access tokens** - API access as the end-user, using OAuth2
  user access tokens.  This is the preferred way for user interactive
  applications to authenticate to Planet APIs.  A registered client application
  and a web browser are required to initialize a session. A web browser is not
  required for continued operation.  The SDK itself is a registered
  client application that may be used for this purpose.
  Examples of applications that fall into this category include
  [ArcGIS Pro](https://www.esri.com/en-us/arcgis/products/arcgis-pro/overview),
  [QGIS](https://qgis.org/), and the SDK's own [`planet`](../../cli/cli-reference)
  CLI program.  All Planet first party web applications also use this method.
* **OAuth2 M2M access tokens** (🚧 _Work in progress_) - API access as a service user, using OAuth2
  M2M access tokens.  This is the new preferred way for automated processes
  to authenticate to Planet APIs that must operate without a human user.
  No web browser is required, but this method carries some additional
  security considerations.
* **Planet API keys** (⚠️ _Pending future deprecation_) - API access as a Planet end-user using a simple
  fixed string bearer key.  This is the method that has historically been
  documented and recommended for developers using Planet APIs.

### OAuth2
OAuth2 authentication requires that the client possesses an access token
in order to make API calls. Access tokens are obtained by the client from
the Planet authorization server, which is separate from the API servers, and are
presented by the client to API services to assert the client's right to make
API calls.

Unlike Planet API keys, access tokens do not last forever for a variety of
reasons and must be regularly refreshed by the client before their expiration.
When using the Planet SDK, many of the details of obtaining and refreshing
OAuth2 access tokens will be taken care of for you.

OAuth2 defines many different ways to obtain access tokens, and a full discussion
is beyond the scope of this SDK user guide.  Please refer to the [Resources](#resources)
below for more information.  Planet broadly divides OAuth2 use cases into
user interactive and machine-to-machine use cases, as described in this guide.

!!! info
    OAuth2 user access tokens currently work for all Planet APIs under both
    the `api.planet.com` and `services.sentinel-hub.com` domains.

    🚧 OAuth2 machine-to-machine (M2M) access tokens are currently available for use
    with `services.sentinel-hub.com` APIs. Work to support `api.planet.com` is
    ongoing.


### Planet API Keys
Planet API keys are simple fixed strings that may be presented by the client
to API services to assert the client's right to access APIs.  API keys are
obtained by the user from their [Account](https://www.planet.com/account) page
under the [_My Settings_](https://www.planet.com/account/#/user-settings) tab.

!!! warning
    Planet API keys are being targeted for eventual deprecation in favor
    of OAuth2 mechanisms for most use cases. No specific timeframe has been
    set for disabling API keys, but new development should use OAuth2
    mechanisms where possible.

    Planet API keys will work for Planet APIs underneath `api.planet.com`, but
    will **NOT** work for APIs underneath `services.sentinel-hub.com`.

    There is no plan for API keys to ever be supported by APIs underneath
    `services.sentinel-hub.com`.

----

## Authentication with the SDK

### Configuration

When determining how to authenticate requests made against the Planet
APIs, the SDK and the Planet CLI may load their configuration from a number of
sources at runtime:

- Highest priority is given to command-line arguments.  This applies
  only to `planet` CLI use, since programmatic use of the SDK bypasses the CLI program.
  Configuration persisted by the `planet` CLI is saved to configuration files
  (below).
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

#### Environment Variables
When the SDK is not otherwise explicitly configured by an application,
the following environment variables will be used.

| Variable                    | Description                                                                                                                   |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| **`PL_AUTH_PROFILE`**       | Specify a custom CLI managed auth client profile by name.  This must name a valid CLI managed profile or an error will occur. |
| **`PL_AUTH_CLIENT_ID`**     | Specify an OAuth2 M2M client ID.  `PL_AUTH_CLIENT_SECRET` must also be specified, or this will be ignored.                    |
| **`PL_AUTH_CLIENT_SECRET`** | Specify an OAuth2 M2M client secret. `PL_AUTH_CLIENT_ID` must also be specified, or this will be ignored.                     |
| **`PL_AUTH_API_KEY`**       | Specify a legacy Planet API key.                                                                                              |

#### Reset User Configuration
The following commands may be used to clear an environment of any
previously configured settings:

```sh title="Clear saved authentication settings"
unset PL_API_KEY
unset PL_AUTH_PROFILE
unset PL_AUTH_CLIENT_ID
unset PL_AUTH_CLIENT_SECRET
planet auth reset
```

### Profiles
Collectively, the configuration of the SDK to use a specific authentication
protocol (see above) and a working set of session state information is
termed a _profile_ by the SDK and the CLI.  Profiles are an abstraction
of the SDK and the CLI, and are not inherent to authentication to the
Planet platform generally.

The [`planet auth profile`](../../cli/cli-reference/#profile) CLI command
is provided to manage persistent profiles and sessions in the user's home
directory. Home directory persisted profiles are shared between the CLI
and applications built using the SDK.

Applications built using the SDK may be configured to bypass home directory
profile and session storage, if this better suits the needs of the application.

### Sessions

Before any calls can be made to a Planet API using the SDK, it is
necessary for the user to login and establish an authentication session.
Exactly how this should be done with the SDK depends on the
application's complexity and needs.

In simple cases, this may be managed external to the application
by using the [`planet auth`](../../cli/cli-reference/#auth)
command-line utility.

In more complex cases, an application may need to manage the
stored session itself independent of utilities provided by the CLI. In such
cases, the application will be responsible for instantiating a `planet.Auth`
object, initiating user login, and saving the resulting session information.
Session information may contain sensitive information such as access and
refresh tokens, and must be stored securely by the application.  Session
information will also be regularly updated during SDK operations, so the
application must handle callbacks to store updated session information.

Regardless of which authentication protocol is used, the SDK encapsulates
the details with
[`planet.Auth`](../sdk-reference/#planet.auth.Auth) and
[`planet.Session`](../sdk-reference/#planet.http.Session).

#### Session Persistence

Once a user login session is established using any method, the state should be
saved to secure persistent storage to allow for continued access to the Planet
platform without the need to perform the login repeatedly.  If state cannot
be persisted in the application environment, the application can operate in
in-memory mode, but will be forced to create a new login session every time the
application is run.  If the rate of repeated logins is too great, this may
result in throttling by the authorization service.

The SDK provides the option to save session state in the user's
home directory in a way that is compatible with the CLI.  The SDK also
provides a way for the application to provide its own secure storage.
Applications needing to use their own storage will do so by providing
the `Auth` layer in the SDK with a custom implementation of the
[`planet_auth.ObjectStorageProvider`](https://planet-auth.readthedocs.io/en/latest/api-planet-auth/#planet_auth.ObjectStorageProvider)
abstract base class.  See examples below for more details.

### CLI Managed Sessions
For simple programs and scripts, it is easiest for the program to defer
session management to the [`planet auth`](../../cli/cli-reference/#auth)
CLI.   This method will store session information in the user's home directory
in the `~/.planet.json` file and `~/.planet/` directory.  The Python SDK will
use the information saved in these locations to make API calls.

When this approach is taken, the authentication session will be shared between
actions taken by the `planet` utility and those taken by the programs built
using the SDK.  Changes made by one will impact the behavior of the other.

CLI managed sessions can be used for all authentication protocols.

**Requirements and Limitations:**

* The program must have read and write access to the user's home directory.
* This method requires that the end-user has access to and understands
  the [`planet`](../../cli/cli-reference) CLI command needed to manage session
  authentication.
* This approach should not be used on public terminals or in cases where the
  user's home directory cannot be kept confidential.

#### Initialize Session - CLI Login
Session login can be performed using the following command.  This command can
be used to initialize sessions using any of the authentication methods
discussed above, and will default to creating an OAuth2 user session.
Refer to the command's `--help` for more information.
```shell title="Initialize session using planet CLI"
planet auth login
```

#### Using Saved Session
Using the CLI managed session is the default behavior for SDK functions.
Developing an application that uses this session requires no additional
action by the developer.  When a developer chooses to create an application
that behaves in this way, it will most often be done implicitly by relying
on SDK default behavior, but it may also be done explicitly.

```python linenums="1" title="Implicitly use CLI managed login sessions"
{% include 'auth-session-management/cli_managed_auth_state__implicit.py' %}
```

```python linenums="1" title="Explicitly use CLI managed login sessions"
{% include 'auth-session-management/cli_managed_auth_state__explicit.py' %}
```

Applications may be developed to always select a specific CLI managed profile.
This may be useful in cases where an application `my-application` may wish to
guide the user experience towards expecting CLI sessions and `my-application`
sessions to always be separate from the default CLI user session.

```python linenums="1" title="Use a specific session that is shared with the CLI"
{% include 'auth-session-management/cli_managed_auth_state__specific_auth_profile.py' %}

```

### Application Managed Sessions
If an application cannot or should not use a login session initiated by the
[`planet auth`](../../cli/cli-reference/#auth) CLI command, it will be
responsible for managing the process on its own, persisting session state as
needed.

Application managed sessions may be used with all authentication protocols.
Application developers may control whether sessions are visible to the CLI.

The process varies depending on the authentication protocol used.
Depending on the use case, applications may need to support multiple authenticaiton
methods, just as the [`planet`](../../cli/cli-reference) CLI command supports interacting with Planet APIs
using either a user or a service user account.

#### OAuth2 Session for Users
User session initialization inherently involves using a web browser to
complete user authentication.  This architecture allows for greater security
by keeping the user's password from being directly exposed to the application
code. This also allows for flexibility in user federation and multifactor
authentication procedures without the complexity of these needing to
be exposed to the application developer who is focused on geospatial
operations using the Planet platform, and not the nuances of user
authentication and authorization.

##### With a Local Web Browser
In environments where a local browser is available, the Planet SDK can manage
the process of launching the browser locally, transferring control to the Planet
authorization services for session initialization, and accepting a network
callback from the local browser to regain control once the authorization
process is complete. At a network protocol level, this is establishing the user
login session using the OAuth2 authorization code flow.

To use this method using the SDK, the following requirements must be met:

* The application must be able to launch a local web browser.
* The web browse must be able to connect to Planet services.
* The application must be able to listen on a network port that is accessible
  to the browser.

###### Examples - OAuth2 Authorization Code Flow
```python linenums="1" title="Login as a user using a local browser with in memory only state persistance"
{% include 'auth-session-management/app_managed_auth_state__in_memory__oauth_user_authcode__with_browser.py' %}
```

```python linenums="1" title="Login as a user using a local browser with sessions persisted on disk and shared with the CLI"
{% include 'auth-session-management/app_managed_auth_state__on_disk_cli_shared__oauth_user_authcode__with_browser.py' %}
```

```python linenums="1" title="Login as a user using a local browser with sessions persisted to application provided storage"
{% include 'auth-session-management/app_managed_auth_state__app_custom_storage__oauth_user_authcode__with_browser.py' %}
```

##### Without a Local Web Browser
In environments where a local web browser is not available, additional steps must
be taken by the application author to initialize the user session.
For example, a remote shell to a cloud environment is not likely
to be able to open a browser on the user's desktop or receive network callbacks
from the user's desktop browser.  In these cases, a browser is
still required.  To complete login in such a case, the SDK will generate a URL and a
verification code that must be presented to the user. The user must visit the
URL out of band to complete the login process while the application polls for
the completion of the login process using the SDK.  At a network protocol
level, this is establishing the user login session using the OAuth2 device
code flow.

To use this method using the SDK, the following requirements must be met:

* The application must be able to connect to Planet services.
* The application must be able to display instructions to the user, directing
  them to a web location to complete login.

###### Examples - OAuth2 Device Code Flow
```python linenums="1" title="Login as a user using an external browser with in memory only state persistance"
{% include 'auth-session-management/app_managed_auth_state__in_memory__oauth_user_devicecode__external_browser.py' %}
```

```python linenums="1" title="Login as a user using an external browser with sessions persisted on disk and shared with the CLI"
{% include 'auth-session-management/app_managed_auth_state__on_disk_cli_shared__oauth_user_devicecode__external_browser.py' %}
```

```python linenums="1" title="Login as a user using an external browser with sessions persisted to application provided storage"
{% include 'auth-session-management/app_managed_auth_state__app_custom_storage__oauth_user_devicecode__external_browser.py' %}
```

#### OAuth2 Session for Service Accounts
Service account session initialization is simpler than user session
initialization, and does not require a web browser.

While preserving session state for user sessions was a concern driven
in part by a concern for the user experience of using a web browser for
initialization, for service account it remains a concern to avoid
throttling by the authorization service.

If applications are expected to run longer than the life of an access token
(a few hours), then in memory operations are acceptable (for example: a long
running data processing job).  If application lifespan is short and frequent,
than the application should still take steps to persist the session state (for
example: a command line utility run from a shell with a short lifespan).

Like the session state itself, service account initialization parameters are
sensitive, and it is the responsibility of the application to store them
securely.

At a network protocol level, OAuth2 service account sessions are implemented
using the OAuth2 authorization code flow.  This carries with it some additional
security considerations, discussed in
[RFC 6819 §4.4.4](https://datatracker.ietf.org/doc/html/rfc6819#section-4.4.4).
Because of these consideration, service accounts should only be used for
workflows that are independent of a controlling user.

##### Examples - OAuth2 Client Credentials Flow
```python linenums="1" title="Access APIs using a service account with in memory only state persistance"
{% include 'auth-session-management/app_managed_auth_state__in_memory__oauth_m2m.py' %}
```

```python linenums="1" title="Access APIs using a service account with sessions persisted on disk and shared with the CLI"
{% include 'auth-session-management/app_managed_auth_state__on_disk_cli_shared__oauth_m2m.py' %}
```

```python linenums="1" title="Access APIs using a service account with sessions persisted to application provided storage"
{% include 'auth-session-management/app_managed_auth_state__app_custom_storage__oauth_m2m.py' %}
```

#### Planet API Key Sessions
Legacy applications that need to continue to support Planet API keys may do so
until API keys are deprecated. This method should not be adopted for new
development.

##### Examples - Planet API Keys

```python linenums="1" title="Access APIs using Planet API keys in memory"
{% include 'auth-session-management/app_managed_auth_state__in_memory__api_key.py' %}
```

```python linenums="1" title="Access APIs using Planet API keys using the on disk file format used by older versions of the SDK"
{% include 'auth-session-management/app_managed_auth_state__on_disk_legacy__api_key.py' %}
```

```json linenums="1" title="Legacy API Key file"
{% include 'auth-session-management/legacy_api_key_file.json' %}
```

```python linenums="1" title="Access APIs using Planet API keys with CLI managed shared state on disk"
{% include 'auth-session-management/app_managed_auth_state__on_disk_cli_shared__api_key.py' %}
```

```python linenums="1" title="Access APIs using Planet API keys using legacy on disk persistance"
{% include 'auth-session-management/app_managed_auth_state__app_custom_storage__api_key.py' %}
```

----

## Resources
More information regarding OAuth2 and JWTs may be found here:

* [RFC 6749 - The OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
* [RFC 8628 - OAuth 2.0 Device Authorization Grant](https://datatracker.ietf.org/doc/html/rfc8628)
* [RFC 7519 - JSON Web Token (JWT)](https://datatracker.ietf.org/doc/html/rfc7519)
* [RFC 9068 - JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens](https://datatracker.ietf.org/doc/html/rfc9068)
* [RFC 6819 - OAuth 2.0 Threat Model and Security Considerations](https://datatracker.ietf.org/doc/html/rfc6819)

----
