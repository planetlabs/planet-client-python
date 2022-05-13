# User Guide

## API
### Session

Communication with the Planet services is provided with the `Session` class.
The recommended way to use a `Session` is as a context manager. This will
provide for automatic clean up of connections when the context is left.

```python
>>> import asyncio
>>> import os
>>> from planet import Session
>>>
>>> async def main():
...     async with Session() as sess:
...         # perform operations here
...         pass
...
>>> asyncio.run(main())

```

Alternatively, use `await Session.aclose()` to close a `Session` explicitly:

```python
>>> async def main():
...     sess = Session()
...     # perform operations here
...     await sess.aclose()
...
>>> asyncio.run(main())

```

### Authentication

#### Authentication Overview

There are two steps to managing authentication information, obtaining the
authentication information from Planet and then managing it for local retrieval
for service authentication purposes.

The recommended method for obtaining authentication information is to
log in using the `login()` method on an instance of `AuthClient`. 
Different implementations of `AuthClient` exist to support different use cases.
The specific steps that will be followed depends on the configuration of the auth
system, which may vary depending on the type of application under development.

Once the authentication information is obtained, the most convenient way of
managing it for local use is to write it to a secret file using `Credential.save()`.

The `Auth` class exists to manage the different components of the auth system,
encapsulating the orchestration of the different classes needed to initialize,
save, and use service access credentials that may be obtained using a variety
of mechanisms.  The Auth class manages different configurations using profiles
to manage on disk locations of configuration and credential files.  This 
use of profiles also allows for the CLI find and manage credentials that may be used
by other applications built on top of the Planet SDK library.

For example, to obtain and store authentication information using the library:

```python
>>> from planet.auth import Auth
>>> my_auth_system = Auth.initialize()
>>> my_credential = my_auth_system.auth_client().login()
>>> my_credential.set_path(my_auth_system.token_file_path())
>>> my_credential.save()
```

The same thing may be accomplished outside your application using Planet's 
CLI tool:

```shell
planet auth login
```

Both of these will result in credentials being saved in a `~/.planet/`
in your home directory that will be understood by subsequent initializations
of the `Auth` system without calling `AuthClient.login()`.

When a `Session` is created, authentication is read from the secret
file created with `Credential.save()`. By default, sessions will use the default
auth profile used by Planet's CLI. This behavior can be modified by passing
in an already initialized Auth object.  Session assumes the selected
auth profile has already been initialized by a call `AuthClient.login()` and 
`Credential.save()`.

```python
>>> import asyncio
>>> from planet import Session
>>> from planet.auth import Auth
>>> 
>>> my_auth = Auth.initialize(profile="my_profile_name")
>>> async def main():
...     async with Session(auth=my_auth) as sess:
...         # perform operations here
...         pass
...
>>> asyncio.run(main())

```

#### Authentication Profiles
Authentication profiles are used to configure how the library interacts
with authentication services, as well as how the credentials obtained from
authentication services are subsequently used by the rest of the SDK to
talk to Planet services.  Different profile configurations have different
login requirements and different downstream behavior characteristics that
must be accommodated.

In their most basic form, a profile is defined by creating a profile 
directory on disk under the `~/.planet/` directory in the user's home
directory. The directory name is used as the profile identifier in all
other operations. Profile names and directories are expected to be all
lower case.

Within the profile directory, the following files are defined:

* `auth_client.json` - This file controls how the `Auth` system is
   bootstrapped by `Auth.initialize()`.  It is here that application
   specific client information may be configured.  Depending on the
   client application type, this file may contain sensitive information.
* `token.json`- This is the file that will store the `Credential` that
   that is returned from a successful login. This credential will then be used
   to authorize subsequent calls to pther Planet APIs.  Depending on the
   profile configuration, this credential may be long-lived, or may be periodically
   refreshed.

##### Built in Profiles
The following profiles are built into the SDK, and will be understood
without the user creating a corresponding profile directory:

* **default**: Configures the SDK to use the built-in client profile that
  uses OAuth based authentication mechanisms to access Planet services on
  behalf of the user. OAuth features short-lived access tokens and user
  controlled scoped access to their account for improved security.
