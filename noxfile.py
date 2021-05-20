import nox

nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = False

nox.options.sessions = ['test', 'lint']

source_files = ("planet", "examples", "tests", "setup.py", "noxfile.py")


@nox.session(python=["3.7", "3.8", "3.9"])
def test(session):
    session.install("-e", ".[test]")

    options = session.posargs
    if '-k' in options:
        options.append('--no-cov')
    session.run('pytest', '--ignore', 'examples/', '-v', *options)


@nox.session
def lint(session):
    session.install("-e", ".[lint]")

    session.run("flake8", *source_files)


@nox.session
def docs_test(session):
    session.install("-e", ".[docs]")

    options = session.posargs

    # Because these doc examples can be long-running, output
    # the INFO and above log messages so we know what's happening
    session.run('pytest', '--doctest-glob', '*.md', '--no-cov',
                '--ignore', 'examples/',
                '--ignore', 'tests/',
                '--log-cli-level=INFO', *options)


@nox.session
def docs(session):
    session.install("-e", ".[docs]")

    session.run("mkdocs", "build")


@nox.session
def watch(session):
    session.install("--upgrade", "-e", ".[docs]")

    session.run("mkdocs", "serve")


@nox.session
def examples(session):
    session.install("-e", ".[test]")

    options = session.posargs

    # Because these example scripts can be long-running, output the
    # example's stdout so we know what's happening
    session.run('pytest', '--no-cov', 'examples/', '-s', *options)
