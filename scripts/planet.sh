#!/bin/bash
# Copyright 2022 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


DOCKER_IMAGE=${PLANET_SDK_DOCKER_IMAGE:-planetlabs/planet-client-python}
DOCKER_TAG=${PLANET_SDK_DOCKER_TAG:-2.0.0}
#CONTAINER_WD=/appuser
CONTAINER_HD=/root
CONTAINER_WD=/data

# TODO:
#     - Need to intercept and mangle CLI options that deal with file IO.
#       We need to bind mount into the docker, and adjust args to reflect
#       the bind mount paths
#     - That the command is run as root so we don't have problems writing
#       the token files is really rather clumsy. Best practice is to not
#       run commands in the docker as root.
if [ ! -e "${HOME}/.planet" ]
then
    mkdir "${HOME}/.planet"
    chmod 700 "${HOME}/.planet"
fi

# TODO: we should probably just move/rename this to "${HOME}/.planet/legacyauth.api_key.json" or something.
if [ ! -e "${HOME}/.planet.json" ]
then
    touch "${HOME}/.planet.json"
    chmod 600 "${HOME}/.planet.json"
fi

exec docker run --rm -ti \
    --mount type=bind,source="${HOME}/.planet",target="${CONTAINER_HD}/.planet" \
    --mount type=bind,source="${HOME}/.planet.json",target="${CONTAINER_HD}/.planet.json" \
    --mount type=bind,source="${PWD}",target="${CONTAINER_WD}" \
    "${DOCKER_IMAGE}:${DOCKER_TAG}" "$@"
