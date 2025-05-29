# Client Authentication Guide

## Introduction
All calls to Planet APIs must be authenticated.  Only authorized clients may
use Planet Platform APIs.

For general information on how to authenticate to Planet APIs, please see
the [Authentication](https://docs.planet.com/develop/authentication) section of Planet's platform documentation.

!!! warning
    Some statements in this guide are forward-looking.

    OAuth2 M2M tokens are currently only supported by `services.sentinel-hub.com`,
    and are not yet supported by `api.planet.com`. This is planned for a future date
    to be announced.

    All APIs support interactive user OAuth2 access tokens, but a process for
    developers to register and manage clients has not yet been made public.
    We have also not yet released a way for end-users of such applications to
    manage which applications have been authorized to access the platform on
    their behalf.

    If you would like to develop an interactive application that uses
    Planet's APIs on behalf of a logged-in user (as the `planet` CLI utility
    does), please contact Planet support and work with engineering to
    register your application.

----
## Authentication Protocols
At the API protocol level underneath the SDK, there are several distinct
ways a client may authenticate to the Planet APIs, depending on the use case:

* **OAuth2 user access tokens** - API access as the end-user, using OAuth2
user access tokens.  This is the preferred way for user interactive
applications to authenticate to Planet APIs.  A web browser is required
to initialize a session, but not required for continued operation.
* **OAuth2 M2M access tokens** - API access as a service user, using OAuth2
M2M access tokens.  This is the preferred way for automated processes
to authenticate to Planet APIs that must operate without a human user.
No web browser is required, but this method carries some additional
security considerations.
* **Planet API keys** - API access as a Planet end-user using a simple
fixed string bearer key.  This method is being targeted for deprecation.

### OAuth2
OAuth2 authentication requires that the client possesses an access token
in order to make API calls. Access tokens are obtained by the client from
the Planet authorization server, which is separate from the API servers, and are
presented by the client to API services to prove the client's right to make
API calls.

Unlike Planet API keys, access tokens do not last forever for a variety of
reasons and must be regularly refreshed by the client before their expiration.
However, clients should not refresh access tokens for every API call; clients
that misbehave in this way will be throttled by the authorization service,
potentially losing access to APIs.

When using the Planet SDK, many of the details of obtaining and refreshing
OAuth2 access tokens will be taken care of for you.

Planet OAuth2 access tokens will work for all Planet APIs underneath
both the `api.planet.com` and `services.sentinel-hub.com` domains.

Planet access tokens conform to the JSON Web Token (JWT) specification.
Tokens may be inspected to determine their expiration time, which will be
in the `exp` claim.

!!! note
    Clients should generally treat the access tokens as opaque bearer tokens.
    While JWTs are open for inspection, Planet does not guarantee the stability
    of undocumented claims.  Rely only on those documented here.

More information regarding OAuth2 and JWTs may be found here:

