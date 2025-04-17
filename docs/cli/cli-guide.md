---
title: No-Code CLI User Guide
---

## About

This is the complete guide to using the command-line interface (CLI) to Planet’s
APIs. It’s divided up into a number of sections, so you can jump right into 
the examples for an API you’re interested in. If you’re new to CLI’s it should
provide all the information you need to work more directly with Planet’s API’s.

## CLI Guide Overview

* **[CLI Introduction](cli-intro.md)** provides an introduction to using a
CLI and highlights some of the key concepts and tools that work with Planet’s CLI.
If you’re already comfortable with CLI tools you can safely skip this section.
* **[CLI for Data API](cli-data.md)** explores the `planet data` commands with 
extensive examples.
* **[CLI for Orders API](cli-orders.md)** dives into the `planet orders` commands
with numerous samples to get you started.
* **[CLI for Subscriptions API](cli-subscriptions.md)** - explains the `planet subscriptions` commands
* **[CLI Tips & Tricks](cli-tips-tricks.md)** highlights a number of interesting 
geospatial CLI command-line tools and shows you how to use them in conjunction
with Planet’s tools.

## Step 1: Install Python 3.9+ and a virtual environment

This is a Python package, so you’ll need to install Python (version 3.9 or greater), and set up and install a virtual environment.

Yes. Even if you’re not writing code—and only using the "no code" CLI part of the Planet SDK for Python—you’re using Python to communicate with the Planet Labs PBC servers. If you need help with Python install and setting up a virtual environment, read [Virtual Environments and the Planet SDK for Python](../get-started/venv-tutorial.md).

## Step 2: Install the Planet SDK for Python

Install the Planet SDK for Python using [pip](https://pip.pypa.io):

```console
pip install planet
```

## Step 3: Check the Planet SDK for Python version

```console
planet --version
```

You should be on some version 2 of the Planet SDK for Python.

## Step 4: Sign on to your account

Planet SDK for Python, like the Planet APIs, requires an account for use.

### Have your Planet account username and password ready

To confirm your Planet account, or to get one if you don’t already have one, see [Get your Planet Account](../get-started/get-your-planet-account.md).

### Authenticate with the Planet server

Just as you log in when you browse to https://planet.com/account, you’ll want to sign on to your account so you have access to your account and orders.

At a terminal console, type the following Planet command:

```console
planet auth login
```

A browser window should be opened, and you will be directed to login to your account.  This
command will wait for the browser login to complete, and should exit shortly afterwards.
When this process succeeds, you will see the following message on the console:

```console
Login succeeded.
```

If you are in an environment where the `planet` command line utility cannot open a browser (such 
as a remote shell on a cloud service provider), use the following command and follow the instructions:
```console
planet auth login --no-open-browser
```

### Get your Access Token

Now that you’ve logged in, you can easily retrieve an Access Token that is being used for requests with the following command:

```console
planet auth print-access-token
```

Many `planet` calls you make require an access token. This is a very convenient way to quickly grab the current access token.

**Note** : As a security measure, access tokens are time limited. They have a relatively short lifespan, and must
be refreshed.  The `print-access-token` command takes care of this transparently for the user.

## Step 5: Search for Planet Imagery

You’ve installed the environment, the SDK, and connected with the Planet server. You’re now ready to get your first bunch of data.

In this step, you search for the most recent PSScene images available to download and filter the list based on those images you actually have permissions to download.

### planet data filter

One of the commands you’ll use most frequently is `planet data filter`. This “convenience method” creates the JSON you need to run other commands. Run it with no arguments to see how it works by default:

```console
planet data filter --permission --std-quality
```

Look at the console output to see some default filters. `PermissionFilter` filters the output to only contain imagery that you have permission to download. You’ll also see `quality_category`, which means the output lists only images in the [`standard quality` category](https://docs.planet.com/data/imagery/planetscope/#standard-versus-test-imagery). Without these options, an empty filter is generated which would be used to disable filtering and simply return all results.

!!!note "The --help switch is your friend"
    You can do a lot with this `filter` command. We recommend running `planet data filter --help` often to get a reference of how the commands work.

### planet data search

Run the filter command and save it to a file named `filter.json`:

```console
planet data filter --permission --std-quality > filter.json
```

Then use that file with the search command and save the results to another file named `recent-psscene.json`.

```console
planet data search PSScene --filter filter.json > recent-psscene.json
```

Open `recent-psscene.json` to see the 100 most recent PSScene images you have permissions to actually download.

## Next steps

Now that you have the quick setup for the Planet SDK for Python, you have a few options:

* Continue to explore the [No-Code CLI Guide](#cli-guide-overview).
* Start coding with the [Python SDK User Guide](../python/sdk-guide.md).
* Check out some of the [examples in our GitHub repo](https://github.com/planetlabs/planet-client-python/tree/main/examples).

## How to Get Help

As The Planet SDK (V2) is in active development, features & functionality will continue to be added.

If there's something you're missing or are stuck, the development team would love to hear from you.

  - To report a bug or suggest a feature, [raise an issue on GitHub](https://github.com/planetlabs/planet-client-python/issues/new)
  - To get in touch with the development team, email [developers@planet.com](mailto:developers@planet.com)
