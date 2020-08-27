=================
Planet API Client
=================

Python client library and CLI for Planet's public API.

.. image:: https://travis-ci.org/planetlabs/planet-client-python.svg?branch=master
   :target: https://travis-ci.org/planetlabs/planet-client-python


Installation
------------

Via pip:

.. code-block:: console

    $ pip install planet

The `--user <https://pip.pypa.io/en/stable/user_guide/#user-installs>`__
flag is highly recommended for those new to `pip <https://pip.pypa.io>`__.

A PEX executable (Windows not supported) and source releases are
`here <https://github.com/planetlabs/planet-client-python/releases/latest>`__.


Documentation
-------------

Online documentation: `https://planetlabs.github.io/planet-client-python/index.html <https://planetlabs.github.io/planet-client-python/index.html>`__

Documentation is also provided for download `here <https://github.com/planetlabs/planet-client-python/releases/latest>`__.


Development
-----------

To develop with or use the library in your own projects, see the `wiki <https://github.com/planetlabs/planet-client-python/wiki>`__.


Virtual Environment Quick Start (Mac)
-------------------------------------
As a quick start to develop, install virtualenvwrapper.

.. code-block::

    $ pip install virtualenvwrapper

Then check where the package was installed by running

.. code-block::

    which virtualenvwrapper.sh

And copying what's returned, which could look like this

.. code-block::

    /Library/Frameworks/Python.framework/Versions/3.8/bin/virtualenvwrapper.sh

Next, add the following lines to your bash profile.

.. code-block::

    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/Devel
    source /Library/Frameworks/Python.framework/Versions/3.8/bin/virtualenvwrapper.sh

Finally, source your bash profile and run the following lines in cl to create the virtual environment

.. code-block::

    cd path/to/planet-client-python
    mkvirtualenv planet-client-python
    workon planet-client-python
    pip install -e .

API Key
-------

The API requires an account for use. `Signup here <https://www.planet.com/explorer/?signup>`__.

This can be provided via the environment variable `PL_API_KEY` or the flag `-k` or `--api-key`.

Using `planet init` your account credentials (login/password) can be used to obtain the api key.


Example CLI Usage
-----------------

**Hint: autocompletion can be enabled in some shells using**::

    eval "$(_PLANET_COMPLETE=source planet)"

Basics and help::

    planet

The CLI provides access to the `data API <https://www.planet.com/docs/reference/data-api/>`__ ::

    planet data

OR specific command help::

    planet data download --help
