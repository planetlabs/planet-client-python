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
```shell title="Initialize session using planet CLI"
planet auth login
```

## Using Saved Session
Using a CLI managed session is the default behavior for SDK functions.
Developing an application that uses a CLI managed session requires no additional
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
This may be useful in cases where an application `my-application` wishes to
guide the user experience towards expecting CLI sessions and `my-application`
sessions to always be separate from the default CLI user session.

This may also be done to coordinate profiles with an
[application managed](../auth-dev-app-managed-oauth) session or with an
application that has been independently registered.

```python linenums="1" title="Use a specific session that is shared with the CLI"
{% include 'auth-session-management/cli_managed_auth_state__specific_auth_profile.py' %}
```
