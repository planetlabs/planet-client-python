# Copyright 2017-2019 Planet Labs, Inc.
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

from collections import deque
from itertools import chain
import json
import logging
import re
from os import path
import sys
import tempfile
import textwrap
import threading
import time

import click
from click import termui

from planet import api
from planet.api import filters

# get_terminal_size was removed from click.termui in click 8.1.0.
# Previously, click delegated to shutil.get_terminal_size for Python
# versions >= 3.3. This import dance allows us to *not* pin the Python
# Client's click dependency for any version of Python.
try:
    from shutil import get_terminal_size
except ImportError:
    from click.termui import get_terminal_size


def _split(value):
    '''return input split on any whitespace or comma'''
    return re.split(r'\s+|,', value)


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
    # in windows with a vagrant ro-mount, this was raised instead
    except IOError:
        return False
    return True


def filter_from_opts(**kw):
    '''Build a AND filter from the provided kwargs defaulting to an
    empty 'and' filter (@todo: API workaround) if nothing is provided.

    If the 'filter_json' argument is provided, this will be assumed to contain
    a filter specification and will be anded with other filters. If the
    'filter_json' is a search, the search filter value will be used.

    All kw values should be tuple or list
    '''
    filter_in = kw.pop('filter_json', None)
    active = and_filter_from_opts(kw)
    if filter_in:
        filter_in = filter_in.get('filter', filter_in)
        if len(active['config']) > 0:
            active = filters.and_filter(active, filter_in)
        else:
            active = filter_in
    return active


def search_req_from_opts(**kw):
    # item_type will be list of lists - flatten
    item_types = chain.from_iterable(kw.pop('item_type'))
    name = kw.pop('name', '')
    interval = kw.pop('interval', '')
    filt = filter_from_opts(**kw)
    return filters.build_search_request(
        filt, item_types, name=name, interval=interval)


def create_order_request(**kwargs):
    for opt in ('item_type', 'bundle'):
        inputvalue = kwargs.get(opt)
        if len(inputvalue) > 1:
            raise click.ClickException(
                'only one value for {} is allowed.'.format(opt))

    item_type = kwargs.get('item_type')[0]
    bundle = kwargs.get('bundle')[0]
    ids = kwargs.get('id').split(',')
    email = kwargs.get('email')
    config = kwargs.get('cloudconfig')
    clip = kwargs.get('clip')
    tools = kwargs.get('tools')

    request = {'name': kwargs.get('name'),
               'products': [{'item_ids': ids,
                             'item_type': item_type,
                             'product_bundle': bundle}
                            ],
               'tools': [
    ],
        'delivery': {
    },
        'notifications': {
                   'email': email
    },
    }

    request["delivery"]["archive_filename"] = "{{name}}_{{order_id}}.zip"
    request["delivery"]["archive_type"] = "zip"
    request["delivery"]["single_archive"] = True

    if config:
        with open(config, 'r') as f:
            conf = json.load(f)
            request["delivery"].update(conf)

    # NOTE clip is the only tool that currently can be specified via CLI param.
    # A full tool chain can be specified via JSON file, so that will overwrite
    # clip if both are present. TODO add other common tools as params.
    if clip and not tools:
        toolchain = [{'clip': {'aoi': json.loads(clip)}}]
        request['tools'].extend(toolchain)

    if tools:
        with open(tools, 'r') as f:
            toolchain = json.load(f)
            request["tools"].extend(toolchain)

    return request


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
    nl = False
    if not ndjson and (pretty or (pretty is None and sys.stdout.isatty())):
        indent = 2
        sort_keys = True
        nl = True
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
            if len(res) == 0:  # if the body is empty, just return the status
                click.echo("status: {}".format(response.response.status_code))
            else:
                res = json.dumps(json.loads(res), indent=indent,
                                 sort_keys=sort_keys)
                click.echo(res)
            if nl:
                click.echo()
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


