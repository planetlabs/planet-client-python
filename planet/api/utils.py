# Copyright 2015 Planet Labs, Inc.
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

from __future__ import print_function
from datetime import datetime
from . import exceptions
import json
import mimetypes
import os
import random
import re
import string
import threading
from requests.compat import urlparse
from ._fatomic import atomic_open

_ISO_FMT = '%Y-%m-%dT%H:%M:%S.%f+00:00'


def _planet_json_file():
    return os.path.join(os.path.expanduser('~'), '.planet.json')


def read_planet_json():
    fname = _planet_json_file()
    contents = {}
    if os.path.exists(fname):
        with open(fname, 'r') as fp:
            contents = json.loads(fp.read())
    return contents


def write_planet_json(contents):
    fname = _planet_json_file()
    with atomic_open(fname, 'w') as fp:
        fp.write(json.dumps(contents))


def geometry_from_json(obj):
    '''try to find a geometry in the provided JSON object'''
    obj_type = obj.get('type', None)
    if not obj_type:
        return None
    if obj_type == 'FeatureCollection':
        features = obj.get('features', [])
        if len(features):
            obj = obj['features'][0]
            obj_type = obj.get('type', None)
        else:
            return None
    if obj_type == 'Feature':
        geom = obj['geometry']
    else:
        geom = obj
    # @todo we're just assuming it's a geometry at this point
    if 'coordinates' in geom:
        return geom


def check_status(response):
    '''check the status of the response and if needed raise an APIException'''
    status = response.status_code
    if status < 300:
        return
    exception = {
        400: exceptions.BadQuery,
        401: exceptions.InvalidAPIKey,
        403: exceptions.NoPermission,
        404: exceptions.MissingResource,
        429: exceptions.TooManyRequests,
        500: exceptions.ServerError
    }.get(status, None)

    # differentiate between over quota and rate-limiting
    if status == 429 and 'quota' in response.text.lower():
        exception = exceptions.OverQuota

    if exception:
        raise exception(response.text)

    raise exceptions.APIException('%s: %s' % (status, response.text))


def get_filename(response):
    """Derive a filename from the given response.

    >>> import requests
    >>> from planet.api import utils
    >>> response = requests.Response()
    >>> response.headers = {
    ...     'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
    ...     'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
    ...     'accept-ranges': 'bytes',
    ...     'content-type': 'image/tiff',
    ...     'content-length': '57350256',
    ...     'content-disposition': 'attachment; filename="open_california.tif"'
    ... }
    >>> response.url = 'https://planet.com/path/to/example.tif?foo=f6f1'
    >>> print(utils.get_filename(response))
    open_california.tif
    >>> del response
    >>> response = requests.Response()
    >>> response.headers = {
    ...     'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
    ...     'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
    ...     'accept-ranges': 'bytes',
    ...     'content-type': 'image/tiff',
    ...     'content-length': '57350256'
    ... }
    >>> response.url = 'https://planet.com/path/to/example.tif?foo=f6f1'
    >>> print(utils.get_filename(response))
    example.tif
    >>> del response
    >>> response = requests.Response()
    >>> response.headers = {
    ...     'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
    ...     'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
    ...     'accept-ranges': 'bytes',
    ...     'content-type': 'image/tiff',
    ...     'content-length': '57350256'
    ... }
    >>> response.url = 'https://planet.com/path/to/oops/'
    >>> print(utils.get_filename(response)) #doctest:+SKIP
    planet-bFL6pwki.tif
    >>>

    :param response: An HTTP response.
    :type response: :py:class:`requests.Response`
    :returns: a filename (i.e. ``basename``)
    :rtype: str
    """
    name = (get_filename_from_headers(response.headers) or
            get_filename_from_url(response.url) or
            get_random_filename(response.headers.get('content-type')))
    return name


def get_filename_from_headers(headers):
    """Get a filename from the Content-Disposition header, if available.

    >>> from planet.api import utils
    >>> headers = {
    ...     'date': 'Thu, 14 Feb 2019 16:13:26 GMT',
    ...     'last-modified': 'Wed, 22 Nov 2017 17:22:31 GMT',
    ...     'accept-ranges': 'bytes',
    ...     'content-type': 'image/tiff',
    ...     'content-length': '57350256',
    ...     'content-disposition': 'attachment; filename="open_california.tif"'
    ... }
    >>> name = utils.get_filename_from_headers(headers)
    >>> print(name)
    open_california.tif
    >>>
    >>> headers.pop('content-disposition', None)
    'attachment; filename="open_california.tif"'
    >>> name = utils.get_filename_from_headers(headers)
    >>> print(name)
    None
    >>>

    :param headers dict: a ``dict`` of response headers
    :returns: a filename (i.e. ``basename``)
    :rtype: str or None
    """
    cd = headers.get('content-disposition', '')
    match = re.search('filename="?([^"]+)"?', cd)
    return match.group(1) if match else None


