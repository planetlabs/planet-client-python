##############################################################################
## Base image
##############################################################################
FROM python:3.9.12-alpine as base
RUN adduser -D -h /appuser appuser
RUN mkdir /data
RUN chown appuser /data
RUN chgrp appuser /data


##############################################################################
## Builder images
##############################################################################
## We use a builder with a virtual env so we can easilly have different
## OS packages in runtime and during pip install to keep runtime images slim.
## This is most relevent when pip installing dependencies with native install-time
## dependencies (such as compilers) that we would rather not have in our runtime
## image.
##
## It is also nice to have a named stage in the docker build that has our
## requirements, but not the code under development, for use with a local IDE.

#######################################
## Builder-1 - Just the dependencies
#######################################
FROM base as builder-1
ENV VIRTUAL_ENV=/venv
RUN python -m venv --system-site-packages  $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /build

RUN apk add gcc
RUN apk add geos-dev
RUN apk add musl-dev
RUN apk add libffi-dev
RUN apk add openssl-dev
RUN apk add rust
RUN apk add cargo

COPY requirements.txt.frozen ./requirements.txt.frozen

RUN python -m pip install  -r requirements.txt.frozen

#######################################
## Builder-2 - Build the product
#######################################
FROM builder-1 as builder-2
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
WORKDIR /build

COPY LICENSE .
COPY README.md .
COPY MANIFEST.in .
COPY setup.py .
COPY setup.cfg .
COPY ./planet ./planet

RUN python -m pip install .

##############################################################################
## Runtime image
##############################################################################
FROM base as runtime
RUN apk add geos
RUN apk add libgcc

ENV VIRTUAL_ENV=/venv
COPY --from=builder-2 "$VIRTUAL_ENV" "$VIRTUAL_ENV"

ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# FIXME: Bind mount user perms - https://github.com/moby/moby/issues/2259
#        Really Docker, you haven't fixed this in 8 years?
#        Note: paths relative to $HOME change with USER, so check wrapper scripts
#        for bind mounts when enabling the USER directive.
# USER appuser
WORKDIR /data
ENTRYPOINT ["/venv/bin/planet"]

##############################################################################
## Unit test image
##############################################################################
# TODO: Test as close to production as possible:
#     - It would be better to test in the runtime rather than a builder container
#     - It would be nice to test as the runtime user
FROM builder-2 as utest
# FROM runtime as utest
ENV CI=true
WORKDIR /build

# COPY requirements-dev.txt.frozen ./requirements-dev.txt.frozen
RUN python -m pip install -e .[dev]
COPY ./tests ./tests

# USER appuser
# FIXME: Why does adding --log-cli-level=DEBUG cause a bunch of tests to fail?
# ENTRYPOINT [ "pytest", "--log-cli-level=DEBUG", "tests" ]
ENTRYPOINT [ "pytest", "tests" ]
