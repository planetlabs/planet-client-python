# Development

A virtual environment is strongly recommended; a tool like virtualenvwrapper
can make this easier.

Once the project repository is cloned and a virtualenv is created, install the
required packages using:
```console
    $ pip install -e .[dev]
```
This will bring in all required development packages.

A Makefile is provided to automate some tasks:
* check - run flake8 and tests
* html-docs - generate docs
* pex - build pex executable

## Testing

### Install a branch

A handy means of installing a branch or tag is:

```console
    $ pip install https://github.com/planetlabs/planet-client-python/archive/<branch-or-tag>.zip
```
Similarly, this can be done using [pipsi](https://github.com/mitsuhiko/pipsi) like:

```console
    $ pipsi install https://github.com/planetlabs/planet-client-python/archive/master.zip#egg=planet
```

With virtualenvwrapper's
[mktmpenv](https://virtualenvwrapper.readthedocs.io/en/latest/command_ref.html#mktmpenv),
testing out a new version is as simple as:

```console
    $ mktmpenv && pip install https://github.com/planetlabs/planet-client-python/archive/master.zip
```

When the environment is deactivated, it is destroyed leaving only wheels in your cache.

### Managing Python version

To run tests against multiple versions of Python, you can use
[tox](http://tox.readthedocs.io/en/latest/).

Install tox in your local dev environment:

```console
    $ pip install tox
```

(optionally: $ pip install --user tox to make the tool available outside of this project's virtualenv)

Run tox:

```console
    $ tox

This will run tests against multiple Python 3.6+ versions -- if an interpreter
for a specific Python version isn't available on your development machine,
tox will just skip that version.
