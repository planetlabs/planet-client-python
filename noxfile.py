import nox

nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = True

source_files = ("planet", "tests", "setup.py", "noxfile.py")


@nox.session(python=["3.7", "3.8", "3.9"])
def test(session):
    session.install("-e", ".[test]")

    options = session.posargs
    session.run("pytest", "-v", *options)


@nox.session
def lint(session):
    session.install("-e", ".[dev]")

    session.run("flake8", *source_files)
