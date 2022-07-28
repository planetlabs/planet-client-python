# Copyright 2017 Planet Labs, Inc.
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

import warnings

from .exceptions import (APIException, BadQuery, InvalidAPIKey)
from .exceptions import (NoPermission, MissingResource, OverQuota)
from .exceptions import (ServerError, RequestCancelled, TooManyRequests)
from .client import (ClientV1)
from .utils import write_to_file
from . import filters
from .__version__ import __version__  # NOQA

__all__ = [
    ClientV1, APIException, BadQuery, InvalidAPIKey,
    NoPermission, MissingResource, OverQuota, ServerError, RequestCancelled,
    TooManyRequests,
    write_to_file,
    filters
]


class ClientV1DeprecationWarning(FutureWarning):
    """Warn about deprecation of ClientV1."""


warnings.warn(
    "The planet.api module is deprecated and will be removed in version 2.0.0. "
    "For more details please see the discussion at "
    "https://github.com/planetlabs/planet-client-python/discussions.",
    ClientV1DeprecationWarning,
    stacklevel=2
)
