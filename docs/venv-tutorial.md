## Getting started with venv & Planet SDK

There are lots of great resources online about virtual environments for python.
This tutorial is aimed at users of the Planet SDK who have little or no experience
with virtual environments but want to be early users of v2 (and still use
their v1 when testing).

### Conda vs venv

There are two main options in the Python world for virtual environments:

* [venv](https://docs.python.org/3/library/venv.html)
* [conda](https://conda.io)

Both are great options. Venv is built into python (version 3.3 and above), so if you've got python
then it's already there. Conda does a bit 'more', as venv just works for python, while conda
creates virtual environments for all libraries and languages (but was designed for python). We
recommend venv, as [GDAL](https://gdal.org/), arguably the most useful geospatial command-lines,
can sometimes be a pain with Conda. And our releases are not (yet) targeting conda packaging.

### venv pre-requisites

The main pre-requisite for venv is that you have Python 3.3 and above. To check your python
version type:

```console
 $ python --version
```

 If you installed on Windows or Linux you most likely have python 3. Mac OS ships by default with
 python 2, so you'll need to install python 3. 

#### Installing Python 3 on a Mac.

 Our recommended route is to install [homebrew](https://brew.sh/). To do that you just run the 
 following on your command-line:

```console
 $ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After it download and installs you just run:

```console
 $ brew install python
```

 That will set up a command called `python3` that you can use to call python3.

### Setting your venvs

It's good to read up on how venv works, we recommend 
[this tutorial](https://www.dataquest.io/blog/a-complete-guide-to-python-virtual-environments/)
to get a solid understanding.

To be able to work with both the v1 stable and v2 pre-release we recommend setting up 2 virtual enviroments.
A good place to put them is in a .venv directory.

```console
 $ mkdir ~/.venv
 $ cd ~/.venv
```

 Then you'll want to create a venv for v1 and v2. First create the
 v1 virtual environment with:

```console
  $ python3 -m venv ~/.venv/planet-v1
```

 Then you can activate on a mac or linux with:

```console
 $ source ~/.venv/planet-v1/bin/activate
```

and on windows with:

```console
  $ planet-v1\Scripts\activate.bat
```

Then you'll be in your new virtual environment. If you already have v1 installed
it will likely work. But you can install it with:

```console
  $ pip install planet
```

Run `planet --version` to check which version it is. If you don't see a v1 then you may
need to adjust your path (ask in [discussions](https://github.com/planetlabs/planet-client-python/discussions)
if you're having trouble, and we can add more info here).

Then you'll want to deactivate, and set up v2:

```console
 $ deactivate
```

 Takes you out of the virtual environment, to your base install.

 Then set up v2, like you did v1:

```console
 $ python3 -m venv ~/.venv/planet-v2
```

And activate the same way. Then install as instructed in [the readme](../README.md#installation).

### Working with virtual environments

It's easy to switch in and out of the virtual environments, just `activate` and `deactivate`. You can 
install additional tools with pip on each. The core directories and files remain the same, so you can 
use both v1 and v2 in the same directory. You can even work with them side by side, just open two 
different terminal windows, and activate v1 in one, and v2 in the other.

You should see a different command-line prompt for each, to easily tell which one you are in:

```console
 $ (planet-v1) user@computer ~ $
 ```

Note that non-python programs (like from node, or C/C++) will be available in both environments. If you want
to manage those in a virtual environment then Conda is the way to go, or even full on [docker](https://www.docker.com/)
containers.