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
''' Provide atomic file support - a subset of `fatomic` included here
(https://github.com/abarnert/fatomic) as upstream is not in pypi
'''
import contextlib
import errno
import os
import shutil
import sys
import tempfile
import types

# If we're on 3.3+, just use os.replace; if we're on POSIX, rename
# and replace do the same thing.
try:
    _replace_file = os.replace
except AttributeError:
    if sys.platform != 'win32':
        _replace_file = os.rename
    else:
        # This requires PyWin32 if you're on Windows. If that's not
        # accepted, you can write a ctypes solution, but then you'll
        # have to handle unicode-vs.-bytes strings and creating an
        # OSError from GetLastError and so on yourself, which I don't
        # feel like doing. (I'll accept a pull request from anyone
        # else who does...)
        import win32api
        import win32con

        def _replace_file(src, dst):
            win32api.MoveFileEx(src, dst, win32con.MOVEFILE_REPLACE_EXISTING)


@contextlib.contextmanager
def atomic_open(filename, mode, *args, **kwargs):
    if mode[0] not in 'wxa' or len(mode) > 1 and mode[1] == '+':
        raise ValueError("invalid mode: '{}'".format(mode))
    f = tempfile.NamedTemporaryFile(mode=mode,
                                    prefix=os.path.basename(filename),
                                    dir=os.path.dirname(filename),
                                    suffix='.tmp',
                                    delete=False)
    _discard = [False]
    try:
        if mode[0] == 'a':
            try:
                with open(filename, 'r'+mode[1:], *args, **kwargs) as fin:
                    shutil.copyfileobj(fin, f)
            except (OSError, IOError) as e:
                if e.errno == errno.ENOENT:
                    pass

        def discard(self, _discard=_discard):
            _discard[0] = True
        f.discard = types.MethodType(discard, f)
        yield f
    # ischneider addition to fatomic - catch/raise any exception thrown in with
    # block and force discarding
    except:
        _discard = [True]
        raise
    finally:
        f.close()
        if _discard[0]:
            os.unlink(f.name)
        else:
            _replace_file(f.name, filename)
