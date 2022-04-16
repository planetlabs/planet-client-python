"""
Package providing an OAuth2/OIDC implementation of the planet.auth package
interfaces.  This is a generic OAuth2/OIDC auth client, and knows nothing
about Planet APIs.

AuthClients are provided for a number of authentication flows, suitable
for user interactive or headless use cases.

Several Request Authenticators are provided that can use the OIDC credentials
obtained from an AuthClient.  Since frequent credential refresh is a part of
using OAuth2/OIDC, these authenticators handle this transparently.
"""
