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

from pyc_utils import marshal


class TestMarshalReader(unittest.TestCase):
    """Tests for marshal reader."""

    def assertStrictEqual(self, s1, s2):
        self.assertEqual(s1, s2)
        self.assertEqual(type(s1), type(s2))

    def load(self, s, python_version=None):
        python_version = python_version or (3, 9)
        return marshal.loads(s, python_version)

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
        self.assertStrictEqual(self.load(b"s\4\0\0\0test", (3, 9)), bytes(b"test"))

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
        self.assertEqual(self.load(b">\3\0\0\0FTN"), frozenset([True, False, None]))

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


if __name__ == "__main__":
    unittest.main()
