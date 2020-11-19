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
import tempfile
import types


@contextlib.contextmanager
def atomic_open(filename, mode, *args, **kwargs):
    if mode[0] not in 'wxa' or len(mode) > 1 and mode[1] == '+':
        raise ValueError("invalid mode: '{}'".format(mode))
    f = tempfile.NamedTemporaryFile(mode=mode,
                                    prefix=os.path.basename(filename),
                                    dir=os.path.dirname(filename),
                                    suffix='.tmp',
                                    delete=False)
    # track: explicitly discarded, normal/abnormal completion
    _discard = [None]
    try:
        if mode[0] == 'a':
            try:
                with open(filename, 'r'+mode[1:], *args, **kwargs) as fin:
                    shutil.copyfileobj(fin, f)
            except (OSError, IOError) as e:
                if e.errno == errno.ENOENT:
                    pass

        def discard(self, _discard=_discard):
            # explicit discard
            _discard[0] = True
        f.discard = types.MethodType(discard, f)
        yield f
        # normal completion
        if not _discard[0]:
            _discard[0] = False
    # block and force discarding
    finally:
        f.close()
        # if we didn't complete or were aborted, delete
        if _discard[0] is None or _discard[0]:
            os.unlink(f.name)
        else:
            os.replace(f.name, filename)
