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

from itertools import chain
import json
import re
import sys
from os import path
import tempfile
import warnings

import click
from requests.packages.urllib3 import exceptions as urllib3exc

from planet import api
from planet.api import filters
from planet.api import utils as api_utils


def _split(value):
    '''return input split on any whitespace'''
    return re.split('\s+', value)


# monkey patch warnings module to hide InsecurePlatformWarning - the warning
# notes 'may cause certain SSL connections to fail' so it doesn't seem to
# introduce any vulnerabilities
# we capture the warning if present and present this if any SSLError is caught
# just in case this configuration is an issue
_insecure_warning = []
showwarning = warnings.showwarning


def hack(message, category, filename, lineno):
    if category is urllib3exc.InsecurePlatformWarning:
        if len(_insecure_warning) == 0:
            _insecure_warning.append(message)
        return
    showwarning(message, category, filename, lineno)


warnings.showwarning = hack


def and_filter_from_opts(opts):
    '''build an AND filter from the provided opts dict as passed to a command
    from the filter_options decorator. Assumes all dict values are lists of
    filter dict constructs.'''
    return filters.and_filter(*list(chain.from_iterable([
        o for o in opts.values() if o]
    )))


def check_writable(dirpath):
    try:
        tempfile.NamedTemporaryFile(dir=dirpath).close()
    except OSError:
        return False
    return True


def filter_from_opts(**kw):
    '''Build a AND filter from the provided filter_in OR kwargs defaulting to an
    empty 'and' filter (@todo: API workaround)
    '''
    filter_in = kw.pop('filter_json', None)
    active = and_filter_from_opts(kw)
    no_filters = len(active['config']) == 0
    if no_filters and not filter_in:
        return filters.and_filter()
    if not no_filters and filter_in:
        raise click.ClickException(
            'Specify filter options or provide using --filter-json, not both')
    if filter_in:
        active = filter_in
    return active


def search_req_from_opts(**kw):
    item_types = kw.pop('item_type')
    name = kw.pop('name', '')
    interval = kw.pop('interval', '')
    filt = filter_from_opts(**kw)
    return filters.build_search_request(
        filt, item_types, name=name, interval=interval)


def call_and_wrap(func, *args, **kw):
    '''call the provided function and wrap any API exception with a click
    exception. this means no stack trace is visible to the user but instead
    a (hopefully) nice message is provided.
    note: could be a decorator but didn't play well with click
    '''
    try:
        return func(*args, **kw)
    except api.exceptions.APIException as ex:
        click_exception(ex)
    except urllib3exc.SSLError:
        # see monkey patch above re InsecurePlatformWarning
        if _insecure_warning:
            click.echo(click.style(str(_insecure_warning[0]), fg='red'))
        raise


def click_exception(ex):
    if type(ex) is api.exceptions.APIException:
        raise click.ClickException('Unexpected response: %s' % str(ex))
    msg = "%s: %s" % (type(ex).__name__, str(ex))
    raise click.ClickException(msg)


def echo_json_response(response, pretty, limit=None, ndjson=False):
    '''Wrapper to echo JSON with optional 'pretty' printing. If pretty is not
    provided explicity and stdout is a terminal (and not redirected or piped),
    the default will be to indent and sort keys'''
    indent = None
    sort_keys = False
    if not ndjson and (pretty or (pretty is None and sys.stdout.isatty())):
        indent = 2
        sort_keys = True
    try:
        if ndjson and hasattr(response, 'items_iter'):
            items = response.items_iter(limit)
            for item in items:
                click.echo(json.dumps(item))
        elif not ndjson and hasattr(response, 'json_encode'):
            response.json_encode(click.get_text_stream('stdout'), limit=limit,
                                 indent=indent, sort_keys=sort_keys)
        else:
            res = response.get_raw()
            res = json.dumps(json.loads(res), indent=indent,
                             sort_keys=sort_keys)
            click.echo(res)
    except IOError as ioe:
        # hide scary looking broken pipe stack traces
        raise click.ClickException(str(ioe))


def read(value, split=False):
    '''Get the value of an option interpreting as a file implicitly or
    explicitly and falling back to the value if not explicitly specified.
    If the value is '@name', then a file must exist with name and the returned
    value will be the contents of that file. If the value is '@-' or '-', then
    stdin will be read and returned as the value. Finally, if a file exists
    with the provided value, that file will be read. Otherwise, the value
    will be returned.
    '''
    v = str(value)
    retval = value
    if v[0] == '@' or v == '-':
        fname = '-' if v == '-' else v[1:]
        try:
            with click.open_file(fname) as fp:
                if not fp.isatty():
                    retval = fp.read()
                else:
                    retval = None
        # @todo better to leave as IOError and let caller handle it
        # to better report in context of call (e.g. the option/type)
        except IOError as ioe:
            # if explicit and problems, raise
            if v[0] == '@':
                raise click.ClickException(str(ioe))
    elif path.exists(v) and path.isfile(v):
        with click.open_file(v) as fp:
            retval = fp.read()
    if retval and split and type(retval) != tuple:
        retval = _split(retval.strip())
    return retval