* **legacy**: Configure the SDK to use Planet API keys to access
  Planet services on behalf of the user.  Planet API keys are sensitive
  long-lived keys that provide full access to the user's account.
  The use of OAuth based mechanisms is considered more secure, and should
  be preferred where possible.

##### User Defined Profiles
*TODO:* We need links to appropriate platform documentation on how to
create applicaiton ID, manage grants, and what these scope things are
at an API level.

*TODO:* We need to document how to configure auth profiles of the various
types: Planet Legacy, OAuth PKCE, OAuth Client Credentials, etc.

**PKCE OAuth Client Configuration:**
```json
{
    "client_type": "oidc_auth_code",
    "auth_server": "FIXME",
    "client_id": "__YOUR_CLIENT_ID_HERE__",
    "redirect_uri": "__YOUR_CLIENT_REDIRECT_URI_HERE__",
    "local_redirect_uri": "__YOUR_CLIENT_REDIRECT_URI_HERE__",
    "default_request_scopes": ["planet",
                               "planet.admin",
                               "planet.admin:read",
                               "planet.admin:write",
                               "planet.tasking",
                               "planet.tasking:read",
                               "planet.tasking:write",
                               "planet.platform",
                               "planet.platform:read",
                               "planet.platform:write",
                               "offline_access",
                               "openid",
                               "profile"]
}
```

**Client Secret Client Credentials Client Configuration:**
```json
{
    "client_type": "oidc_client_credentials_secret",
    "auth_server": "FIXME",
    "client_id": "__YOUR_CLIENT_ID_HERE__",
    "client_secret": "__YOUR_CLIENT_SECRET__",
    "default_request_scopes": ["planet"]
}
```

**Public Key Client Credentials Client Configuration:**
```json
{
    "client_type": "oidc_client_credentials_pubkey",
    "auth_server": "FIXME",
    "client_id": "__YOUR_CLIENT_ID_HERE__",
    "client_privkey": "-----BEGIN RSA PRIVATE KEY-----\n__YOUR_PRIVATE_KEY_HERE__\n-----END RSA PRIVATE KEY-----",
    "client_privkey_file": "/path/to/private/key.pem",
    "client_privkey_password": "__PASSWORD_FOR_PRIVATEKEY__",
    "default_request_scopes": ["planet"]
}
```
Only one of `private_key` or `private_key_file` is required.

**Planet Legacy API Key Client Configuration**:
```json
{
    "client_type": "planet_legacy",
    "legacy_auth_endpoint": "https://api.planet.com/v0/auth/login"
}
```
### Orders Client

