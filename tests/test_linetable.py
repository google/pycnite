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

import unittest

from . import base
from pycnite import linetable
from pycnite import pyc


class TestLineTable(unittest.TestCase):
    """Test linetable parsing."""

    def test_read(self):
        src_file = base.test_src("trivial")
        with open(src_file, "r") as f:
            src = f.readlines()
        n_lines = len(src)
        for version in base.VERSIONS:
            path = base.test_pyc("trivial", version)
            code = pyc.load_file(path)
            lt = linetable.linetable_reader(code)
            entries = lt.read_all()
            self.assertEqual(entries[-1].line, n_lines)


if __name__ == "__main__":
    unittest.main()
