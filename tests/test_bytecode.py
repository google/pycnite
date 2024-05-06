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

"""Tests for pycnite.bytecode."""

import unittest

from . import base
from pycnite import bytecode
from pycnite import pyc


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

    def test_line_col(self):
        path = base.test_pyc("trivial", (3, 11))
        code = pyc.load_file(path)
        opcode = bytecode.dis(code)[0]
        self.assertIsNotNone(opcode.line)
        self.assertIsNotNone(opcode.endline)
        self.assertIsNotNone(opcode.col)
        self.assertIsNotNone(opcode.endcol)

    def test_extended_arg(self):
        code = bytearray([144, 10, 144, 20, 100, 1])
        ops = list(bytecode.wordcode_reader(code))
        expected_arg = 10 << 16 | 20 << 8 | 1
        expected = [bytecode.RawOpcode(0, 6, 100, expected_arg)]
        self.assertEqual(ops, expected)

    def test_generator_expression(self):
        # Check for a corner case in 3.11 generator expressions
        path = base.test_pyc("genexpr", (3, 11))
        code = pyc.load_file(path)
        d = bytecode.dis_all(code)
        genexpr = d.get_child("f").get_child("<genexpr>")
        retval = genexpr.opcodes[-1]
        self.assertEqual((retval.name, retval.line), ("RETURN_VALUE", 2))

    def test_method_calls(self):
        # Check that we assign line numbers correctly in 3.11
        # (regression test for https://github.com/google/pycnite/issues/15)
        path = base.test_pyc("method_calls", (3, 11))
        code = pyc.load_file(path)
        d = bytecode.dis_all(code)
        lines = [x.line for x in d.opcodes]
        chunks = [(0, 1), (1, 3), (2, 6), (3, 5), (4, 6), (5, 10)]
        expected = []
        for l, n in chunks:
            expected.extend([l] * n)
        self.assertEqual(lines, expected)

    def test_exception_table(self):
        def run(version):
            path = base.test_pyc("exception", version)
            code = pyc.load_file(path)
            dis = bytecode.dis_all(code)
            if version == (3, 11):
                self.assertTrue(dis.exception_table)
            else:
                self.assertFalse(dis.exception_table)

        for version in base.VERSIONS:
            run(version)
