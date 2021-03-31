# Examples

This directory contains examples for how to use the Planet SDK for Python.

# Navigation
Each example script is named according to the convention
`<Planet API>_<use_case>.py`.

## Usage

To use these examples, just run the scripts with `python <script_name>`. These
examples hit the Planet services, so be aware that usage and fees may apply.

## Contributing

New examples are great! They just need to meet two requirements.

First off, the name of the new example needs to follow the examples naming
convention.

Second, the new example needs to be tested. All examples in this directory are
tested as a part of an automated test suite. The testing is conducted by
`test_examples.py`.
All scripts should default to downloading into the directory pointed to by the
`TEST_DOWNLOAD_DIR` environment variable, with logic for when that variable
is missing. For example, `DOWNLOAD_DIR = os.getenv('TEST_DOWNLOAD_DIR', '.')`.

Running all example script tests is a long process and also, since each script
communicates with the Planet servers, could affect your usage and incur fees.
To minimize the pain, filter the scripts tested to e.g. the script under
development with:

```console
> nox -s examples -- <script_name>.py
````

For a new script named 
`new_script.py`, this would be `nox -s examples -- new_script.py`
