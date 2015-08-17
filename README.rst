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

    planet get-scenes-list --help

An API key is `required <https://www.planet.com/explorers/>`__.

This can be provided via the environment variable `PL_API_KEY` or the flag `-k` or `--api-key`.

Examples
~~~~~~~~

Get a visual ortho scene by id (writes to working directory)::

    planet download 20141008_170544_0907

Get an analytic ortho scene by id::

    planet download 20141008_170544_0907 --analytic

Get scene metadata by id (and pretty print)::

    planet fetch_scene_info -pp 20141008_170544_0907
