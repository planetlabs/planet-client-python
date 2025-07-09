# Application Managed Sessions - Planet API Key

## Planet API Key Sessions
Legacy applications that need to continue to support Planet API keys may do so
until API keys are deprecated. This method should not be adopted for new
development if possible.

### Examples - Planet API Keys

#### In Memory Session State
Once provided with an API key, an application may operate with the API key
in memory indefinitely without the need to prompt the user for re-authentication.
```python linenums="1" title="Access APIs using Planet API keys in memory"
{% include 'auth-session-management/app_managed_auth_state__in_memory__api_key.py' %}
```

#### Version 2 Compatibility
The SDK continues to support files written by version 2 of the SDK to save
auth state.
```python linenums="1" title="Access APIs using Planet API keys using the on disk file format used by older versions of the SDK"
{% include 'auth-session-management/app_managed_auth_state__on_disk_legacy__api_key.py' %}
```

```json linenums="1" title="Legacy API Key file example"
{% include 'auth-session-management/legacy_api_key_file.json' %}
```

#### Session State Shared with CLI
```python linenums="1" title="Access APIs using Planet API keys with CLI managed shared state on disk"
{% include 'auth-session-management/app_managed_auth_state__on_disk_cli_shared__api_key.py' %}
```

####  Session State Saved to Application Storage

```python linenums="1" title="Access APIs using Planet API keys with sessions persisted to application provided storage"
{% include 'auth-session-management/app_managed_auth_state__app_custom_storage__api_key.py' %}
```

----
