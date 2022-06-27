# Copyright 2022 Planet Labs, PBC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""CLI Parameter types"""
from typing import List

import click


class CommaSeparatedString(click.types.StringParamType):
    """A list of strings that is extracted from a comma-separated string."""

    def convert(self, value, param, ctx) -> List[str]:
        if isinstance(value, list):
            convlist = value
        else:
            convstr = super().convert(value, param, ctx)

            if convstr == '':
                self.fail('Entry cannot be an empty string.')

            convlist = [part.strip() for part in convstr.split(",")]

            for v in convlist:
                if not v:
                    self.fail(f'Empty entry encountered in "{value}".')

        return convlist


class CommaSeparatedFloat(click.types.StringParamType):
    """A list of floats that is extracted from a comma-separated string."""
    name = 'VALUE'

    def convert(self, value, param, ctx) -> List[float]:
        values = CommaSeparatedString().convert(value, param, ctx)

        try:
            ret = [float(v) for v in values]
        except ValueError:
            self.fail(f'Cound not convert all entries in "{value}" to float.')

        return ret
