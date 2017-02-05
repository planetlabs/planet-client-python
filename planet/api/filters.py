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


def _filter(ftype, config=None, **kwargs):
    kwargs.update({
        'type': ftype,
        'config': config,
    })
    return kwargs


def and_filter(*predicates):
    return _filter("AndFilter", predicates)


def or_filter(*predicates):
    return _filter("OrFilter", predicates)


def not_filter(*predicates):
    return _filter("NotFilter", predicates)


def date_range(field_name, **kwargs):
    for k, v in kwargs.items():
        if hasattr(v, 'isoformat'):
            # @todo check timezone handling
            kwargs[k] = v.isoformat() + 'Z'
    return _filter("DateRangeFilter", config=kwargs, field_name=field_name)


def range_filter(field_name, **kwargs):
    return _filter("RangeFilter", config=kwargs, field_name=field_name)


def geom_filter(geom, field_name=None):
    return _filter("GeometryFilter", config=geom,
                   field_name=field_name or "geometry")


def num_filter(field_name, *vals):
    return _filter("NumberInFilter", config=vals, field_name=field_name)


def string_filter(field_name, *vals):
    return _filter("StringInFilter", config=vals, field_name=field_name)
