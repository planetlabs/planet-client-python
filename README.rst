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
