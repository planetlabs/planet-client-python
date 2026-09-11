from pathlib import Path
import shutil
import sys

import nox

nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = False

nox.options.sessions = ['lint', 'analyze', 'test', 'coverage', 'docs']

source_files = ("planet", "examples", "tests", "setup.py", "noxfile.py")
# Generated code — excluded from linting and formatting checks
generated_dirs = ("planet/api_models", )

BUILD_DIRS = ['build', 'dist']


@nox.session
def analyze(session):
    session.install(".[lint]")

    session.run("mypy",
                "--ignore-missing",
                "--exclude",
                "|".join(generated_dirs),
                "planet")


@nox.session
def coverage(session):
    session.install("-e", ".[test]")

    session.run('coverage',
                'run',
                '-m',
                'pytest',
                '-qq',
                '--no-header',
                '--no-summary',
                '--no-cov',
                '--ignore',
                'examples/')
    session.run('coverage', 'report')


@nox.session(python=["3.10", "3.11", "3.12", "3.13", "3.14"])
def test(session):
    session.run('python', '-m', 'ensurepip', '--upgrade')
    session.install('-U', 'setuptools')
    session.install(".[test]")

    options = session.posargs
    # -W=error raises pytest warnings to errors so they are caught by CI
    # to exclude some warnings, see
    # https://docs.python.org/3/library/warnings.html#temporarily-suppressing-warnings
    session.run('python',
                '-m',
                'pytest',
                '--ignore',
                'examples/',
                '-v',
                '-Werror',
                '-Wignore::DeprecationWarning:tqdm.std',
                '-Wignore::PendingDeprecationWarning:planet.auth',
                *options)


@nox.session
def lint(session):
    session.install("-e", ".[lint]")

    session.run("flake8",
                f"--exclude={','.join(generated_dirs)}",
                *source_files)
    # yapf --exclude is a repeatable flag taking one fnmatch pattern; a bare
    # directory name matches nothing, so the trailing /* is required.
    yapf_excludes = [f"--exclude={d}/*" for d in generated_dirs]
    session.run('yapf', '--diff', '-r', *yapf_excludes, *source_files)


@nox.session
def docs_test(session):
    session.install("-e", ".[docs, test]")

    options = session.posargs

    # Because these doc examples can be long-running, output
    # the INFO and above log messages so we know what's happening
    session.run('pytest',
                '--doctest-glob',
                '*.md',
                '--no-cov',
                '--ignore',
                'examples/',
                '--ignore',
                'tests/',
                '--log-cli-level=INFO',
                *options)


@nox.session
def docs(session):
    """Build documentation locally"""
    session.install("-e", ".[docs]")

    session.run("mkdocs", "build")


@nox.session
def watch(session):
    """Build and serve live docs for editing"""
    session.install("-e", ".[docs]")

    session.run("mkdocs", "serve")


@nox.session
def examples(session):
    session.install("-e", ".[test]")

    options = session.posargs

    # Because these example scripts can be long-running, output the
    # example's stdout so we know what's happening
    session.run('pytest', '--no-cov', 'examples/', '-s', *options)


@nox.session
def generate_models(session):
    """Re-generate Pydantic models for the Destinations API in planet/api_models/.

    Uses the same pinned datamodel-code-generator as `nox -s validate_models`,
    so the committed output is byte-identical to what the drift check
    regenerates. Do not reformat the result.

    Run after a known API spec change to refresh the models, then re-run
    validate_models to confirm compatibility.
    """
    session.install("-e", ".[validate_models]")

    sys.path.insert(0, str(Path(__file__).parent / "tests" / "drift"))
    import codegen_config

    for name, url in codegen_config.SPECS.items():
        output = Path("planet/api_models") / f"{name}.py"
        session.run(*codegen_config.codegen_argv(url, output))


@nox.session
def validate_models(session):
    """Validate committed Pydantic models match the live API specs.

    Fetches live OpenAPI specs from Planet's API and compares against committed
    snapshots. Fails if any spec has changed. No API key required.

    To refresh snapshots after a deliberate API change, run:
        nox -s generate_models
    Intended as a pre-release gate; not included in the default nox session list.
    """
    session.install("-e", ".[validate_models]")
    session.run(
        "pytest",
        "tests/drift/validate_models.py",
        # Stop conftest discovery below tests/, whose conftest imports the
        # full test-suite dependencies that this extra deliberately omits.
        "--confcutdir=tests/drift",
        # setup.cfg addopts injects --cov, but this extra deliberately omits
        # pytest-cov; clear addopts rather than pull in the full test deps.
        "-o",
        "addopts=",
        "-v",
        "--tb=short",
    )


@nox.session
def build(session):
    """Build package"""
    # check preexisting
    exist_but_should_not = [p for p in BUILD_DIRS if Path(p).is_dir()]
    if exist_but_should_not:
        session.error(f"Pre-existing {', '.join(exist_but_should_not)}. "
                      "Run clean session and try again")

    session.install('build', 'twine', 'check-wheel-contents')

    session.run(*'python -m build --sdist --wheel'.split())
    session.run('check-wheel-contents', 'dist')


@nox.session
def clean(session):
    """Remove build directories"""
    to_remove = [Path(d) for d in BUILD_DIRS if Path(d).is_dir()]
    for p in to_remove:
        shutil.rmtree(p)


@nox.session
def publish_testpypi(session):
    """Publish to TestPyPi using API token"""
    _publish(session, 'testpypi')


@nox.session
def publish_pypi(session):
    """Publish to PyPi using API token"""
    _publish(session, 'pypi')


def _publish(session, repository):
    missing = [p for p in BUILD_DIRS if not Path(p).is_dir()]
    if missing:
        session.error(
            f"Missing one or more build directories: {', '.join(missing)}. "
            "Run build session and try again")

    session.install('twine')

    files = [str(f) for f in Path('dist').iterdir()]
    session.run("twine", "check", *files)
    session.run("twine",
                "upload",
                f"--repository={repository}",
                '-u=__token__',
                *files)
