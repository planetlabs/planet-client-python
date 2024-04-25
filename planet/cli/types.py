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
from datetime import datetime
import json
from typing import List

import click

from planet import exceptions, io


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


class JSON(click.ParamType):
    """JSON specified as a string, json file filename, or stdin."""
    name = 'JSON'

    def convert(self, value, param, ctx) -> dict:
        if isinstance(value, dict):
            convdict = value
        else:
            # read from raw json
            # skip this if value is a Path object or something else
            if isinstance(value, str) and (value.startswith('{')
                                           or value.startswith('[')):
                try:
                    convdict = json.loads(value)
                except json.decoder.JSONDecodeError:
                    self.fail(
                        'JSON string is not valid JSON. Make sure the entire '
                        'JSON string is single-quoted and string entries are '
                        'double-quoted.')

            # read from stdin or file
            else:
                try:
                    with click.open_file(value) as f:
                        convdict = json.load(f)
                except FileNotFoundError:
                    self.fail('File not found.')
                except json.decoder.JSONDecodeError:
                    self.fail('JSON file does not contain valid JSON.')

        if convdict == {}:
            self.fail('JSON cannot be empty.')

        return convdict


class Geometry(click.ParamType):
    name = 'geom'

    def __init__(self):
        self.types = [JSON(), CommaSeparatedString()]

    def convert(self, value, param, ctx):
        for type in self.types:
            try:
                return type.convert(value, param, ctx)
            except click.BadParameter:
                continue


class Field(click.ParamType):
    """Clarify that this entry is for a field"""
    name = 'field'


class Comparison(click.ParamType):
    name = 'comp'
    valid = ['lt', 'lte', 'gt', 'gte']

    def convert(self, value, param, ctx) -> str:
        if value not in self.valid:
            self.fail(f'COMP ({value}) must be one of {",".join(self.valid)}',
                      param,
                      ctx)
        return value


class GTComparison(Comparison):
    """Only support gt or gte comparison"""
    valid = ['gt', 'gte']


class DateTime(click.ParamType):
    name = 'datetime'

    def convert(self, value, param, ctx) -> datetime:
        if not isinstance(value, datetime):
            try:
                value = io.str_to_datetime(value)
            except exceptions.PlanetError as e:
                self.fail(str(e))

        return value
