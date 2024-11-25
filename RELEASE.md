# Version Release

*Planet maintainers only*

Releasing is a two-step process: (1) releasing on GitHub and test.pypi and (2) releasing to PyPI. Releasing on GitHub will automatically trigger a release on test.pypi via a GitHub Action. Following manual confirmation of a successful and satisfactory release on test.pypi, release on PyPI is triggered manually with the Github Action `Autopublish to TestPyPI`. There is also an option to publish to test.pypi and PyPI from your local machine.

NOTE: the version is detected from git using the tag name. There is no need to modify a version file.

If the repository is not on tag, the version will be computed using the default versioning scheme of [setuptools_scm](https://setuptools-scm.readthedocs.io/en/latest/usage/#default-versioning-scheme).

## Versions and Stability

The SDK follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and therefore only major releases should break compatibility. Minor versions may include new functionality and patch versions address bugs or trivial changes (like documentation).

## Release Workflow

1. Create a release branch off of `main` that bumps the SDK version number and updates the changelog:
   * Update `CHANGES.txt`, adhering to [keep a changelog](https://keepachangelog.com/)
2. Create a PR for the release branch and merge into `main`
3. Create a new GitHub release:
   * From the GitHub UI:
     * Navigate to the releases UI
     * Set tag to release version
     * Set target to `main`
     * Set title to tag release version
     * Copy description from the new entry in the changelog
   * Alternatively, create a release from the GitHub CLI:
     * Make sure the pre-requisite [gh](https://cli.github.com/manual/gh) CLI is installed, and optionally review the docs for CLI command [gh release create](https://cli.github.com/manual/gh_release_create)
     * By default, `gh release create` will automatically tag releases from the latest state of the default branch
     * Run CLI command `gh release create {VERSION} --notes "{RELEASE NOTES}"` where `VERSION` is the release version and `RELEASE NOTES` is the description copied from the new entry in the changelog
4. Verify the successful run of the Github Action `Autopublish to TestPyPI` and validate the test release on [test.pypi.org](https://test.pypi.org/project/planet/)
5. Run the Github Action `Publish on PyPI`
6. Verify the successful run of the Github Action `Publish on PyPI` and validate the release on [pypi.org](https://pypi.org/project/planet/)


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
