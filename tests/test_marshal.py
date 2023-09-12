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

"""Tests for marshal.py."""

import unittest

from pycnite import marshal


class Base(unittest.TestCase):
    """Base class for marshal reader tests."""

    def assertStrictEqual(self, s1, s2):
        self.assertEqual(s1, s2)
        self.assertEqual(type(s1), type(s2))

    def load(self, s, python_version=None):
        python_version = python_version or (3, 9)
        return marshal.loads(s, python_version)


class TestMarshalReader(Base):
    """Tests for marshal reader."""

    def test_load_none(self):
        self.assertIsNone(self.load(b"N"))

    def test_load_false(self):
        self.assertEqual(self.load(b"F"), False)

    def test_load_true(self):
        self.assertEqual(self.load(b"T"), True)

    def test_load_stopiter(self):
        self.assertEqual(self.load(b"S"), StopIteration)

    def test_load_ellipsis(self):
        self.assertEqual(self.load(b"."), Ellipsis)

    def test_load_int(self):
        self.assertEqual(self.load(b"i\1\2\3\4"), 0x04030201)
        self.assertEqual(self.load(b"i\xff\xff\xff\xff"), -1)

    def test_load_int64(self):
        self.assertEqual(self.load(b"I\1\2\3\4\5\6\7\x08"), 0x0807060504030201)
        self.assertEqual(self.load(b"I\xff\xff\xff\xff\xff\xff\xff\xff"), -1)

    def test_load_float(self):
        self.assertEqual(self.load(b"f\x040.25"), 0.25)

    def test_load_long_float(self):
        self.assertEqual(self.load(b"f\xff0." + (b"9" * 253)), 1.0)

    def test_load_binary_float(self):
        self.assertEqual(self.load(b"g\0\0\0\0\0\0\xd0\x3f"), 0.25)

    def test_load_complex(self):
        self.assertEqual(self.load(b"x\3.25\3.25"), 0.25 + 0.25j)

    def test_load_binary_complex(self):
        c = self.load(b"y\0\0\0\0\0\0\xf0\x3f\0\0\0\0\0\0\xf0\x3f")
        self.assertEqual(c, 1 + 1j)

    def test_load_long(self):
        """Load a variable length integer."""
        self.assertEqual(
            self.load(b"l\3\0\0\0\1\0\2\0\3\0"), 1 + 2 * 2**15 + 3 * 2**30
        )
        self.assertEqual(self.load(b"l\xff\xff\xff\xff\1\0"), -1)
        self.assertEqual(self.load(b"l\xfe\xff\xff\xff\1\0\2\0"), -65537)

    def test_load_string(self):
        self.assertStrictEqual(
            self.load(b"s\4\0\0\0test", (3, 9)), bytes(b"test")
        )

    def test_load_interned(self):
        self.assertStrictEqual(self.load(b"t\4\0\0\0test"), "test")

    def test_load_stringref(self):
        st = (
            b"(\4\0\0\0"  # tuple of 4
            b"t\4\0\0\0abcd"  # store "abcd" at 0
            b"t\4\0\0\0efgh"  # store "efgh" at 1
            b"R\0\0\0\0"  # retrieve stringref 0
            b"R\1\0\0\0"
        )  # retrieve stringref 1
        self.assertEqual(self.load(st), ("abcd", "efgh", "abcd", "efgh"))

    def test_load_tuple(self):
        self.assertEqual(self.load(b"(\2\0\0\0TF"), (True, False))

    def test_load_list(self):
        self.assertEqual(self.load(b"[\2\0\0\0TF"), [True, False])

    def test_load_dict(self):
        self.assertEqual(self.load(b"{TFFN0"), {True: False, False: None})

    def test_load_unicode(self):
        self.assertStrictEqual(self.load(b"u\4\0\0\0test", (3, 9)), "test")
        # This character is \u00e4 (umlaut a).
        s = b"u\2\0\0\0\xc3\xa4"
        self.assertStrictEqual(self.load(s, (3, 9)), "\xe4")

    def test_load_set(self):
        self.assertEqual(self.load(b"<\3\0\0\0FTN"), {True, False, None})

    def test_load_frozenset(self):
        self.assertEqual(
            self.load(b">\3\0\0\0FTN"), frozenset([True, False, None])
        )

    def test_load_ref(self):
        data = (
            b"(\4\0\0\0"  # tuple of 4
            b"\xe9\0\1\2\3"  # store 0x03020100 at 0
            b"\xe9\4\5\6\7"  # store 0x07060504 at 1
            b"r\0\0\0\0"  # retrieve 0
            b"r\1\0\0\0"
        )  # retrieve 1
        self.assertEqual(
            self.load(data), (0x03020100, 0x7060504, 0x03020100, 0x7060504)
        )

    def test_load_ascii(self):
        self.assertStrictEqual(self.load(b"a\4\0\0\0test"), "test")

    def test_load_ascii_interned(self):
        self.assertStrictEqual(self.load(b"A\4\0\0\0test"), "test")

    def test_load_small_tuple(self):
        self.assertEqual(self.load(b")\2TF"), (True, False))

    def test_load_short_ascii(self):
        self.assertStrictEqual(self.load(b"z\4test"), "test")

    def test_load_short_ascii_interned(self):
        self.assertStrictEqual(self.load(b"Z\4test"), "test")

    def test_truncated(self):
        self.assertRaises(EOFError, lambda: self.load(b"f\x020"))

    def test_trailing(self):
        self.assertRaises(BufferError, lambda: self.load(b"N\0"))

    def test_illegal(self):
        self.assertRaises(ValueError, lambda: self.load(b"\7"))

    def test_truncated_byte(self):
        self.assertRaises(EOFError, lambda: self.load(b"f"))


