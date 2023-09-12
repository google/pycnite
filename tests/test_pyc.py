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

"""Tests for pycnite.pyc."""

import unittest

from . import base
from pycnite import types
from pycnite import pyc


class TestLoader(unittest.TestCase):
    """Test pyc loading."""

    def test_load(self):
        for version in base.VERSIONS:
            path = base.test_pyc("basic", version)
            with open(path, "rb") as f:
                code = pyc.load(f)
            self.assertIsInstance(code, types.CodeTypeBase)
            self.assertEqual(version, code.python_version)

    def test_loads(self):
        for version in base.VERSIONS:
            path = base.test_pyc("basic", version)
            with open(path, "rb") as f:
                data = f.read()
            code = pyc.loads(data)
            self.assertIsInstance(code, types.CodeTypeBase)
            self.assertEqual(version, code.python_version)

    def test_load_file(self):
        for version in base.VERSIONS:
            path = base.test_pyc("basic", version)
            code = pyc.load_file(path)
            self.assertIsInstance(code, types.CodeTypeBase)
            self.assertEqual(version, code.python_version)


if __name__ == "__main__":
    unittest.main()
