# Version Release

*Planet maintainers only*

Releasing is a two-step process: (1) releasing on GitHub and test.pypi and (2) releasing to PyPI. Releasing on GitHub will automatically trigger a release on test.pypi via a GitHub Action. Following manual confirmation of a successful and satisfactory release on test.pypi, release on PyPI is triggered manually with the Github Action `Autopublish to TestPyPI`. There is also an option to publish to test.pypi and PyPI from your local machine.

NOTE: the version is detected from git using the tag name. There is no need to modify a version file.

If the repository is not on tag, the version will be computed using the default versioning scheme of [setuptools_scm](https://setuptools-scm.readthedocs.io/en/latest/usage/#default-versioning-scheme).

## Versions and Stability

The SDK follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and therefore only major releases should break compatibility. Minor versions may include new functionality and patch versions address bugs or trivial changes (like documentation).

## Release Workflow

1. Create a new GitHub release:
   * From the GitHub UI:
     * Navigate to the [releases UI](https://github.com/planetlabs/planet-client-python/releases), and select "Draft a new release".
     * Choose or create a tag for the release version.  The is expected to simply be the [PEP 440](https://peps.python.org/pep-0440/)
       compliant semantic version number, without any prefix or other adornments.  Examples, from most to least mature:
       * Production release: `2.3.4`
       * Release candidate: `2.3.4rc1`
       * Beta release: `2.3.4b1`
       * Alpha release: `2.3.4a1`
       * Alpha development pre-release build: `2.3.4a1.dev1`
     * Set target the release branch.  This should normally be `main` for production releases.
     * Set title to tag release version
     * Describe the change(s) that are shipping with this version in the release description
   * Alternatively, create a release from the GitHub CLI:
     * Make sure the pre-requisite [gh](https://cli.github.com/manual/gh) CLI is installed, and optionally review the docs for CLI command [gh release create](https://cli.github.com/manual/gh_release_create)
     * By default, `gh release create` will automatically tag releases from the latest state of the default branch
     * Run CLI command `gh release create {VERSION} --notes "{RELEASE NOTES}"` where `VERSION` is the release version and `RELEASE NOTES` is the description of changes
2. Verify the successful run of the Github Action [`Autopublish to TestPyPI`](https://github.com/planetlabs/planet-client-python/actions/workflows/autopublish-testpypi.yml) and validate the test release on [test.pypi.org](https://test.pypi.org/project/planet/)
3. Run the Github Action [`Publish on PyPI`](https://github.com/planetlabs/planet-client-python/actions/workflows/publish-pypi.yml)
4. Verify the successful run of the Github Action `Publish on PyPI` and validate the release on [pypi.org](https://pypi.org/project/planet/)
5. Verify the successful and correct publishing of documentation to Read the Docs.
   Read the Docs publishing should be triggered automatically by Github
   [project webhooks](https://github.com/planetlabs/planet-client-python/settings/hooks).
   Correct publishing includes verifying that the `default`, `stable`, and `latest`
   versions of the documentation point to the correct versions, and that the version
   specific documentation URL also works as expected.  The management of these
   symbolic documentation versions is handled by Read the Docs
   [automation rules](https://app.readthedocs.org/dashboard/planet-sdk-for-python/rules/).
   * Published to [planet-sdk-for-python](https://planet-sdk-for-python.readthedocs.io/en/latest/) (Note the new version-less project slug in DNS name).
     * _`default`_: [https://planet-sdk-for-python.readthedocs.io/](https://planet-sdk-for-python.readthedocs.io/) - Should point to same version as `stable`.
     * `stable`: [https://planet-sdk-for-python.readthedocs.io/en/stable/](https://planet-sdk-for-python.readthedocs.io/en/stable/) - Should point to the highest stable release version.
     * `latest`: [https://planet-sdk-for-python.readthedocs.io/en/latest/](https://planet-sdk-for-python.readthedocs.io/en/latest/) - Should point to the most recent build from `main`.
     * _`version`_: [https://planet-sdk-for-python.readthedocs.io/en/X.YY.ZZ/](https://planet-sdk-for-python.readthedocs.io/en/X.YY.Z/) - Should point to version `X.YY.ZZ`.
   * Published to [planet-sdk-for-python-v2](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/) (Note the older "v2" in the project slug in the DNS name).
     * _`default`_: [https://planet-sdk-for-python-v2.readthedocs.io/](https://planet-sdk-for-python-v2.readthedocs.io/) - Should point to same version as `stable`.
     * `stable`: [https://planet-sdk-for-python-v2.readthedocs.io/en/stable/](https://planet-sdk-for-python-v2.readthedocs.io/en/stable/) - Should point to the highest stable release version.
     * `latest`: [https://planet-sdk-for-python-v2.readthedocs.io/en/latest/](https://planet-sdk-for-python-v2.readthedocs.io/en/latest/) - Should point to the most recent build from `main`.
     * _`version`_: [https://planet-sdk-for-python-v2.readthedocs.io/en/X.YY.ZZ/](https://planet-sdk-for-python-v2.readthedocs.io/en/X.YY.ZZ/) - Should point to version `X.YY.ZZ`.
   * Pre-release versions should _not_ impact the default version of the documentation. Pre-release version may be published as the `latest` version.

## Local publishing

Publishing to testpypi and pypi can also be performed locally with:

```console
  $ nox -s build publish-testpypi
```
then
```console
  $ nox -s publish-pypi
```

This approach requires specifying the pypi/testpypi api token as the password at the prompt.


## Conda builds

When stable, not pre-release, files are uploaded to PyPI, a bot will detect them and make an automated PR to https://github.com/conda-forge/planet-feedstock/pulls. When a Conda-forge maintainer merges that PR, a package will be built for the new version and will be published to https://anaconda.org/conda-forge/planet/files.
