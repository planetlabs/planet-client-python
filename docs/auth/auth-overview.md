# Client Authentication Overview

## Introduction
All calls to Planet APIs must be authenticated.  Only authorized clients may
use Planet Platform APIs.

For general information on how to authenticate to Planet APIs, please see
the [Authentication](https://docs.planet.com/develop/authentication/) section of Planet's platform documentation.
This documentation focuses on the use of the Planet Python SDK and
[`planet`](../../cli/cli-reference) CLI.

!!! info
    Work to unify authentication practices between `api.planet.com` and `services.sentinel-hub.com`
    is ongoing and being rolled out in phases over time. Documentation referring
    to work in progress is marked as such 🚧.

    Of particular note is the general shift towards OAuth2 based authentication,
    and a corresponding move away from Planet API keys.

----

## Authentication Protocols
At the HTTP protocol level underneath the SDK, there are several distinct
ways a client may authenticate to the Planet APIs, depending on the use case.
See [Authentication Protocols](https://docs.planet.com/develop/authentication/#authentication-protocols) for a
complete discussion of when to choose a particular method.

* **OAuth2 user access tokens** - API access as the end-user, using OAuth2
    user access tokens.  This is the preferred way for user-interactive
    applications to authenticate to Planet APIs.  A registered client application
    and a web browser are required to initialize a session. A web browser is not
    required for continued operation.  The SDK itself is a registered
    client application that may be used for this purpose.

    Examples of applications that fall into this category include
    [ArcGIS Pro](https://www.esri.com/en-us/arcgis/products/arcgis-pro/overview),
    [QGIS](https://qgis.org/), and the SDK's own [`planet`](../../cli/cli-reference)
    CLI program.  All Planet first-party web applications also use this method.

* **OAuth2 M2M access tokens** (🚧 _Work in progress_) - API access as a service user, using OAuth2
    M2M access tokens.  This is the new preferred way for automated processes
    to authenticate to Planet APIs that must operate without a human user.
    No web browser is required, but this method carries some additional
    security considerations.

* **Planet API keys** (⚠️ _Pending future deprecation_) - API access as a Planet end-user using a simple
    fixed string bearer key.  This is the method that has historically been
    documented and recommended for developers using Planet APIs.

### OAuth2
OAuth2 authentication requires that the client possess an access token
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
user-interactive and machine-to-machine use cases, as described in this guide.

**SDK Examples:**

* **OAuth2 user access tokens**
    * [Using the CLI (Quick start)](../auth-dev-cli-managed/#planet-auth-login-planet-user)
    * [Forcing use of SDK Built-in Application ID in code (Quick start)](../auth-dev-cli-managed/#use-cli-session-force-builtin)
    * [Using a custom registered application ID](../auth-dev-app-managed-oauth/#oauth2-session-for-users)
* **OAuth2 M2M access tokens**
    * [Using the CLI (Quick start)](../auth-dev-cli-managed/#planet-auth-login-planet-m2m)
    * [Using a M2M Access Token in code](../auth-dev-app-managed-oauth/#oauth2-session-for-service-accounts)

!!! info
    OAuth2 user access tokens currently work for all Planet APIs under both
    the `api.planet.com` and `services.sentinel-hub.com` domains.

    🚧 OAuth2 machine-to-machine (M2M) access tokens are currently available for use
    with `services.sentinel-hub.com` APIs. Work to support `api.planet.com` is
    ongoing.  It should also be noted that at this time no API clients for
    `services.sentinel-hub.com` APIs have been incorporated into this SDK.
    The SDK may still be used to obtain and manage M2M access tokens to
    support external applications.

### Planet API Keys
Planet API keys are simple fixed strings that may be presented by the client
to API services to assert the client's right to access APIs.  API keys are
obtained by the user from their [Account](https://www.planet.com/account) page
under the [_My Settings_](https://www.planet.com/account/#/user-settings) tab.

**SDK Examples:**

* **Planet API keys**
     * [Using the CLI (Quick start)](../auth-dev-cli-managed/#planet-auth-login-planet-apikey)
     * [Using a Planet API Key in code](../auth-dev-app-managed-apikey)


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

## Resources
More information regarding Authentication to Planet APIs, OAuth2, and JWTs
may be found here:

* [Planet Authentication](https://docs.planet.com/develop/authentication/)
* [RFC 6749 - The OAuth 2.0 Authorization Framework](https://datatracker.ietf.org/doc/html/rfc6749)
* [RFC 8628 - OAuth 2.0 Device Authorization Grant](https://datatracker.ietf.org/doc/html/rfc8628)
* [RFC 7519 - JSON Web Token (JWT)](https://datatracker.ietf.org/doc/html/rfc7519)
* [RFC 9068 - JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens](https://datatracker.ietf.org/doc/html/rfc9068)
* [RFC 6819 - OAuth 2.0 Threat Model and Security Considerations](https://datatracker.ietf.org/doc/html/rfc6819)

----
