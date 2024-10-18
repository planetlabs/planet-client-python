from pathlib import Path
import shutil

import nox

nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = False

nox.options.sessions = ['lint', 'analyze', 'test', 'coverage', 'docs']

source_files = ("planet", "examples", "tests", "setup.py", "noxfile.py")

BUILD_DIRS = ['build', 'dist']


@nox.session
def analyze(session):
    session.install(".[lint]")

    session.run("mypy", "--ignore-missing", "planet")


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


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"])
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
                *options)


@nox.session
def lint(session):
    session.install("-e", ".[lint]")

    session.run("flake8", *source_files)
    session.run('yapf', '--diff', '-r', *source_files)


@nox.session
def docs_test(session):
    session.install("-e", ".[docs]")

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
