---
title: Virtual Environments and the Planet SDK for Python
---

This tutorial is aimed at Planet SDK for Python users who have little or no experience with virtual environments, especially those who want to be early users of v2 of the Planet SDK for Python (and still use v1 while evaluating v2).

A virtual environment is a space you create to pull in the resources you need for a specific project. In Python, virtual environments are used to install tools that work well together in their own isolated area. While you may have Python installed already, this overview focuses on installing a version of Python in a way that ensures you have the right virtual environment for using this Planet SDK. 

Using the default Python installation without a virtual environment is not recommended, because it’s so easy to get a combination of tools installed that don’t work well with each other. The great thing about installing a virtual environment is that if you get a combination of tools that don’t work well together, you can “throw away” that virtual environment and create a new one with a few lines in the terminal.

So while it may feel inconvenient at first, spinning up virtual environments will be your go-to setup step for trying out a new idea, testing a routine, or repeating a process at scale.

## Conda vs venv

There are two main options in the Python world for virtual environments:

* [venv](https://docs.python.org/3/library/venv.html)
* [Conda](https://conda.io)

Both are great options. venv is built into Python (version 3.3 and above), so if you’ve got Python
then it’s already there. Conda does a bit ‘more,’ as venv just works for Python, while Conda
creates virtual environments for all libraries and languages (but was designed for Python). We
recommend venv, as [GDAL](https://gdal.org/), arguably the most useful geospatial command-lines,
can sometimes be a pain with Conda. And our releases are not (yet) targeting Conda packaging.

## venv prerequisites

The main prerequisite for venv is that you have Python 3.3 and above. To check your Python
version type:

```console
 $ python --version
```

 If you installed on Windows or Linux you most likely have Python 3. Mac OS ships by default with
 Python 2, so you’ll need to install Python 3. 

### Installing Python 3 on a Mac

 Our recommended route is to install [homebrew](https://brew.sh/). To do that you just run the 
 following on your command-line:

```console
 $ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After it download and installs you just run:

```console
 $ brew install python
```

That will set up a command called `python3` that you can use to call Python 3.

## Setting your virtual environments

It’s good to read up on how venv works, we recommend 
[this tutorial](https://www.dataquest.io/blog/a-complete-guide-to-python-virtual-environments/)
to get a solid understanding.

To be able to work with both the v1 stable and v2 pre-release we recommend setting up 2 virtual environments. A good place to put them is in a .venv directory. The following commands creates a `.venv` directory at your root, user home directory and then switches into that new directory.

```console
 $ mkdir ~/.venv
 $ cd ~/.venv
```

Then you’ll want to create a venv for v1 and v2.

### Install a virtual environment for version 1 of the SDK

#### Install and activate version 1

First create the v1 virtual environment with:

```console
  $ python3 -m venv ~/.venv/planet-v1
```

Then activate the virtual environment. On a Mac or Linux with, you can do so with the following command:

```console
 $ source ~/.venv/planet-v1/bin/activate
```

Or, on Windows with:

```console
  $ planet-v1\Scripts\activate.bat
```

If you haven’t installed version 1, you can do so with:

```console
  $ pip install planet
```

If you already have v1 of the Planet SDK installed, you can check to see if it’s recognized in your new virtual environment by making a command call to get the version number.

Check the version again to confirm it was installed:

```console
 $ planet --version
```

You should see a number that begins with 1.

!!!note "If a version 1 doesn’t appear"
    If you don’t see a version 1 number, then you may need to adjust your path. If you have trouble getting the version for the Planet SDK v1 that you know you’ve installed, feel free to [discuss with us](https://github.com/planetlabs/planet-client-python/discussions). We can troubleshoot together and then update the steps here.

#### Deactivate version 1

As we mentioned, the point to creating virtual environments is to have a place to install the right packages together. This virtual environment is for version 1 of the SDK. For version 2, we’ll need to set up a separate virtual environment. To do so, we must first deactivate the version 1 virtual environment.

Deactivate the virtual environment you’ve activated with a call to `deactivate`:

```console
 $ deactivate
```

This call takes you out of the virtual environment, back to only your base install.

### Install a virtual environment for version 2 of the SDK

#### Install and activate version 2

Set up a virtual environment for version 2 with the following command line Python call:

```console
 $ python3 -m venv ~/.venv/planet-v2
```

Then activate the virtual environment. On a Mac or Linux with, you can do so with the following command:

```console
 $ source ~/.venv/planet-v2/bin/activate
```

Or, on Windows with:

```console
  $ planet-v2\Scripts\activate.bat
```

Now that your `planet-v2` virtual environment is activated, it’s time to install the Planet SDK for Python! Find instructions on how to do so in the [Quick Start Guide](quick-start-guide.md).

## Working with virtual environments

It’s easy to switch in and out of the virtual environments, just `activate` and `deactivate`. You can 
install additional tools with pip on each. The core directories and files remain the same, so you can 
use both v1 and v2 in the same directory. You can even work with them side by side, just open two 
different terminal windows, and activate v1 in one, and v2 in the other.

You should see a different command-line prompt for each, to easily tell which one you are in:

```console
 $ (planet-v1) user@computer ~ $
 ```

!!!note "This is a Python-specific virtual environment"
    Note that non-Python programs (like from node, or C/C++) will be available in both environments. If you want to manage those in a virtual environment then Conda is the way to go, or even full on [docker](https://www.docker.com/) containers.
