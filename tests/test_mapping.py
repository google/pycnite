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

"""Tests for pycnite.mapping."""

import unittest

from pycnite import mapping


class TestMapping(unittest.TestCase):
  """Test opcode to name mapping."""

  def run_test(self, version, op, expected):
    opmap = mapping.get_mapping(version)
    self.assertEqual(opmap.get(op), expected)

  def test_versions(self):
    """Spot checks for a few opcodes."""
    self.run_test((3, 8), 9, "NOP")
    self.run_test((3, 9), 9, "NOP")
    self.run_test((3, 9), 53, None)
    self.run_test((3, 9), 117, "IS_OP")
    self.run_test((3, 10), 99, "ROT_N")
    self.run_test((3, 10), 48, None)
    self.run_test((3, 11), 0, "CACHE")
    self.run_test((3, 11), 6, None)
    self.run_test((3, 11), 9, "NOP")
    self.run_test((3, 11), 75, "RETURN_GENERATOR")
    self.run_test((3, 12), 121, "RETURN_CONST")
    self.run_test((3, 12), 150, "YIELD_VALUE")


if __name__ == "__main__":
    unittest.main()
