# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for pycnite.linetable."""

import itertools
import unittest

from . import base
from pycnite import linetable
from pycnite import pyc
from pycnite import types


class TestLineTable(unittest.TestCase):
    """Test linetable parsing."""

    def _get_linetable(self, testfile, version, fn=None):
        path = base.test_pyc(testfile, version)
        code = pyc.load_file(path)
        if fn is not None:
            code = code.co_consts[fn]
        lt = linetable.linetable_reader(code)
        return lt.read_all()

    def test_read(self):
        src_file = base.test_src("trivial")
        with open(src_file, "r") as f:
            src = f.readlines()
        n_lines = len(src)
        for version in base.VERSIONS:
            entries = self._get_linetable("trivial", version)
            self.assertEqual(entries[-1].line, n_lines)

    def test_flow(self):
        for version in base.VERSIONS:
            entries = self._get_linetable("flow", version)
            lines = [x.line for x in entries]
            lines = [k for k, _ in itertools.groupby(lines)]
            # Lines checked against the godbolt.org disassembler
            if version == (3, 11):
                expected = [0, 1, 2, 3, 4, 5, 6, 1, 2]
            elif version == (3, 10):
                expected = [1, 2, 3, 4, 5, 6, 1, 2]
            else:
                expected = [1, 2, 3, 4, 5, 6]
            self.assertEqual(lines, expected)

    def test_generator_311(self):
        # Check that we handle NO_COLUMN_INFO correctly in 3.11
        # (regression test for https://github.com/google/pycnite/issues/18)
        entries = self._get_linetable("generator", (3, 11), fn=0)
        self.assertEqual(len(entries), 11)
        for e in entries:
            self.assertEqual(e.line, e.endline)


class TestExceptionTable(unittest.TestCase):
    """Test exceptiontable parsing."""

    def test_basic(self):
        for version in base.VERSIONS:
            # Exception table is new in 3.11
            if version < (3, 11):
                continue
            path = base.test_pyc("exception", version)
            code = pyc.load_file(path)
            et = linetable.ExceptionTableReader(code)
            actual = et.read_all()
            entry = types.ExceptionTableEntry
            # Verified using godbolt
            expected = [
                entry(start=4, end=22, target=26, depth=0, lasti=False),
                entry(start=24, end=24, target=66, depth=0, lasti=False),
                entry(start=26, end=34, target=58, depth=1, lasti=True),
                entry(start=36, end=38, target=66, depth=0, lasti=False),
                entry(start=40, end=46, target=58, depth=1, lasti=True),
                entry(start=48, end=50, target=66, depth=0, lasti=False),
                entry(start=52, end=52, target=58, depth=1, lasti=True),
                entry(start=54, end=62, target=66, depth=0, lasti=False),
                entry(start=66, end=68, target=70, depth=1, lasti=True),
                entry(start=78, end=86, target=92, depth=0, lasti=False),
                entry(start=92, end=94, target=102, depth=1, lasti=True),
            ]
            self.assertEqual(actual, expected)

    def test_complex(self):
        for version in base.VERSIONS:
            # Exception table is new in 3.11
            if version < (3, 11):
                continue
            path = base.test_pyc("complex_exception", version)
            code = pyc.load_file(path)
            et = linetable.ExceptionTableReader(code.co_consts[0])
            actual = et.read_all()
            entry = types.ExceptionTableEntry
            # Verified using godbolt
            expected = [
                entry(start=8, end=20, target=162, depth=0, lasti=False),
                entry(start=22, end=94, target=96, depth=1, lasti=True),
                entry(start=96, end=102, target=104, depth=3, lasti=True),
                entry(start=104, end=108, target=162, depth=0, lasti=False),
                entry(start=110, end=110, target=104, depth=3, lasti=True),
                entry(start=112, end=158, target=162, depth=0, lasti=False),
                entry(start=162, end=180, target=286, depth=1, lasti=True),
                entry(start=182, end=264, target=276, depth=1, lasti=True),
                entry(start=276, end=284, target=286, depth=1, lasti=True),
            ]
            self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
