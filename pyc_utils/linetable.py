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

"""Line table reader."""

import abc
import dataclasses

from typing import List, Optional

from . import types


@dataclasses.dataclass(kw_only=True)
class Entry:
    """Position information for an opcode."""

    index: int
    line: int
    # The following are new in 3.11
    endline: Optional[int] = None
    startcol: Optional[int] = None
    endcol: Optional[int] = None


class LineTableReader(abc.ABC):
    """State machine for decoding a pyc line table."""

    def __init__(self, code: types.CodeTypeBase):
        self.lineno = code.co_firstlineno
        self.pos = 0

    @abc.abstractmethod
    def get(self, i: int) -> Entry:
        """Get position information for the instruction at the given position.

        This does NOT allow random access. Call with incremental numbers.

        Args:
          i: The byte position in the bytecode. i needs to stay constant or increase
            between calls.

        Returns:
          The line number corresponding to the position at i.
        """

    @abc.abstractmethod
    def read_all(self) -> List[Entry]:
        """Get all entries in the table.

        Mostly used for testing and debugging purposes.

        Returns:
          A list of entries parsed from the table.
        """


class LnotabReader(LineTableReader):
    """Read code.co_lnotab from pre-Python 3.11."""

    def __init__(self, code: types.CodeType38):
        super().__init__(code)
        self.linetable = code.co_lnotab
        if self.linetable:
            self.end_pos = len(self.linetable)
            self.next_addr = self.linetable[0]
        else:
            self.end_pos = 0
            self.next_addr = 0

    def read_all(self) -> List[Entry]:
        ret = []
        i = 0
        while self.pos < self.end_pos:
            ret.append(self.get(i))
            i = self.next_addr
        return ret


class LineTableReader38(LnotabReader):
    """Read code.co_lnotab from pre-Python 3.10."""

    def get(self, i: int) -> Entry:
        while i >= self.next_addr and self.pos < self.end_pos:
            line_diff = self.linetable[self.pos + 1]
            if line_diff >= 0x80:
                line_diff -= 0x100
            self.lineno += line_diff

            self.pos += 2
            if self.pos < self.end_pos:
                self.next_addr += self.linetable[self.pos]
        return Entry(index=i, line=self.lineno)


class LineTableReader310(LnotabReader):
    """Read code.co_lnotab from Python 3.10."""

    def __init__(self, code: types.CodeType38):
        super().__init__(code)
        if self.linetable:
            self.lineno += self.line_delta

    @property
    def line_delta(self):
        line_delta = self.linetable[self.pos + 1]
        if line_delta == 128:
            line_delta = 0
        elif line_delta > 128:
            line_delta -= 256
        return line_delta

    def get(self, i: int) -> Entry:
        while i >= self.next_addr and self.pos < self.end_pos:
            self.pos += 2
            if self.pos < self.end_pos:
                self.next_addr += self.linetable[self.pos]
                self.lineno += self.line_delta
        return Entry(index=i, line=self.lineno)


class PyCodeLocation:
    """Enum used in the 3.11 line table reader."""

    INFO_SHORT0 = 0
    INFO_ONE_LINE0 = 10
    INFO_ONE_LINE1 = 11
    INFO_ONE_LINE2 = 12
    INFO_NO_COLUMNS = 13
    INFO_LONG = 14
    INFO_NONE = 15


class LineTableReader311(LineTableReader):
    """Read code.co_linetable for Python 3.11+"""

    def __init__(self, code: types.CodeType311):
        super().__init__(code)
        self.linetable = code.co_linetable
        self.start = code.co_firstlineno
        self.end = self.start
        self.line = self.start
        self.end_pos = len(self.linetable)

    def _read_byte(self):
        b = self.linetable[self.pos]
        self.pos += 1
        return b

    def _read_varint(self):
        read = self._read_byte()
        val = read & 63
        shift = 0
        while read & 64:
            read = self._read_byte()
            shift += 6
            val |= (read & 63) << shift
        return val

    def _read_signed_varint(self):
        uval = self._read_varint()
        if uval & 1:
            return -(uval >> 1)
        else:
            return uval >> 1

    def read(self):
        b = self._read_byte()
        code = (b >> 3) & 15
        self.start = self.end
        self.end = self.start + (b & 7) + 1
        if code == PyCodeLocation.INFO_NONE:
            self.line = -1
            endline = -1
            col = -1
            endcol = -1
        elif code == PyCodeLocation.INFO_LONG:
            self.line += self._read_signed_varint()
            endline = self.line + self._read_varint()
            col = self._read_varint() - 1
            endcol = self._read_varint() - 1
        elif code == PyCodeLocation.INFO_NO_COLUMNS:
            self.line += self._read_signed_varint()
            endline = self.line + self._read_varint()
            col = -1
            endcol = -1
        elif code in (
            PyCodeLocation.INFO_ONE_LINE0,
            PyCodeLocation.INFO_ONE_LINE1,
            PyCodeLocation.INFO_ONE_LINE2,
        ):
            self.line += code - 10
            endline = self.line
            col = self._read_byte()
            endcol = self._read_byte()
        else:
            b2 = self._read_byte()
            assert b2 & 128 == 0
            endline = self.line
            col = (code << 3) | (b2 >> 4)
            endcol = col + (b2 & 15)
        return (endline, col, endcol)

    def get(self, i: int) -> Entry:
        endline, startcol, endcol = self.read()
        return Entry(
            index=i, line=self.line, endline=endline, startcol=startcol, endcol=endcol
        )

    def read_all(self):
        ret = []
        i = 0
        while self.pos < self.end_pos:
            ret.append(self.get(i))
            i = self.start * 2
        return ret


def linetable_reader(code: types.CodeTypeBase) -> LineTableReader:
    if code.python_version < (3, 10):
        assert isinstance(code, types.CodeType38)
        return LineTableReader38(code)
    elif code.python_version == (3, 10):
        assert isinstance(code, types.CodeType38)
        return LineTableReader310(code)
    else:
        assert isinstance(code, types.CodeType311)
        return LineTableReader311(code)
