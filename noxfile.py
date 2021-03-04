import nox

nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = True
# nox.options.keywords = "test + check"

source_files = ("planet", "tests", "setup.py", "noxfile.py")
# docs_requirements = ("mkdocs", "mkdocs-material", "mkautodoc>=0.1.0")


@nox.session(python=["3.7", "3.8", "3.9"])
def test(session):
    session.install("-e", ".[test]")

    options = session.posargs
    if "-k" or "-x" in options:
        options.append("--no-cov")

    session.run("pytest", "-v", *options)


@nox.session
def lint(session):
    session.install("-e", ".[dev]")

    session.run("flake8", *source_files)

# @nox.session
# def docs(session):
#     session.install("--upgrade", *docs_requirements)
#     session.install("-e", ".")
#
#     session.run("mkdocs", "build")
#
#
# @nox.session(reuse_venv=True)
# def watch(session):
#     session.install("--upgrade", *docs_requirements)
#     session.install("-e", ".")
#
#     session.run("mkdocs", "serve")
