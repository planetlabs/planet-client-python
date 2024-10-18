# Contributing

Thank you for your interest in contributing to the Planet SDK for Python! This
document explains how to contribute successfully.

## Workflows

### Development

#### Development Branch

The default branch is always `main` and should be always considered in-development.  Feature enhancements, bug fixes, and other maintenance should be performed in a development branch, starting with the appropriate base branch and merged back into that branch:

```console
git checkout main
git pull
git checkout -b new-branch-name
```

#### Branch Naming

Branch names should describe the work performed within the branch, and include a ticket number if applicable.  For example, a branch that corrects typos in documentation and is not ticketed could be named `fix-documentation-typos`, and a branch that adds a new feature and is ticketed could be named `new-feature-123` (where 'new-feature' is the name of the feature and '-123' is the ticket number).

### Pull Requests

NOTE: Make sure to set the appropriate base branch for PRs. See Development Branch above for appropriate branch.

The Pull Request requirements are included in the pull request template as a list of checkboxes.

Not listed in the PR template, but enforced by the system, are the additional requirements that the PR pass Continuous Integration (CI) checks and that the PR have at least one approval by a project maintainer.

The CI checks:

* all tests on all supported versions of Python
* test coverage
* linting / formatting
* type annotation
* docs build successfully

To minimize the feedback loop, we have configured Nox so that it can be used to run all of the CI checks on the local machine. See the [Development Tools](#development-tools) section for information on running CI checks locally with Nox.

### Releasing

The release process is outlined in [RELEASE.md](RELEASE.md).

## <a name="development-tools"></a>Development Tools

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

To run nox with the default sessions (same checks as CI: lint, analyze, test,
coverage, docs) type "nox".

```console
    $ nox
```

If no changes have been made to the Nox environment since it was last run,
speed up the run by reusing the environment:

```console
    $ nox -r
```

If only one test is desired, specify it with `-s`. To only run linting:

```console
$ nox -s lint
```

To determine which tests are available:

```console
    $ nox --list
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
    $ pip install -e .'[dev]'
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

These commands can be performed on the entire repository, when run from the repository root directory, with:

```console
    $ yapf --diff -r .
```

and

```console
    $ yapf --diff -r .
```
The configuration for YAPF is given in `setup.cfg` and `.yapfignore`.
See the YAPF link above for advanced usage.

##### Alternative to YAPF

YAPF is not required to follow the style and formatting guidelines. You can
perform all formatting on your own using the linting output as a guild. Painful,
maybe, but possible!

## Testing

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

By default, Nox runs tests on all supported Python versions along with other
CI checks. However, Nox can run a test on a single Python version.

To run tests on python 3.13:

```console
    $ nox -s test-3.13
```

Configuration can be passed onto pytest through Nox.

To only run tests in a specific file:

```console
    $ nox -s test3.13 -- tests/unit/test_http.py
```

Or to only run tests filtered by keyword:

```console
   $ nox -s test3.13 -- -k test__Limiter
```

## Code coverage

To measure code coverage and see a report:

```console
    $ nox -s coverage
```

## Linting

Linting is performed using [flake8](https://flake8.pycqa.org/)
and YAPF (mentioned above). By default, Nox runs the lint check along with
all other CI checks. However, Nox can run just the linting check.

To run lint check:

```console
    $ nox -s lint
```

## Static code analysis

The project uses [mypy](https://mypy.readthedocs.io/en/stable/) for static
analysis of code. Mypy checks for correctness of type hints and can find other
type-related bugs. The nox session that calls mypy is named analyze.

```console
    $ nox -s analyze
```

## <a name="documentation"></a> Documentation

Documentation is built from Markdown files in the `docs` directory using
[MkDocs](https://www.mkdocs.org/) according to `mkdocs.yml`. The API reference
is auto-populated from code docstrings. These docstrings must be in the
[google format](https://mkdocstrings.github.io/handlers/python/#google-style)
(note: we use `Parameters` in our docstrings).

By default, Nox builds the docs along with other CI checks. However, Nox can
also be used to only build the docs or to build and serve the docs locally
to assist documentation development.

To build the documentation:

```console
    $ nox -s docs
```

To build and host an automatically-updated local version of the documentation:

```console
    $ nox -s watch
```

Copy the local url from the console output and paste it into your browser to view the live rendered docs.

In addition to verifying that the documentation renders correctly locally,
the accuracy of the code examples must be verified. See Testing Documentation
below.


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
