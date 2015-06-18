Planet API Client
=================

Initial, incomplete, strawman effort at a Python client to Planet's public API.

Installation
------------

Recommend using a virtual environment.

Shellish:

    git clone git@github.com:planetlabs/planet-client-python.git
    cd planet-client-python
    pip install -e .

Enabling bash completion (planet <tab> <tab>):

    eval "$(_PLANET_COMPLETE=source planet)"

If you receive nasty looking error messages regarding a SSLContext object not being available, see:
http://stackoverflow.com/questions/29134512/insecureplatformwarning-a-true-sslcontext-object-is-not-available-this-prevent
(verified to work on Ubuntu 14.04)


Usage
-----

### As a library ###

Pending

### Command line use ###

basics and help:

    planet

OR specific command help

    planet get-scenes-list --help

To do anything real, one must provide an API key. This can be done via the environment variable `PL_API_KEY` or the flag `-k` or `--api-key`.

Examples:

Get a visual ortho scene by id (writes to working directory):

    planet download 20141008_170544_0907
    
Get an analytic ortho scene by id:

    planet download 20141008_170544_0907 --analytic
    
Get scene metadata by id (and pretty print):

    planet fetch_scene_info -pp 20141008_170544_0907

Testing
-------

### Install Test Dependencies ###

A few extra libraries are needed for testing:

    pip install -e .[test]

### Running the Tests ###

There are two suites of tests, one for the cli, the other for the library module.

Both can be run using:

    py.test

Distributing
------------

This requires that development libraries are installed:

    pip install -e .[test]

An executable python file can be built by running:

    pex  .  -o dist/planet -m planet.scripts:cli

This can be executed directly on systems with a python executable and in an environment (bash shell) capable of interpreting a shebang.

TODO!
-----

* more command line flags/tools (query filters, for example)
* more docs
* tests