class TestCodeReader(Base):
    """Tests for marshal code reader."""

    def test_code_3_8(self):
        # Code from marshal.dumps of
        #   def f():
        #     x = 10
        #     def g():
        #       return x
        #     return g
        bytecode = (
            b"\xe3\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00"
            b"\x00\x03\x00\x00\x00\x03\x00\x00\x00s\x14\x00\x00\x00d\x01\x89"
            b"\x00\x87\x00f\x01d\x02d\x03\x84\x08}\x02|\x02S\x00)\x04N\xe9\n"
            b"\x00\x00\x00c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x01\x00\x00\x00\x13\x00\x00\x00s\x04\x00\x00"
            b"\x00\x88\x00S\x00)\x01N\xa9\x00r\x02\x00\x00\x00\xa9\x01\xda"
            b"\x01xr\x02\x00\x00\x00\xfa\x1e<ipython-input-1-fe7579e34ce2>"
            b"\xda\x01g\x03\x00\x00\x00s\x02\x00\x00\x00\x04\x01z\x0c"
            b"f.<locals>.gr\x02\x00\x00\x00)\x03\xda\x01a\xda\x01br\x06\x00"
            b"\x00\x00r\x02\x00\x00\x00r\x03\x00\x00\x00r\x05\x00\x00\x00\xda"
            b"\x01f\x01\x00\x00\x00s\x06\x00\x00\x00\x04\x01\x0c\x01\x04\x02"
        )
        code = marshal.loads(bytecode, (3, 10))
        self.assertEqual(code.co_argcount, 1)
        self.assertEqual(code.co_kwonlyargcount, 1)
        self.assertEqual(code.co_nlocals, 3)
        self.assertEqual(code.co_stacksize, 3)
        self.assertEqual(code.co_flags, 3)
        self.assertEqual(code.co_names, ())
        self.assertEqual(
            code.co_varnames,
            (
                "a",
                "b",
                "g",
            ),
        )
        self.assertEqual(code.co_freevars, ())
        self.assertEqual(code.co_cellvars, ("x",))

    def test_code_3_11(self):
        # Code from marshal.dumps of
        #   def f(a, *, b):
        #     x = 10
        #     def g():
        #       return x
        #     return g
        bytecode = (
            b"\xe3\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00"
            b"\x00\x00\x03\x00\x00\x00\xf3\x16\x00\x00\x00\x87\x03\x97\x00d"
            b"\x01\x8a\x03\x88\x03f\x01d\x02\x84\x08}\x02|\x02S\x00)\x03N\xe9"
            b"\n\x00\x00\x00c\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x01\x00\x00\x00\x13\x00\x00\x00\xf3\x08\x00\x00\x00\x95\x01\x97"
            b"\x00\x89\x00S\x00)\x01N\xa9\x00)\x01\xda\x01xs\x01\x00\x00\x00"
            b"\x80\xfa\x1e<ipython-input-2-fe7579e34ce2>\xda\x01gz\x0c"
            b"f.<locals>.g\x03\x00\x00\x00s\x08\x00\x00\x00\xf8\x80\x00\xd8"
            b"\x0f\x10\x88\x08\xf3\x00\x00\x00\x00r\x04\x00\x00\x00)\x04\xda"
            b"\x01a\xda\x01br\x07\x00\x00\x00r\x05\x00\x00\x00s\x04\x00\x00"
            b"\x00   @r\x06\x00\x00\x00\xda\x01fr\x0b\x00\x00\x00\x01\x00\x00"
            b"\x00s&\x00\x00\x00\xf8\x80\x00\xd8\x08\n\x80A\xf0\x02\x01\x05"
            b"\x11\xf0\x00\x01\x05\x11\xf0\x00\x01\x05\x11\xf0\x00\x01\x05\x11"
            b"\xf0\x00\x01\x05\x11\xe0\x0b\x0c\x80Hr\x08\x00\x00\x00"
        )
        code = marshal.loads(bytecode, (3, 11))
        self.assertEqual(code.co_argcount, 1)
        self.assertEqual(code.co_kwonlyargcount, 1)
        self.assertEqual(code.co_stacksize, 2)
        self.assertEqual(code.co_flags, 3)
        self.assertEqual(code.co_names, ())


if __name__ == "__main__":
    unittest.main()
