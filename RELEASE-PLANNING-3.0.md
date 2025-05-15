# Planet Python Client 3.0 Release Planning

* Authentication changes:
  * Migrate to OAuth2 based authentication mechanisms, leveraging the
    [planet-auth-python](https://github.com/planetlabs/planet-auth-python)
    library for implementation.
  * Deprecate use of the legacy authentication protocol and handling of the
    user's password.
  * CLI changes to support changes in authentication practices.
  * Support for API keys supplied by the user is maintained, but users should
    be aware that there are currently no plans for sentinel-hub.com APIs to
    support Planet API keys.  The longer term roadmap is for all APIs to work
    with OAuth service accounts.
