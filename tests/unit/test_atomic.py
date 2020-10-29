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
import os
from planet.api._fatomic import atomic_open


def test_atomic_open(tmpdir):
    outfile = str(tmpdir.join('foo'))

    def lsdir():
        return os.listdir(str(tmpdir))

    def assert_content_is(expected):
        with open(outfile, 'r') as fp:
            assert fp.read() == expected

    # success case
    with atomic_open(outfile, 'w') as fp:
        fp.write('bar')
    assert_content_is('bar')
    # no tmp files remain
    assert ['foo'] == lsdir()

    # exception during write, assert file remains untouched
    try:
        with atomic_open(outfile, 'w') as fp:
            fp.write('bazzy')
            raise Exception('drat')
    except Exception:
        assert_content_is('bar')
    else:
        assert False
    # no tmp files remain
    assert ['foo'] == lsdir()

    # manual discarding
    with atomic_open(outfile, 'w') as fp:
        fp.write('bazzy')
        fp.discard()
    assert_content_is('bar')
    # no tmp files remain
    assert ['foo'] == lsdir()
