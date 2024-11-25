---
title: Quick Start Guide
---


If you’re a Python developer, this Planet SDK for Python makes it easy to access Planet’s massive repository of satellite imagery and add Planet data to your data ops workflow.

If you’re not a Python developer, you can use the Command Line Interface (CLI) to get Planet data, and to process and analyze that data.

Take the following steps to install the SDK and connect with the Planet Server.

[TOC]

## Step 1: Install Python 3.9+ and a virtual environment

This is a Python package, so you’ll need to install Python (version 3.9 or greater), and set up and install a virtual environment.

Yes. Even if you’re not writing code—and only using the "no code" CLI part of the Planet SDK for Python—you’re using Python to communicate with the Planet Labs PBC servers. If you need help with Python install and setting up a virtual environment, read [Virtual Environments and the Planet SDK for Python](venv-tutorial.md).

## Step 2: Install the Planet SDK for Python

Install the Planet SDK for Python using [pip](https://pip.pypa.io):

```console
$ pip install planet
```

## Step 3: Check the Planet SDK for Python version

```console
$ planet --version
```

You should be on some version 2 of the Planet SDK for Python.

## Step 4: Sign on to your account

Planet SDK for Python, like the Planet APIs, requires an account for use.

### Have your Planet account username and password ready

To confirm your Planet account, or to get one if you don’t already have one, see [Get your Planet Account](get-your-planet-account.md).

### Authenticate with the Planet server

Just as you log in when you browse to https://account.planet.com, you’ll want to sign on to your account so you have access to your account and orders.

At a terminal console, type the following Planet command:

```console
$ planet auth init
```

You’ll be prompted for the email and password you use to access [your account](https://account.planet.com). When you type in your password, you won’t see any indication that the characters are being accepted. But when you hit enter, you’ll know that you’ve succeeded because you’ll see on the command line:

```console
Initialized
```

### Get your API key

Now that you’ve logged in, you can easily retrieve your API key that is being used for requests with the following command:

```console
planet auth value
```

Many `planet` calls you make require an API key. This is a very convenient way to quickly grab your API key.

#### Your API Key as an Environment Variable

You can also set the value of your API Key as an environment variable in your terminal at the command line:

```console
export PL_API_KEY=<your api key>
```

And you can see that the value was stored successfully as an environment variable with the following command:

```console
echo $PL_API_KEY
```

!!!note "The API Key environment variable is ignored by the CLI but used by the Python library"
    If you do create a `PL_API_KEY` environment variable, the CLI will be unaffected but the Planet library will use this as the source for authorization instead of the value stored in `planet auth init`.

## Step 5: Search for Planet Imagery

You’ve installed the environment, the SDK, and connected with the Planet server. You’re now ready to get your first bunch of data.

In this step, you search for the most recent PSScene images available to download and filter the list based on those images you actually have permissions to download.

### planet data filter

One of the commands you’ll use most frequently is `planet data filter`. This “convenience method” creates the JSON you need to run other commands. Run it with no arguments to see how it works by default:

```console
planet data filter --permission --std-quality
```

Look at the console output to see some default filters. `PermissionFilter` filters the output to only contain imagery that you have permission to download. You’ll also see `quality_category`, which means the output lists only images in the [`standard quality` category](https://developers.planet.com/docs/data/planetscope/#image-quality-standard-vs-test-imagery). Without these options, an empty filter is generated which would be used to disable filtering and simply return all results.

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

* Continue to explore the [No-Code CLI Guide](../cli/cli-guide.md).
* Start coding with the [Python SDK User Guide](../python/sdk-guide.md).
* Check out some of the [examples in our GitHub repo](https://github.com/planetlabs/planet-client-python/tree/main/examples).

## How to Get Help

As The Planet SDK (V2) is in active development, features & functionality will continue to be added.

If there's something you're missing or are stuck, the development team would love to hear from you.

  - To report a bug or suggest a feature, [raise an issue on GitHub](https://github.com/planetlabs/planet-client-python/issues/new)
  - To get in touch with the development team, email [developers@planet.com](mailto:developers@planet.com)
