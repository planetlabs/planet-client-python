# Overview
* Auth functions are now implemented by the `planet_auth` and
  `planet_auth_utils` libraries.
* The use of API keys and Planet's legacy username/password based
  authentication protocol is being phased out in favor of OAuth2 based
  mechanisms.  These legacy mechanisms remain in place for the time being,
  but clients are encouraged to start adopting OAuth2.

# Changes to the `planet auth` CLI command
* Deprecated:
  * The `planet auth init` command has been marked as deprecated, and will be
    removed in a future release.  The `planet auth init` command operates using
    Planet's proprietary username/password based authentication protocol and
    durable API keys.  This protocol will be phased out in favor of OAuth2.
    Use of durable API keys are discouraged in favor of time limited OAuth2
    access tokens.
  * The `planet auth store` command has been marked as deprecated, and will be
    removed in a future release.
  * The `planet auth value` command has been marked as deprecated, and will be
    removed in a future release.
* Replacements:
  * The `planet auth login` command should replace both `planet auth init` for
    initializing authentication for interactive CLI use, and `planet auth store`
    for initializing authentication for other use cases.  This command will
    store OAuth2 access and refresh tokens and perform any other necessary
    configuration.
  * The `planet auth print-access-token` command provides a similar function
  for obtaining current access tokens that can be used in scripted cases.
* Additions:
  * _Auth profiles_
    * Auth profiles are a new addition to the Planet Client SDK, and come from
      the underlying `planet_auth` library.  Profiles encapsulate a number of
      related auth concerns, and can be used to manage multiple client sessions
      with separate identities or underlying protocol configurations.
    * The Planet CLI provides a number of commands for manipulating profiles
      geared for Planet CLI users and use cases:
      * `planet auth profile-show`
      * `planet auth profile-list`
      * `planet auth profile-set`
  * `plauth` - The `planet_auth_utils` library provides a separate, lower level
    `plauth` command line utility for expert use cases.

# Library API changes
* TODO - Document

# On-disk interface changes
* TODO - Document

# Misc Notes
* The interfaces for the `planet_auth` and `planet_auth_utils` libraries are
  not currently considered to be as stable as the `planet` library.

# Release Sequencing & Requirements
* Planet APIs need to accept SH M2M tokens.
* Users/Admins need a good way to register/manage M2M clients.


# Branch TODO
- I think this bumps to version 3
- update API docs
- Update example docs
- Update new dev center docs
