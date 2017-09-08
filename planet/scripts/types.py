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

import json
import re

import click
from click.types import CompositeParamType

from .util import read
from .util import _split

from planet.api import filters
from planet.api.utils import geometry_from_json
from planet.api.utils import strp_lenient
from planet.scripts.item_asset_types import get_item_types, get_asset_types, \
    DEFAULT_ITEM_TYPES, DEFAULT_ASSET_TYPES


metavar_docs = {
    'FIELD COMP VALUE...': '''A comparison query format where FIELD is a
    property of the item-type and COMP is one of lt, lte, gt, gte and VALUE is
    the number or date to compare against.

    Note: ISO-8601 variants are supported. For example, ``2017`` is short for
    ``2017-01-01T00:00:00+00:00``.
    ''',
    'FIELD VALUES...': '''Specifies an 'in' query where FIELD is a property
    of the item-type and VALUES is space or comma separated text or numbers.
    ''',
    'GEOM': '''Specify a geometry in GeoJSON format either as an inline value,
    stdin, or a file. ``@-`` specifies stdin and ``@filename`` specifies
    reading from a file named 'filename'. Otherwise, the value is assumed to
    be GeoJSON.
    ''',
    'FILTER': '''Specify a Data API search filter provided as JSON.
    ``@-`` specifies stdin and ``@filename`` specifies reading from a file
    named 'filename'. Otherwise, the value is assumed to be JSON.
    ''',
    'ITEM-TYPE': '''Specify Item-Type(s) of interest. Case-insensitive,
    supports glob-matching, e.g. ``psscene*`` means ``PSScene3Band`` and
    ``PSScene4Band``. The ``all`` value specifies every Item-Type.
    ''',
    'ASSET-TYPE': '''Specify Asset-Type(s) of interest. Case-insenstive,
    supports glob-matching, e.g. ``visual*`` specifies ``visual`` and
    ``visual_xml``.
    '''
}


class _LenientChoice(click.Choice):
    '''Like click.Choice but allows
    case-insensitive prefix matching
    optional 'all' matching
    optional prefix matching
    glob matching
    format fail msges for large selection of choices

    returns a list unlike choice (to support 'all')
    '''

    allow_all = False
    allow_prefix = False

    def get_metavar(self, param):
        return self.name.upper()

    def _fail(self, msg, val, param, ctx):
        self.fail('%s choice: %s.\nChoose from:\n\t%s' %
                  (msg, val, '\n\t'.join(self.choices)), param, ctx)

    def convert(self, val, param, ctx):
        matched = set()
        for p in _split(val):
            matched = matched.union(self._match(p, param, ctx))
        return list(matched)

    def _match(self, val, param, ctx, update_on_fail=True):
        lval = val.lower()
        if lval == 'all' and self.allow_all:
            return self.choices
        if '*' in lval:
            pat = lval.replace('*', '.*')
            matches = [c for c in self.choices
                       if re.match(pat, c.lower())]
        elif self.allow_prefix:
            matches = [c for c in self.choices
                       if c.lower().startswith(lval)]
        else:
            matches = [c for c in self.choices if c.lower() == lval]
        if not matches and update_on_fail:
            self._update_choices()  # get choices from a remote source.
            return self._match(val, param, ctx, False)  # Try one more time
        elif not matches:
            self._fail('invalid', val, param, ctx)
        else:
            return matches

    def _update_choices(self):
        self.choices = self.get_remote_choices()

    def get_remote_choices(self):
        '''
        No-op just returns current choices.
        Subclasses should override.
        '''
        return self.choices


class ItemType(_LenientChoice):
    name = 'item-type'
    allow_all = True
    allow_prefix = True

    def __init__(self):
        _LenientChoice.__init__(self, DEFAULT_ITEM_TYPES)

    def get_remote_choices(self):
        return get_item_types()


class AssetType(_LenientChoice):
    name = 'asset-type'

    def __init__(self):
        _LenientChoice.__init__(self, DEFAULT_ASSET_TYPES)

    def get_remote_choices(self):
        return get_asset_types()


class AssetTypePerm(AssetType):

    @staticmethod
    def to_permissions(asset_types):
        return filters.permission_filter(*[
            'assets.%s:download' % a for a in asset_types
        ])

    def convert(self, val, param, ctx):
        return AssetTypePerm.to_permissions(
            AssetType.convert(self, val, param, ctx))


class _FilterFieldValues(CompositeParamType):
    name = 'field values'
    arity = 2

    def convert(self, val, param, ctx):
        field, vals = val
        vals = _split(vals)
        parsed = []
        for v in vals:
            v = v.strip()
            if not v:
                continue
            try:
                parsed.append(self.val_type(v))
            except ValueError:
                self.fail('invalid value: %s' % v, param, ctx)
        return self._builder(field, *parsed)


class StringIn(_FilterFieldValues):
    val_type = str

    @property
    def _builder(self):
        return filters.string_filter


class NumberIn(_FilterFieldValues):
    val_type = float

    @property
    def _builder(self):
        return filters.num_filter


class Range(CompositeParamType):
    arity = 3
    name = 'field comp value'
    comp_ops = ['lt', 'lte', 'gt', 'gte']

    @property
    def _builder(self):
        return filters.range_filter

    def _parse(self, val, param, ctx):
        try:
            return float(val)
        except ValueError:
            self.fail('invalid value for range: "%s", must be number' % val)

    def convert(self, vals, param, ctx):
        field, comp_op, val = vals
        if comp_op not in self.comp_ops:
            self.fail('invalid operator: %s. allowed: %s' % (
                comp_op, ','.join(self.comp_ops)), param, ctx)
        args = dict([(comp_op, self._parse(val, param, ctx))])
        return self._builder(field, **args)


class DateRange(Range):
    @property
    def _builder(self):
        return filters.date_range

    def _parse(self, val, param, ctx):
        parsed = strp_lenient(val)
        if parsed is None:
            self.fail('invalid date: %s.' % val, param, ctx)
        return parsed


class GeomFilter(click.ParamType):
    name = 'geom'

    def convert(self, val, param, ctx):
        val = read(val)
        if not val:
            return []
        try:
            geoj = json.loads(val)
        except ValueError:
            raise click.BadParameter('invalid GeoJSON')
        geom = geometry_from_json(geoj)
        if geom is None:
            raise click.BadParameter('unable to find geometry in input')
        return [filters.geom_filter(geom)]


class FilterJSON(click.ParamType):
    name = 'filter'

    def convert(self, val, param, ctx):
        val = read(val)
        if not val:
            return []
        try:
            filt = json.loads(val)
        except ValueError:
            raise click.BadParameter('invalid JSON')
        if not filters.is_filter_like(filt):
            self.fail('Does not appear to be valid filter', param, ctx)
        return filt


class SortSpec(CompositeParamType):
    name = 'field order'
    arity = 2

    def convert(self, val, param, ctx):
        if not val:
            return ''
        field, order = val
        fields = ('published', 'acquired')
        if field not in fields:
            raise click.BadParameter(
                'sort only supports: %s' % ' '.join(fields))
        orders = ('asc', 'desc')
        if order not in orders:
            raise click.BadParameter(
                'order only supports: %s' % ' '.join(orders))
        return ' '.join(val)
