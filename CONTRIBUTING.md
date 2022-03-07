# Contributing

Thank you for your interest in contributing to the Planet SDK for Python! This
document explains how to contribute successfully.

## Tools

This repository uses two primary tools for development:
* [Nox](https://nox.thea.codes/) to automate testing
* [YAPF](https://github.com/google/yapf) to enforce style guidelines

Install Nox in your local dev environment:

```console
    $ pip install nox
```

Install YAPF in your local dev environment:

```console
    $ pip install yapf
```

### Nox

In this repository, Nox is used to automate testing, linting, and to build
documentation. Nox manages virtual environments for you, specifying Python
versions and installing the the local, dynamic version of the Plant SDK for
Python and required development packages.

Run Nox:

```console
    $ nox
```

If no changes have been made to the Nox environment since it was last run,
speed up the run by reusing the environment:

```console
    $ nox -r
```

The configuration for Nox is given in `noxfile.py`. See the Nox link above for
advanced usage.

##### Alternative to Nox
Nox is the recommended way to manage local testing. With Nox it is not necessary
to install the Planet SDK for Python on the local machine for testing.
However, Nox is not necessary for local testing. Where Nox is not used, a
virtual environment is highly recommended.
[pyenvwrapper](https://github.com/pyenv/pyenv-virtualenv) manages virtual
environments and works well with pyenv. To install the local, dynamic version
of the Planet SDK for Python and required development packages into the virtual
environment use:

```console
    $ pip install -e .[dev]
```

### YAPF

Code in this repository follows the
[PEP8](https://www.python.org/dev/peps/pep-0008/) style guide and uses
[YAPF](https://github.com/google/yapf) to enforce and automate formatting.
Linting in Nox will fail if YAPF would reformat a portion of the code.
Helpfully, YAPF can be used to automatically reformat the code for you so you
don't have to worry about formatting issues. WIN!

To see how YAPF would reformat a file:

```console
    $ yapf --diff [file]
```

To reformat the file:

```console
    $ yapf --in-place [file]
```

The configuration for YAPF is given in `setup.cfg` and `.yapfignore`.
See the YAPF link above for advanced usage.

##### Alternative to YAPF

YAPF is not required to follow the style and formatting guidelines. You can
perform all formatting on your own using the linting output as a guild. Painful,
maybe, but possible!

## Testing

When a Pull Request (PR) is created, the Continuous Integration (CI) runs all
tests with Nox on all supported versions of Python. Before a PR can be
considered, all tests must pass. To minimize the feedback loop, we recommend
running Nox on your local machine. By default, Nox runs all fast tests and
lints the code.

Installing all supported Python versions locally is recommended. This allows
Nox to fully reproduce the CI tests.
One way of achieving this is with [pyenv](https://github.com/pyenv/pyenv).
If a specific Python version isn't available on your development machine,
Nox will just skip that version in the local tests.

Testing is performed with [pytest](https://docs.pytest.org/) and
[pytest-cov](https://pytest-cov.readthedocs.io/). The configuration for these
packages is given in `setup.cfg`.

Command-line arguments can be passed to pytest within Nox. For example, to only
run the tests on a certain file, use:

```console
    $ nox -- [file]
```

By default, Nox runs tests on all supported Python versions along with linting.
However, Nox can run a test on a single Python version, as well.

To run tests on python 3.7:

```console
    $ nox -s test-3.7
```

## Linting

In addition to running tests, the CI also lints the code. Again, this is done
using Nox. Linting is performed using [flake8](https://flake8.pycqa.org/)
and YAPF (mentioned above). By default, Nox runs tests along with linting.
However, Nox can run linting alone.

To run linting:

```console
    $ nox -s lint
```

### Testing Documentation

NOTE: Doc tests need to be reworked and are failing. See
[#275](https://github.com/planetlabs/planet-client-python/issues/275).

There are many code examples written into the documentation that need to be
tested to ensure they are accurate. These tests are not run by default because
they communicate with the Planet services, and thus are slower and also could
incur usages.

To test the documentation, run the Nox `docs_test` session:

```console
    $ nox -s docs_test
```

This will test all code examples in Markdown documents.
To only test one document:

```console
    $ nox -s docs_test -- <document_name>.md
```

### Testing Examples

The `examples` directory is populated with many helpful examples of how to
use the Planet SDK for Python in real use cases. These examples also need to
be tested to ensure they are accurate. These tests are not run by default
because they are long and communicate with the Planet services; and thus are
very slow and also could incur usages.

To test the examples, run the Nox `examples` session:

```console
    $ nox -s examples
```

This will test all scripts within the `examples` directory.
To only test one script:

```console
    $ nox -s examples -- <script_name>.py
```

For more information on developing examples, see the examples
[README.md](examples/README.md)


## Documentation

Documentation is built from Markdown files in the `docs` directory using
[MkDocs](https://www.mkdocs.org/) according to `mkdocs.yml`. The API reference
is auto-populated from code docstrings. These docstrings must be in the
[google format](https://mkdocstrings.github.io/handlers/python/#google-style)
(note: we use `Parameters` in our docstrings).

Nox is used to manage the process of building the documentation as well as
serving it locally to assist documentation development.

To build and host an automatically-updated local version of the documentation:

```console
    $ nox -s watch
```

To build the documentation:

```console
    $ nox -s docs
```

In addition to verifying that the documentation renders correctly locally,
the accuracy of the code examples must be verified. See Testing Documentation
above.
