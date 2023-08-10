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

"""Base module for unit tests."""

import os

DATADIR = os.path.join(os.path.dirname(__file__), "testdata")

VERSIONS = ((3, 8), (3, 9), (3, 10), (3, 11))


def test_file(filename, version):
    version = ".".join(map(str, version))
    return os.path.join(DATADIR, version, filename)


def test_pyc(prefix, version):
    v = "".join(map(str, version))
    filename = f"{prefix}.cpython-{v}.pyc"
    return test_file(filename, version)
