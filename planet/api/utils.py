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
'''Helpful and commonly-used functionality'''
import mimetypes
import random
import re
import string

from requests.compat import urlparse


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
            get_filename_from_url(str(response.url)) or
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