class _BaseOutput(object):

    refresh_rate = 1

    def _report_complete(self, item, asset, path=None):
        msg = {
            'item': item['id'],
            'asset': asset['type'],
            'location': path or asset['location']
        }
        # cancel() allows report log to persist for both ANSI & regular output
        self.cancel()
        click.echo(json.dumps(msg))

    def __init__(self, thread, dl):
        self._thread = thread
        self._timer = None
        self._dl = dl
        self._running = False
        dl.on_complete = self._report_complete

    def _schedule(self):
        if self._thread.is_alive() and self._running:
            self._timer = threading.Timer(self.refresh_rate, self._run)
            self._timer.start()
            return True

    def _run(self, exit=False):
        if self._running:
            self._output(self._dl.stats())
        if not exit and self._running and not self._schedule():
            self._run(True)

    def start(self):
        self._running = True
        self._run()

    def cancel(self):
        self._running = False
        self._timer and self._timer.cancel()


class Output(_BaseOutput):

    def _output(self, stats):
        logging.info('%s', stats)


class AnsiOutput(_BaseOutput):

    def __init__(self, *args, **kw):
        _BaseOutput.__init__(self, *args, **kw)
        self._start = time.time()
        # log msg ring buffer
        self._records = deque(maxlen=100)
        self._lock = threading.Lock()
        self._stats = {}

        # highjack the root handler, remove existing and replace with one
        # that feeds our ring buffer
        h = logging.Handler()
        root = logging.getLogger('')
        h.formatter = root.handlers[0].formatter
        h.emit = self._emit
        root.handlers = (h,)
        self._handler = h

    def start(self):
        click.clear()
        _BaseOutput.start(self)

    def _emit(self, record):
        with self._lock:
            self._records.append(self._handler.format(record))
            self._do_output()

    def _output(self, stats):
        with self._lock:
            self._stats.update(stats)
            self._do_output()

    def _do_output(self):
        # renders a terminal like:
        # highlighted status rows
        # ....
        #
        # scrolling log output
        # ...
        width, height = get_terminal_size()
        wrapper = textwrap.TextWrapper(width=width)
        self._stats['elapsed'] = '%d' % (time.time() - self._start)
        stats = ['%s: %s' % (k, v) for k, v in sorted(self._stats.items())]
        stats = wrapper.wrap(''.join([s.ljust(25) for s in stats]))
        remaining = height - len(stats) - 2
        stats = [s.ljust(width) for s in stats]
        lidx = max(0, len(self._records) - remaining)
        loglines = []
        while remaining > 0 and lidx < len(self._records):
            wrapped = wrapper.wrap(self._records[lidx])
            while remaining and wrapped:
                loglines.append(wrapped.pop(0))
                remaining -= 1
            lidx += 1
        # clear/cursor-to-1,1/hightlight
        click.echo(u'\u001b[2J\u001b[1;1H\u001b[30;47m' + '\n'.join(stats)
                   # unhighlight
                   + u'\u001b[39;49m\n' + '\n'.join(loglines))


def downloader_output(dl, disable_ansi=False):
    thread = threading.current_thread()
    # Do fancy output if we can or not explicitly disabled.
    # Attention: the click project deprecated a method in its termui
    # module in 8.0.0 and removed it in 8.1.0. If support for v1 of the
    # Python client continues, we should keep an eye on termui's WIN
    # attribute, which looks like an incidental part of click's API
    # (it's not imported into click/__init__.py).
    if sys.stdout.isatty() and not disable_ansi and not termui.WIN:
        return AnsiOutput(thread, dl)
    # work around for lack of nice output for downloader on windows:
    # unless told to be quiet, set logging higher to get some output
    # @todo fallback to simpler 'UI' when isatty on win
    if termui.WIN and not disable_ansi:
        logging.getLogger('').setLevel(logging.INFO)
    return Output(thread, dl)


def ids_from_search_response(resp):
    ret = []
    r = json.loads(resp)
    for feature in r['features']:
        ret.append(feature['id'])
    return ','.join(ret)
