---
title: Upgrading from V1 to V2
---

The Planet SDK for Python is Version 2 of what was previously referred to as
the Planet API client. 

Version 2 is essentially a complete rewrite and brings with it big changes to
the Python library.

In Version 1, a single client was created for all APIs,
`client=api.ClientV1(api_key=API_KEY)`. With this client, all commumication was
synchronous. Asynchronous bulk support was provided with the `downloader`
module. There was no built-in support for polling when an order was
ready to download or tracking when an order was downloaded.

In Version 2, a `Session` is used to manage all communication with the Planet
APIs. This provides for multiple asynchronous connections. An API-specific
client is created. This client manages polling and downloading, along with
any other capabilities provided by the API.
