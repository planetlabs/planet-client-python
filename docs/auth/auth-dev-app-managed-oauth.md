# Application Managed Sessions - OAuth2

If an application cannot or should not use a login session initiated by the
[`planet auth`](../../cli/cli-reference/#auth) CLI command, the application will be
responsible for managing the process on its own, persisting session state as
needed.

Application managed sessions may be used with all authentication protocols.
Application developers may control whether sessions are visible to the CLI.
This is managed with the `save_state_to_storage` parameter on the `planet.Auth`
constructor methods illustrated below.

The process varies depending on the authentication protocol used.
Depending on the use case, applications may need to support multiple authentication
methods, just as the [`planet`](../../cli/cli-reference) CLI command supports interacting with Planet APIs
using either a user or a service user account.

## OAuth2 Session for Users
User session initialization inherently involves using a web browser to
complete user authentication.  This architecture allows for greater security
by keeping the user's password from being directly exposed to the application
code. This also allows for flexibility in user federation and multifactor
authentication procedures without the complexity of these needing to
be exposed to the application developer who is focused on geospatial
operations using the Planet platform, and not the nuances of user
authentication and authorization.

### OAuth2 User Client Registration
Developers of applications must register client applications with Planet, and
will be issued a Client ID as part of that process.  Developers should register
a client for each distinct application so that end-users may discretely manage
applications permitted to access Planet APIs on their behalf.

See [OAuth2 Client Registration](http://docs.planet.com/develop/authentication/#interactive-client-registration)
for more information.

### With a Local Web Browser
In environments where a local browser is available, the Planet SDK library can manage
the process of launching the browser locally, transferring control to the Planet
authorization services for session initialization, and accepting a network
callback from the local browser to regain control once the authorization
process is complete. At a network protocol level, this establishes the user
login session using the OAuth2 authorization code flow.

To use this method using the SDK, the following requirements must be met:

* The application must be able to launch a local web browser.
* The web browser must be able to connect to Planet services.
* The application must be able to listen on a network port that is accessible
  to the browser.

#### Examples - OAuth2 Authorization Code Flow

##### In Memory Session State
When an application cannot safely store user session state, it may operate purely in memory. When this
method is used, the user will be prompted to complete the login process each time the application is run.

```python linenums="1" title="Login as a user using a local browser with in memory only state persistance"
{% include 'auth-session-management/app_managed_auth_state__in_memory__oauth_user_authcode__with_browser.py' %}
```

##### Session State Shared with CLI
Applications may save their session state in a way that is shared with the CLI.  With saved state,
the user will only be prompted to complete the login process once.
```python linenums="1" title="Login as a user using a local browser with sessions persisted on disk and shared with the CLI"
{% include 'auth-session-management/app_managed_auth_state__on_disk_cli_shared__oauth_user_authcode__with_browser.py' %}
```

#####  Session State Saved to Application Storage
Applications may save their session state to application provided storage.  With saved state,
the user should only be prompted to complete the login process once.  Using application provided storage
will result in the session state not being shared with the CLI.

Applications needing to use their own storage will do so by providing
the `Auth` layer in the SDK with a custom implementation of the
[`planet_auth.ObjectStorageProvider`](https://planet-auth.readthedocs.io/en/latest/api-planet-auth/#planet_auth.ObjectStorageProvider)
abstract base class.  See examples below for more details.

```python linenums="1" title="Login as a user using a local browser with sessions persisted to application provided storage"
{% include 'auth-session-management/app_managed_auth_state__app_custom_storage__oauth_user_authcode__with_browser.py' %}
```

### Without a Local Web Browser
In environments where a local web browser is not available, additional steps must
be taken by the application author to initialize the user session.
For example, a remote shell to a cloud environment is not likely
to be able to open a browser on the user's desktop or receive network callbacks
from the user's desktop browser.  In these cases, a browser is
still required.  To complete login in such a case, the SDK will generate a URL and a
verification code that must be presented to the user. The user must visit the
URL out of band to complete the login process while the application polls for
the completion of the login process using the SDK. At a network protocol
level, this establishes the user login session using the OAuth2 device
code flow.

To use this method using the SDK, the following requirements must be met:

* The application must be able to connect to Planet services.
* The application must be able to display instructions to the user, directing
  them to a web location to complete login.

As above, this may be done with state only persisted in memory, with state
shared with the CLI, or with state saved to application provided storage.

#### Examples - OAuth2 Device Code Flow

##### In Memory Session State
```python linenums="1" title="Login as a user using an external browser with in memory only state persistance"
{% include 'auth-session-management/app_managed_auth_state__in_memory__oauth_user_devicecode__external_browser.py' %}
```

##### Session State Shared with CLI
```python linenums="1" title="Login as a user using an external browser with sessions persisted on disk and shared with the CLI"
{% include 'auth-session-management/app_managed_auth_state__on_disk_cli_shared__oauth_user_devicecode__external_browser.py' %}
```

#####  Session State Saved to Application Storage
```python linenums="1" title="Login as a user using an external browser with sessions persisted to application provided storage"
{% include 'auth-session-management/app_managed_auth_state__app_custom_storage__oauth_user_devicecode__external_browser.py' %}
```

## OAuth2 Session for Service Accounts
Service account session initialization is simpler than user session
initialization, and does not require a web browser.

While preserving session state for user sessions was a concern driven
in part by a concern for the user experience of using a web browser for
initialization, for service accounts it remains a concern to avoid
throttling by the authorization service.

If applications are expected to run longer than the life of an access token
(a few hours), then in memory operations are acceptable (for example: a long-running
data processing job).  If application lifespan is short and frequent,
then the application should take steps to persist the session state (for
example: a command line utility run repeatedly from a shell with a short lifespan).

Like the session state itself, service account initialization parameters are
sensitive, and it is the responsibility of the application to store them
securely.

At a network protocol level, OAuth2 service account sessions are implemented
using the OAuth2 authorization code flow.  This carries with it some additional
security concerns, discussed in
[RFC 6819 §4.4.4](https://datatracker.ietf.org/doc/html/rfc6819#section-4.4.4).
Because of these considerations, service accounts should only be used for
workflows that are independent of a controlling user.

As above, this may be done with state only persisted in memory, with state
shared with the CLI, or with state saved to application provided storage.

### OAuth2 M2M Client Registration
Service accounts are managed under the
**OAuth Clients** panel on the [Planet Insights Account](https://insights.planet.com/account/#/) page.

See [Sentinel Hub Authentication](https://docs.sentinel-hub.com/api/latest/api/overview/authentication/) for further information.

### Examples - OAuth2 Client Credentials Flow

#### In Memory Session State
```python linenums="1" title="Access APIs using a service account with in memory only state persistance"
{% include 'auth-session-management/app_managed_auth_state__in_memory__oauth_m2m.py' %}
```

#### Session State Shared with CLI
```python linenums="1" title="Access APIs using a service account with sessions persisted on disk and shared with the CLI"
{% include 'auth-session-management/app_managed_auth_state__on_disk_cli_shared__oauth_m2m.py' %}
```

####  Session State Saved to Application Storage
```python linenums="1" title="Access APIs using a service account with sessions persisted to application provided storage"
{% include 'auth-session-management/app_managed_auth_state__app_custom_storage__oauth_m2m.py' %}
```

----
