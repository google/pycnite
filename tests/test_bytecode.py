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

"""Tests for pyc_utils.bytecode."""

import unittest

from . import base
from pyc_utils import bytecode
from pyc_utils import pyc


class TestBytecode(unittest.TestCase):
    """Test bytecode reading."""

    def test_reader(self):
        path = base.test_pyc("trivial", (3, 11))
        code = pyc.load_file(path)
        opcodes = [x.name for x in bytecode.dis(code)]
        expected = [
            "RESUME",
            "LOAD_CONST",
            "STORE_NAME",
            "LOAD_CONST",
            "STORE_NAME",
            "LOAD_NAME",
            "LOAD_NAME",
            "BINARY_OP",
            "STORE_NAME",
            "LOAD_NAME",
            "LOAD_NAME",
            "BINARY_OP",
            "STORE_NAME",
            "LOAD_CONST",
            "RETURN_VALUE",
        ]
        self.assertEqual(opcodes, expected)

    def test_argval(self):
        def run(version):
            path = base.test_pyc("trivial", version)
            code = pyc.load_file(path)
            opcodes = [(x.name, x.argval) for x in bytecode.dis(code)]
            if version == (3, 11):
                opcodes = opcodes[1:5]
            else:
                opcodes = opcodes[0:4]
            expected = [
                ("LOAD_CONST", 1),
                ("STORE_NAME", "x"),
                ("LOAD_CONST", 2),
                ("STORE_NAME", "y"),
            ]
            self.assertEqual(opcodes, expected)

        for version in base.VERSIONS:
            run(version)


if __name__ == "__main__":
    unittest.main()
