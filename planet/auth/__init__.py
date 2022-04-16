"""
The Planet Authentication package

This package contains functionality for authenticating to the service
and managing authentication material.  This package knows nothing about
the service itself apart from how to interact with authentication APIs.

This package understands multiple authentication mechanisms, whose details
are encapsulated in implementation subclasses that implement the primary
(abstract) base class interfaces.  These primary interfaces are as follows:

- AuthClient & AuthClientConfig - Responsible for interacting with
      authentication services to obtain a credential that may be used for
      other API requests. Different clients have different configuration
      needs, so a configuration type exists for each client type to keep
      configuration on rails.
- Credential - Models just a credential. Responsible for reading and
      writing saved credentials to disk and performing basic data
      validation.  Knows nothing about how to get a credential, or how to
      use a credential.
- RequestAuthenticator - Responsible for decorating API requests with a
      credential.
"""
