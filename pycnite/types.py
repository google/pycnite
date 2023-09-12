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

"""Basic datatypes for parsed pyc files."""

from dataclasses import dataclass

from typing import Any, List, Optional, Tuple, Union


@dataclass(kw_only=True)
class CodeTypeBase:
    """Pure python types.CodeType with python version added."""

    python_version: Tuple[int, int]
    co_argcount: int
    co_posonlyargcount: int
    co_kwonlyargcount: int
    co_stacksize: int
    co_flags: int
    co_code: bytes
    co_consts: List[object]
    co_names: List[str]
    co_filename: Union[bytes, str]
    co_name: int
    co_firstlineno: int

    def __repr__(self):
        return f"<code: {self.co_name}>"


@dataclass(kw_only=True)
class CodeType38(CodeTypeBase):
    """CodeType for python 3.8 - 3.10."""

    co_nlocals: int
    co_lnotab: bytes
    co_varnames: List[str]
    co_freevars: Tuple[str, ...]
    co_cellvars: Tuple[str, ...]


@dataclass(kw_only=True)
class CodeType311(CodeTypeBase):
    """CodeType for python 3.11+."""

    co_qualname: str
    co_localsplusnames: Tuple[str, ...]
    co_localspluskinds: Tuple[int, ...]
    co_linetable: bytes
    co_exceptiontable: bytes


@dataclass(kw_only=True)
class Opcode:
    """Opcode with names and line numbers."""

    index: int
    line: int
    op: int
    name: str
    arg: Optional[int]
    argval: Any

    def __str__(self):
        if self.arg is not None:
            return f"{self.line:>5}{self.index:>6}  {self.name:<30}{self.arg:>5} {self.argval}"
        else:
            return f"{self.line:>5}{self.index:>6}  {self.name:<30}"
