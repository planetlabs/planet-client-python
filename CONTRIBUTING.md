# Development

For development, installing all Python versions supported by this repo is
recommended. One way of achieving this is with
[pyenv](https://github.com/pyenv/pyenv).

[Nox](https://nox.thea.codes/) is used to automate all checks and build
documentation. Nox manages virtual environments for you, specifying Python
versions and installing the the local, dynamic version of the Planet Python
Client and required development packages.

Where Nox is not used, a virtual environment is highly recommended.
[pyenvwrapper](https://github.com/pyenv/pyenv-virtualenv) manages virtual
environments and works well with pyenv. To install the local, dynamic version
of the Planet Python Client and required development packages into the virtual
environment use:

```console
    $ pip install -e .[dev]
```

## Testing

[Nox](https://nox.thea.codes/) automates all testing and linting. By default,
Nox runs all fast tests and lints the code.

Install Nox in your local dev environment:

```console
    $ pip install nox
```

Run nox:

```console
    $ nox
```

This will run tests against multiple Python versions and will lint the code.
If a specific Python version isn't available on your development machine,
Nox will just skip that version. While that version is skipped for local tests,
the tests will be run on all versions with Continuous Integration (CI) when a
pull request is initiated on the repository.

### Testing Documentation

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

Nox is used to manage the process of building the documentation as well as and
hosting it locally to assist documentation development.

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
