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

"""Tests for pycnite.magic."""

import unittest

from . import base
from pycnite import magic


class TestMagic(unittest.TestCase):
    """Test magic number parsing."""

    def test_version(self):
        for version in base.VERSIONS:
            path = base.test_pyc("basic", version)
            with open(path, "rb") as f:
                magic_number = f.read(2)
            self.assertEqual(
                version, magic.magic_number_to_version(magic_number)
            )


if __name__ == "__main__":
    unittest.main()
