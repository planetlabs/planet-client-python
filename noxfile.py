import nox

nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = True

nox.options.sessions = ['test', 'lint']

source_files = ("planet", "examples", "tests", "setup.py", "noxfile.py")


@nox.session(python=["3.7", "3.8", "3.9"])
def test(session):
    session.install("-e", ".[test]")

    options = session.posargs
    session.run("pytest", "-v", *options)


@nox.session
def lint(session):
    session.install("-e", ".[dev]")

    session.run("flake8", *source_files)


@nox.session
def docs(session):
    session.install("-e", ".[dev]")

    session.run('pytest', '--doctest-glob', '*.md', '--no-cov', 'README.md')