* [RFC 6749 - The OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
* [RFC 8628 - OAuth 2.0 Device Authorization Grant](https://datatracker.ietf.org/doc/html/rfc8628)
* [RFC 7519 - JSON Web Token (JWT)](https://datatracker.ietf.org/doc/html/rfc7519)
* [RFC 9068 - JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens](https://datatracker.ietf.org/doc/html/rfc9068)

#### OAuth2 Client Registration
!!! TODO
    * link to docs for this process
    * discuss registering a interactive client (that will access Planet
    as the user) vs registering a M2M client identity (which is really
    more like creating a new user) vs registering a confidential client.
    discuss native vs web clients.

Developers of applications must register client applications with Planet, and
will be issued a Client ID as part of that process.  Developers should register
a client for each distinct application so that end-users may discretely manage
applications permitted to access Planet APIs on their behalf.

### Planet API Keys
Planet API keys are simple fixed strings that may be presented by the client
to API services to assert the client's right to access APIs.  API keys are
obtained by the user from their account page and provided to the client
so that it may make API calls on the user's behalf.

Planet API keys are simpler to use than OAuth2 mechanisms, but are considered less secure
in many ways.  Because of this, Planet API keys are targeted for eventual
deprecation.  Support for this method is maintained for continuity
while OAuth2 based methods are being rolled out across all Planet APIs and
clients.

Planet API keys will work for Planet APIs underneath `api.planet.com`, but
will **NOT** work for APIs underneath `services.sentinel-hub.com`.

----
## Authentication with the SDK

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
application must handle keeping the saved session information up-to-date.

Regardless of which authentication protocol is used, the SDK encapsulates
the details with
[`planet.Auth`](../sdk-reference/#planet.auth.Auth) and
[`planet.Session`](../sdk-reference/#planet.http.Session).

#### Session State Storage

Once a user login session is established using any method, the state should be
saved to secure persistent storage to allow for continued access to the Planet
platform without the need to perform the login repeatedly.  If state cannot
be persisted in the application environment, the application can operate in
in-memory mode, and will be forced to create a new login session every time the
application is run.  In some cases, this may result in throttling by the
authorization service.

By default, the SDK provides the option to save session state in the user's
home directory in a way that is compatible with the CLI.  The SDK also
provides a way for the application to provide its own secure storage.
Applications needing to use their own storage will do so by providing
the `Auth` layer in the SDK with a custom implementation of the
`planet_auth.ObjectStorageProvider` abstract base class.  See examples
below for more details.

### Using `planet auth` CLI Managed Auth Session
For simple programs and scripts, it is easiest for the program to defer
session management to the [`planet auth`](../../cli/cli-reference/#auth)
CLI.   This method will store session information in the user's home directory
in the `~/.planet.json` file and `~/.planet/` directory.  The Python SDK will
use the information saved in these locations to make API calls.

When this approach is taken, the authentication session will be shared between
actions taken by the `planet` utility and those taken by the programs built
using the SDK.  Changes made by one will impact the behavior of the other.

**Requirements and Limitations:**

* The program must have read and write access to the user's home directory.
* This method requires that the end-user has access to and understands
  the [`planet`](../../cli/cli-reference) CLI command needed to manage session
  authentication.
* This approach should not be used on public terminals or in cases where the
  user's home directory cannot be kept confidential.

#### Initialize Session - Login
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

```python linenums="1" title="Use a specific session that is shared with the CLI"
{% include 'auth-session-management/cli_managed_auth_state__specific_auth_profile.py' %}

```

### Manually Creating a Session Using Library Functions
If an application cannot or should not use a login session initiated by the
[`planet auth`](../../cli/cli-reference/#auth) CLI command, it will be
responsible for managing the process on its own, persisting session state as
needed.

The process differs slightly for applications accessing Planet services on behalf
of a human user verses accessing Planet services using a service account.  Depending
on the use case, applications may need to support one or the other or both (just
as the [`planet`](../../cli/cli-reference) CLI command supports both methods).

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

###### Examples - Authorization Code Flow
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
In environments where a local web browsers is not available the process above
will not work.  For example, a remote shell to a cloud environment is not likely
to be able to open a browser on the user's desktop or receive network callbacks
from the user's desktop browser.  In these cases, a browser is
still required.  To login in such a case the SDK will generate a URL and a
verification code that must be presented to the user. The user must visit the
URL out of band to complete the login process while the application polls for
the completion of the login process using the SDK.  At a network protocol
level, this is establishing the user login session using the OAuth2 device
code flow.

To use this method using the SDK, the following requirements must be met:

* The application must be able to connect to Planet services.
* The application must be able to display instructions to the user, directing
  them to a web location to complete login.

###### Examples - Device Code Flow
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

##### Examples - Client Credentials Flow
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

## OAuth2 Scopes
OAuth2 uses scopes to allow users to limit how much access clients have to the Planet
service on their behalf.

* **`planet`** - Use this scope to request access to Planet APIs.
* **`offline_acess`** - Use this scope to request a refresh token.  This may
  only be requested by clients that access APIs on behalf of a user.  M2M
  clients may not request this scope.


## Environment Variables
When session information is not explicitly configured, the following environment variables
will influence the library behavior when initialized to user default preferences.

* **`PL_AUTH_PROFILE`** - Specify a custom CLI managed auth client profile by name.
* **`PL_AUTH_CLIENT_ID`** - Specify an OAuth2 M2M client ID.
* **`PL_AUTH_CLIENT_SECRET`** - Specify an OAuth2 M2M client secret.
* **`PL_AUTH_API_KEY`** - Specify a legacy Planet API key.
----


## Web Services
!!! TODO
    All of the above really deals with native applications running in an
    environment controlled by the end-user.  The considerations
    are different if the application being developed is a web service where
    the end-user is not directly accessing Planet APIs.  This involves
    "Confidential" OAuth2 client configurations, and needs to be documented
    here.

----
