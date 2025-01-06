---
title: Python SDK Quick Start
---

The Planet SDK for Python makes it easy to access Planet’s massive repository of satellite imagery and add Planet
data to your data ops workflow.

**Note:** This is the new, non-asyncio client. If you want to take advantage of asyncio, see the [async client guide](../python/async-sdk-guide.md). For the no-code CLI client, see the [CLI guide](../cli/cli-guide.md).

Your feedback on this version of our client is appreciated. Please raise an issue on [GitHub](https://github.com/planetlabs/planet-client-python/issues) if you encounter any problems.

## Dependencies

This package requires [Python 3.9 or greater](https://python.org/downloads/). A virtual environment is strongly recommended.

You will need your Planet API credentials. You can find your API key in [Planet Explorer](https://planet.com/explorer) under Account Settings.

## Installation

Install from PyPI using pip:

```bash
pip install planet
```

## Usage

### Authentication

Use the `PL_API_KEY` environment variable to authenticate with the Planet API. For other authentication options, see the [SDK guide](../python/sdk-guide.md).

```bash
export PL_API_KEY=your_api_key
```

### The Planet client

The `Planet` class is the main entry point for the Planet SDK. It provides access to the various APIs available on the Planet platform.

```python
from planet import Planet
pl = Planet()  # automatically detects PL_API_KEY
```

The Planet client has members `data`, `orders`, and `subscriptions`, which allow you to interact with the Data API, Orders API, and Subscriptions API. Usage examples for searching, ordering and creating subscriptions can be found in the [SDK guide](../python/sdk-guide.md).

## How to Get Help

As The Planet SDK (V2) is in active development, features & functionality will continue to be added.

If there's something you're missing or are stuck, the development team would love to hear from you.

  - To report a bug or suggest a feature, [raise an issue on GitHub](https://github.com/planetlabs/planet-client-python/issues/new)
  - To get in touch with the development team, email [developers@planet.com](mailto:developers@planet.com)