The Orders Client mostly mirrors the
[Orders API](https://developers.planet.com/docs/orders/reference/#tag/Orders),
with the only difference being the addition of the ability to poll for when an
order is completed and to download an entire order.

```python
>>> from planet import OrdersClient
>>>
>>> async def main():
...     async with Session() as sess:
...         client = OrdersClient(sess)
...         # perform operations here
...
>>> asyncio.run(main())

```

#### Creating an Order

When creating an order, the order request details must be provided to the API
as a JSON blob. This JSON blob can be built up manually or by using the
`build_request` function.

An example of creating the request JSON with `build_request`:

```python
>>> from planet import order_request
>>> products = [
...     order_request.product(['20170614_113217_3163208_RapidEye-5'],
...                           'analytic', 'REOrthoTile')
... ]
...
>>> tools = [
...     order_request.toar_tool(scale_factor=10000),
...     order_request.reproject_tool(projection='WSG84', kernel='cubic'),
...     order_request.tile_tool(1232, origin_x=-180, origin_y=-90,
...               pixel_size=0.000027056277056,
...               name_template='C1232_30_30_{tilex:04d}_{tiley:04d}')
... ]
...
>>> request = order_request.build_request(
...     'test_order', products=products, tools=tools)
...

```

The same thing, expressed as a `JSON` blob:

```python
>>> request = {
...   "name": "test_order",
...   "products": [
...     {
...       "item_ids": [
...         "20170614_113217_3163208_RapidEye-5"
...       ],
...       "item_type": "REOrthoTile",
...       "product_bundle": "analytic"
...     }
...   ],
...   "tools": [
...     {
...       "toar": {
...         "scale_factor": 10000
...       }
...     },
...     {
...       "reproject": {
...         "projection": "WSG84",
...         "kernel": "cubic"
...       }
...     },
...     {
...       "tile": {
...         "tile_size": 1232,
...         "origin_x": -180,
...         "origin_y": -90,
...         "pixel_size": 2.7056277056e-05,
...         "name_template": "C1232_30_30_{tilex:04d}_{tiley:04d}"
...       }
...     }
...   ]
... }

```

Once the order request is built up, creating an order is done within
the context of a `Session` with the `OrdersClient`:

```python
>>> async def main():
...     async with Session() as sess:
...         cl = OrdersClient(sess)
...         order = await cl.create_order(request)
...
>>> asyncio.run(main())

```

#### Polling and Downloading an Order

Once an order is created, the Orders API takes some time to create the order
and thus we must wait a while before downloading the order.
We can use polling to watch the order creation process and find out when the
order is created successfully and ready to download.

With polling and download, it is often desired to track progress as these
processes can take a long time. Therefore, in this example, we use a progress
bar from the `reporting` module to report poll status. `download_order` has
reporting built in.

```python
from planet import reporting

>>> async def create_poll_and_download():
...     async with Session() as sess:
...         cl = OrdersClient(sess)
...         with reporting.StateBar(state='creating') as bar:
...             # create order
...             order = await cl.create_order(request)
...             bar.update(state='created', order_id=order['id'])
...
...             # poll
...             await cl.wait(order['id'], callback=bar.update_state)
...
...         # download
...         await cl.download_order(order['id'])
...
>>> asyncio.run(create_poll_and_download())
```

## CLI

### Authentication

The `auth` command allows the CLI to authenticate with Planet servers. Before
any other command is run, the CLI authentication should be initiated with

```console
$ planet auth init
```

To store the authentication information in an environment variable, e.g.
for passing into a Docker instance:

```console
$ export PL_API_KEY=$(planet auth value)
```

### Orders API

Most `orders` cli commands are simple wrappers around the
[Planet Orders API](https://developers.planet.com/docs/orders/reference/#tag/Orders)
commands.


#### Create Order File Inputs

Creating an order supports JSON files as inputs and these need to follow certain
formats.


##### --cloudconfig
The file given with the `--cloudconfig` option should contain JSON that follows
the options and format given in
[Delivery to Cloud Storage](https://developers.planet.com/docs/orders/delivery/#delivery-to-cloud-storage).

An example would be:

Example: `cloudconfig.json`
```
{
    "amazon_s3": {
        "aws_access_key_id": "aws_access_key_id",
        "aws_secret_access_key": "aws_secret_access_key",
        "bucket": "bucket",
        "aws_region": "aws_region"
    },
    "archive_type": "zip"
}
```

##### --clip
The file given with the `--clip` option should contain valid [GeoJSON](https://geojson.org/).
It can be a Polygon geometry, a Feature, or a FeatureClass. If it is a FeatureClass,
only the first Feature is used for the clip geometry.

Example: `aoi.geojson`
```
{
    "type": "Polygon",
    "coordinates": [
        [
            [
                37.791595458984375,
                14.84923123791421
            ],
            [
                37.90214538574219,
                14.84923123791421
            ],
            [
                37.90214538574219,
                14.945448293647944
            ],
            [
                37.791595458984375,
                14.945448293647944
            ],
            [
                37.791595458984375,
                14.84923123791421
            ]
        ]
    ]
}
```

##### --tools
The file given with the `--tools` option should contain JSON that follows the
format for a toolchain, the "tools" section of an order. The toolchain options
and format are given in
[Creating Toolchains](https://developers.planet.com/docs/orders/tools-toolchains/#creating-toolchains).

Example: `tools.json`
```
[
    {
        "toar": {
            "scale_factor": 10000
        }
    },
    {
        "reproject": {
            "projection": "WGS84",
            "kernel": "cubic"
        }
    },
    {
        "tile": {
            "tile_size": 1232,
            "origin_x": -180,
            "origin_y": -90,
            "pixel_size": 2.7056277056e-05,
            "name_template": "C1232_30_30_{tilex:04d}_{tiley:04d}"
        }
    }
]
```

