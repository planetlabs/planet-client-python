---
title: Resources
---

## Examples

### SDK examples

The following examples were created specifically to show you how to use the SDK and CLI:

* [data_download_multiple_assets.py](https://github.com/planetlabs/planet-client-python/blob/main/examples/data_download_multiple_assets.py) - this Python script orders, activates, and downloads two assets
* [orders_create_and_download_multiple_orders.py](https://github.com/planetlabs/planet-client-python/blob/main/examples/orders_create_and_download_multiple_orders.py) - this Python script creates two orders, each with unique Area of Interest (AoI), preventing a combined download
* [Planet API Python Client](https://github.com/planetlabs/notebooks/blob/master/jupyter-notebooks/data-api-tutorials/planet_python_client_introduction.ipynb) - a Python notebook to introduce Planet’s Data API and the `planet` module
* [Orders API & Planet SDK](https://github.com/planetlabs/notebooks/blob/665f165e59f2c3584976ad2dde569c649e631c0b/jupyter-notebooks/orders_api_tutorials/Planet_SDK_Orders_demo.ipynb) - a Python notebook shows how to get started with Planet SDK and the Orders API.
* [Analysis Ready Data Tutorial Part 1: Introduction and Best Practices](https://github.com/planetlabs/notebooks/blob/6cc220ff6db246353af4798be219ee1fe7e858b0/jupyter-notebooks/analysis-ready-data/ard_1_intro_and_best_practices.ipynb) - this Python notebook uses the SDK to prepare Analysis Ready Data.
* [Analysis Ready Data Tutorial Part 2](https://github.com/planetlabs/notebooks/blob/6cc220ff6db246353af4798be219ee1fe7e858b0/jupyter-notebooks/analysis-ready-data/ard_2_use_case_1.ipynb) - the first use case in this Python notebook leverages the SDK’s `order_request` feature to prepare an NDVI time stack and the second use case visualizes the NDVI imagery.

### Other examples

Besides the SDK-specific examples, above, you can find many examples that show how to access Planet data in the documentation and Planet School at the [Planet Developers Center](https://developers.planet.com).Also, more working examples are on the [Planet Labs Python notebooks](https://github.com/planetlabs/notebooks) on GitHub.

## Planet APIs

This pre-release SDK has implemented interfaces for several Planet APIs. Check out the documentation for the underlying API:

* [Data](https://developers.planet.com/docs/apis/data/)
* [Orders](https://developers.planet.com/apis/orders/)
* [Subscriptions](https://developers.planet.com/docs/subscriptions/)

## Email Developer Relations

We are eager to share this pre-release with you and encourage you to test your workflows rigorously. Based on your feedback, we may roll out additional updates to improve your experience. Besides joining the discussion, and filing issues and pull requests here, feel free to share your general feedback with us at developers@planet.com.
## Contribute to this open source project

To contribute or develop with this library, see
[CONTRIBUTING](https://github.com/planetlabs/planet-client-python/blob/main/CONTRIBUTING.md).

## Build Status

[Planet Software Development Kit (SDK) for Python main branch](https://github.com/planetlabs/planet-client-python)

[![Build Status](https://github.com/planetlabs/planet-client-python/actions/workflows/test.yml/badge.svg)](https://github.com/planetlabs/planet-client-python/actions/workflows/test.yml)

## Version 1 of this SDK

[Version 1 of this SDK](https://github.com/planetlabs/planet-client-python/tree/1.5.2) is significantly different (see the [documentation](https://planet-sdk-for-python.readthedocs.io/en/latest/)). Version 2 is not backward compatible. Make sure to create a separate virtual environment if you need to work with both versions. For more information on how to do this, see the [Virtual Environments and the Planet SDK for Python](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/get-started/venv-tutorial/).
