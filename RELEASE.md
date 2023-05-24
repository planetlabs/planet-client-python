# Version Release

*Planet maintainers only*

Releasing is a two-step process: (1) releasing on Github and test.pypi and (2) releasing to pypi. Releasing on Github will automatically trigger a release on test.pypi via a Github Action. Following manual confirmation of a successful and satisfactory release on test.pypi, release on pypi is triggered manually with the Github Action "Automatically Publish on TestPyPi". There is also an option to publish to test.pypi and pypi from your local machine.

The first step in a release is determining if the release is a feature release or a maintenance release. A maintenance release is a backward compatible bug fix or documentation change, while a feature release adds functionality in a backward compatible manner.

#### Release Naming Conventions

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html), which specifies a version number as MAJOR.MINOR.PATCH with a feature release mapped to a MINOR version and a maintenance release mapped to a PATCH.

The following are the release naming conventions:

1. Current Dev Version is obtained from `planet/__version__.py` in the format `MAJOR.MINOR.PATCHdev`
3. Release Version: Remove `dev` from Current Dev Version
4. Next Dev Version: Bumped version of last release with `dev` added to the end.
    * For maintenance release, bump PATCH
    * For feature release, bump MINOR and set PATCH to 0
5. Source branch: 
    * For maintenance release, source branch is `maint-MAJOR.MINOR`
    * For feature release, source branch is the main branch, `main`


##### Maintenance Release Example:

**IF** Current Dev Version ==  `1.1.1dev` **THEN**
  * Release Version: `1.1.1`
  * Next Dev Version: `1.1.2dev`
  * Source Branch: `maint-1.1`

MAINT: YES

##### Feature Release Example:

**IF** Current Dev Version ==  `1.1.1dev` **THEN**
  * Release Version: `1.2.0`
  * Next Dev Version: `1.1.1dev`
  * Source Branch: `main`


## Release Workflow

The release on Github and PyPi performed from a release branch while the release branch PR is in progress. After the releases, the version in the PR is updated before it is merged. Thus, the version in `main` is not the same as the version of the release.

*NOTE: This section refers to version names given in Release Naming Conventions section above.*

1. Starting from the Source Branch, create a release branch named `release-{Release Version}`
1. Make the following changes for the release:
  * Update `CHANGES.txt`, adhering to [Keep a Changelog](https://keepachangelog.com/)
    * Include added, changed, depricated or removed features and bug fixes.
       A list of merged PRs and their titles since the last release can be obtained with `git log $PREVIOUS_RELEASE_TAG..HEAD | awk '/Merge pull request/{print;getline;getline;print}'`.
    * Sort according to importance
  * Update `planet/__version__.py` to Release Version
1. Create a PR for the release branch (named after release branch, description is changelog entry, base is Source Branch), wait for CI to pass
1. Create a new github release:
  * Set Tag to Release Version
  * **!!!** Set Target to the release branch **!!!**
  * Set Title to Tag Release Version
  * Copy Description from the new entry in the changelog
  * Select "This is a pre-release" if applicable
1. Verify the successful run of the Github Action "Autopublish to TestPyPi" and validate the test release on [test.pypi.org](https://test.pypi.org/project/planet/)
1. Run the Github Action "Publish on PyPi", **!!!** Set Branch to the release branch **!!!**
1. Verify the successful run of the Github Action "Publish on PyPi" and validate the release on [pypi.org](https://pypi.org/project/planet/)
1. Push a commit to the PR updating `planet/__version__.py` to Next Dev Version
1. Merge PR
1. Announce the release through the following avenues:
 * *Planet Internal:* #python slack channel
 * Changelog
 * Twitter

### Local publishing

Publishing to testpypi and pypi can also be performed locally with:

```console
  $ nox -s build publish-testpypi
```
then
```console
  $ nox -s publish-pypi
```
this approach requires specifying the pypi/testpypi api token as the password at the prompt.

## Conda builds

When stable, not pre-release, files are uploaded to PyPI, a bot will detect them and make an automated PR to https://github.com/conda-forge/planet-feedstock/pulls. When a Conda-forge maintainer merges that PR, a package will be built for the new version and will be published to https://anaconda.org/conda-forge/planet/files.
