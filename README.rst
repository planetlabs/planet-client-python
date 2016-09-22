=================
Planet API Client
=================

**PRE-ALPHA SOFTWARE - MAY CHANGE**

Initial, incomplete, strawman effort at a Python client to Planet's public API.

.. image:: https://travis-ci.org/planetlabs/planet-client-python.svg?branch=master
   :target: https://travis-ci.org/planetlabs/planet-client-python


Documentation
-------------

`https://planetlabs.github.io/planet-client-python/index.html <https://planetlabs.github.io/planet-client-python/index.html>`__


Installation
------------

Executable CLI releases and documentation are `here <https://github.com/planetlabs/planet-client-python/releases/latest>`__.

To develop with or use the library in your own projects, see the `wiki <https://github.com/planetlabs/planet-client-python/wiki>`__.


Example CLI Usage
-----------------

**Hint: autocompletion can be enabled in some shells using**::

    eval "$(_PLANET_COMPLETE=source planet)"

Basics and help::

    planet

OR specific command help::

    planet search --help

An API key is `required <https://www.planet.com/explorers/>`__.

This can be provided via the environment variable `PL_API_KEY` or the flag `-k` or `--api-key`. Using the `planet init` the username and password can be used and saved instead.

Examples
~~~~~~~~

Get a visual ortho scene by id (writes to working directory)::

    planet download 20150825_180952_1_0b07

Get scene metadata by id (and pretty print)::

    planet metadata -pp 20150825_180952_1_0b07

Get a list of all mosaics::

    planet mosaics


Contributing
~~~~~~~~~~~~

You'll want to set up a virtualenv dev environment:

  virtualenv venv
  . venv/bin/activate

And install development dependencies:

  pip install -e .[dev]

Confirm tests pass:

  make check
