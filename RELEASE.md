# Release Process

*Planet maintainers only*

Releasing is a two-step process: (1) releasing on Github and test.pypi and (2) releasing to pypi. Releasing on Github will automatically trigger a release on test.pypi via a Github Action. Following manual confirmation of a successful and satisfactory release on test.py, release on pypi is triggered manually with the Github Action "Automatically Publish on TestPyPi".

###### Step 1: Release on Github

1. Create a PR with the following:
  * Update `CHANGES.txt` (**PROPOSAL**: change this to `docs/CHANGELOG.md`)
    * Include added, changed, depricated or removed features and bug fixes.
       A list of merged PRs and their titles since the last release can be obtained with `git log <RELEASE_TAG>..HEAD | awk '/Merge pull request/{print;getline;getline;print}`
    * Sort according to importance
    * **PROPOSAL**: Adhere to [Keep a Changelog](https://keepachangelog.com/)
  * Bump version in `planet/__version__.py`
    * **PROPOSAL**: Version number is determined by [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
1. Merge the PR
1. Create a new github release:
  * Set Tag to the version number specified in `planet/__version__.py`
  * Copy Description from the new entry in `docs/CHANGELOG.md`
  * Select "This is a pre-release" if applicable
  * Select "Create a discussion for this release"

###### Step 2: Release on pypi

1. Verify the test release on [test.pypi.org](https://test.pypi.org/project/planet/)
1. Run the Github Action "Publish on PyPi"

###### Local publishing

Publishing to testpypi and pypi can also be performed locally with:

```console
  $ nox -s build publish-testpypi
```
then
```console
  $ nox -s publish-pypi
```
this approach requires specifying the pypi/testpypi api token as the password at the prompt.