def get_filename_from_url(url):
    """Get a filename from a URL.

    >>> from planet.api import utils
    >>> urls = [
    ...     'https://planet.com/',
    ...     'https://planet.com/path/to/',
    ...     'https://planet.com/path/to/example.tif',
    ...     'https://planet.com/path/to/example.tif?foo=f6f1&bar=baz',
    ...     'https://planet.com/path/to/example.tif?foo=f6f1&bar=baz#quux'
    ... ]
    >>> for url in urls:
    ...     print('{} -> {}'.format(url, utils.get_filename_from_url(url)))
    ...
    https://planet.com/ -> None
    https://planet.com/path/to/ -> None
    https://planet.com/path/to/example.tif -> example.tif
    https://planet.com/path/to/example.tif?foo=f6f1&bar=baz -> example.tif
    https://planet.com/path/to/example.tif?foo=f6f1&bar=baz#quux -> example.tif
    >>>

    :returns: a filename (i.e. ``basename``)
    :rtype: str or None
    """
    path = urlparse(url).path
    name = path[path.rfind('/')+1:]
    return name or None


def get_random_filename(content_type=None):
    """Get a pseudo-random, Planet-looking filename.

    >>> from planet.api import utils
    >>> print(utils.get_random_filename()) #doctest:+SKIP
    planet-61FPnh7K
    >>> print(utils.get_random_filename('image/tiff')) #doctest:+SKIP
    planet-V8ELYxy5.tif
    >>>

    :returns: a filename (i.e. ``basename``)
    :rtype: str
    """
    extension = mimetypes.guess_extension(content_type or '') or ''
    characters = string.ascii_letters + '0123456789'
    letters = ''.join(random.sample(characters, 8))
    name = 'planet-{}{}'.format(letters, extension)
    return name


def write_to_file(directory=None, callback=None, overwrite=True):
    '''Create a callback handler for asynchronous Body handling.

    If provided, the callback will be invoked as described in
    :py:meth:`planet.api.models.Body.write`. In addition, if the download
    is skipped because the destination exists, the callback will be invoked
    with ``callback(skip=body)``.

    The name of the file written to will be determined from the Body.name
    property.

    :param directory str: The optional directory to write to.
    :param callback func: An optional callback to receive notification of
                          write progress.
    :param overwrite bool: Overwrite any existing files. Defaults to True.
    '''

    def writer(body):
        file = os.path.join(directory or '.', body.name)
        if overwrite or not os.path.exists(file):
            body.write(file, callback)
        else:
            if callback:
                callback(skip=body)
            body.response.close()
    return writer


def strp_timestamp(value):
    return datetime.strptime(value, _ISO_FMT)


def strf_timestamp(when):
    return datetime.strftime(when, _ISO_FMT)


def strp_lenient(when):
    when = when[:-1] if when[-1] == 'Z' else when
    for i in range(0, 9):
        try:
            return datetime.strptime(when, _ISO_FMT[:i*-3 or len(_ISO_FMT)])
        except ValueError:
            pass


class GeneratorAdapter(list):
    '''Allow a generator to be used in JSON serialization'''
    def __init__(self, gen):
        self.gen = gen

    def __iter__(self):
        return self.gen

    def __len__(self):
        return 1


def probably_wkt(text):
    '''Quick check to determine if the provided text looks like WKT'''
    valid = False
    valid_types = set([
        'POINT', 'LINESTRING', 'POLYGON', 'MULTIPOINT',
        'MULTILINESTRING', 'MULTIPOLYGON', 'GEOMETRYCOLLECTION',
    ])
    matched = re.match(r'(\w+)\s*\([^)]+\)', text.strip())
    if matched:
        valid = matched.group(1).upper() in valid_types
    return valid


def probably_geojson(input):
    '''A quick check to see if this input looks like GeoJSON. If not a dict
    JSON-like object, attempt to parse input as JSON. If the resulting object
    has a type property that looks like GeoJSON, return that object or None'''
    valid = False
    if not isinstance(input, dict):
        try:
            input = json.loads(input)
        except ValueError:
            return None
    typename = input.get('type', None)
    supported_types = set([
        'Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString',
        'MultiPolygon', 'GeometryCollection', 'Feature', 'FeatureCollection'
    ])
    valid = typename in supported_types
    return input if valid else None


def handle_interrupt(cancel, f, *a, **kw):
    '''Execute a function f(*a, **kw) listening for KeyboardInterrupt and if
    handled, invoke the cancel function. Blocks until f is complete or the
    interrupt is handled.
    '''
    res = []

    def run():
        res.append(f(*a, **kw))
    t = threading.Thread(target=run)
    t.start()
    # poll (or we miss the interrupt) and await completion
    try:
        while t.is_alive():
            t.join(.1)
    except KeyboardInterrupt:
        cancel()
        raise
    return res and res.pop()
