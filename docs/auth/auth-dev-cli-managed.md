# CLI Managed Sessions
For simple programs and scripts, it is easiest for the program to defer
session management to the [`planet auth`](../../cli/cli-reference/#auth)
CLI.   This method will store session information in the user's home directory
in the `~/.planet.json` file and `~/.planet/` directory.  The Python SDK will
use the information saved in these locations to make API calls.

When this approach is taken, the authentication session will be shared between
actions taken by the `planet` utility and those taken by programs built
using the SDK.  Changes made by one will impact the behavior of the other.

CLI managed sessions can be used for all authentication protocols supported
by the SDK library.

**Requirements and Limitations:**

* The program must have read and write access to the user's home directory.
* This method requires that the end-user has access to and understands
  the [`planet`](../../cli/cli-reference) CLI command needed to manage
  authentication.
* This approach should not be used on public terminals or in cases where the
  user's home directory cannot be kept confidential.

## Initialize Session - CLI Login
Session login can be performed using the following command.  This command can
be used to initialize sessions using any of the supported authentication methods,
and will default to creating an OAuth2 user session.
Refer to the command's `--help` for more information.

<a name="planet-auth-login"></a>
```shell title="Initialize session using planet CLI."
planet auth login
```

A particular configuration may be selected by using the `--auth-profile` option.
`planet-user` is the default, but may be [overridden](../auth-sdk/#configuration)
by the runtime environment.

<a name="planet-auth-login-planet-user"></a>
```shell title="Initialize session using planet CLI, forcing the built-in user interactive OAuth2 login flow."
planet auth login --auth-profile planet-user
```

<a name="planet-auth-login-planet-m2m"></a>
```shell title="Initialize session using planet CLI, forcing the use of the specified service principal."
planet auth login --auth-client-id <your-client-id> --auth-client-secret <your-client-secret>
```

<a name="planet-auth-login-planet-apikey"></a>
```shell title="Initialize session using planet CLI, forcing the use of a legacy Planet API key."
planet auth login --auth-api-key <your-api-key>
```

## Using Saved Session
Using a CLI managed session is the default behavior for SDK functions.
Developing an application that uses a CLI managed session requires no additional
action by the developer.  When a developer chooses to create an application
that behaves in this way, it will most often be done implicitly by relying
on SDK default behavior, but it may also be done explicitly.

### CLI Selected Session
The default behavior of the SDK is to defer which session is loaded to CLI.

<a name="use-cli-session-implicit"></a>
```python linenums="1" title="Implicitly use CLI managed login sessions, deferring session selection to the user and the CLI."
{% include 'auth-session-management/cli_managed_auth_state__implicit.py' %}
```
<a name="use-cli-session-explicit"></a>
```python linenums="1" title="Explicitly use CLI managed login sessions, deferring session selection to the user and the CLI."
{% include 'auth-session-management/cli_managed_auth_state__explicit.py' %}
```

### Application Selected Session
Applications may be developed to always select a specific CLI managed profile.
This may be useful in cases where an application wishes to guide the user
experience towards expecting an auth session that is separate from the default
sessions used by the CLI.

In cases where the application has access to the
user's home directory and saved sessions, forcing the use of a particular
profile circumvents the user's CLI managed preferences.

<a name="use-cli-session-force-custom"></a>
Note: This first example does not create the session `my-app-profile`.
This must be created either through a separate code path as show in
the [Application Managed Sessions](../auth-dev-app-managed-oauth) guide,
or by using a CLI command to copy an existing profile such as
`planet auth profile copy planet-user my-app-profile`.

```python linenums="1" title="Use a specific session that is shared with the CLI."
{% include 'auth-session-management/cli_managed_auth_state__specific_auth_profile.py' %}
```

<a name="use-cli-session-force-builtin"></a>
It is also possible to force the use of the SDK's built-in OAuth2 application ID
for interactive user applications.  This capability is provided for developer
convenience, primarily for smaller programs and scripts. Larger applications
developed for multiple users should
[register](../auth-dev-app-managed-oauth/#oauth2-user-client-registration)
a unique application ID.

This second example also initiates a login and does not save session state to storage.
This means this example does not depend on the CLI, and may be considered a simple
example of an [Application Managed Session](../auth-dev-app-managed-oauth).

```python linenums="1" title="Use the Planet SDK with an OAuth2 user session initialized by the application and utilizing the SDK's built-in OAuth2 application ID."
{% include 'auth-session-management/app_managed_auth_state__using_sdk_app_id.py' %}
```

---
