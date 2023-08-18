from dataclasses import dataclass

from typing import Iterable, List, Optional, Tuple

from . import linetable
from . import mapping
from . import types


# From cpython/Include/opcodes.h
HAVE_ARGUMENT = 90
EXTENDED_ARG = 144


@dataclass
class RawOpcode:
    """Opcode parsed from code.co_code."""

    start: int
    end: int
    op: int
    arg: Optional[int]


def wordcode_reader(data: bytes) -> Iterable[RawOpcode]:
    """Reads binary data from pyc files."""

    extended_arg = 0
    for pos in range(0, len(data), 2):
        op = data[pos]
        if op == EXTENDED_ARG:
            oparg = data[pos + 1] | extended_arg
            extended_arg = oparg << 8
        elif op >= HAVE_ARGUMENT:
            oparg = data[pos + 1] | extended_arg
            extended_arg = 0
        else:
            oparg = None
            extended_arg = 0
        # Don't yield EXTENDED_ARG; it is part of the next opcode.
        if op != EXTENDED_ARG:
            yield RawOpcode(pos, pos + 2, op, oparg)


def dis(code: types.CodeTypeBase) -> List[types.Opcode]:
    """Disassemble code."""
    lt = linetable.linetable_reader(code)
    opmap = mapping.get_mapping(code.python_version)
    ret = []
    for o in wordcode_reader(code.co_code):
        if o.op == 0:  # CACHE
            continue
        name = opmap[o.op]
        pos = lt.get(o.start)
        op = types.Opcode(index=o.start, name=name, line=pos.line, op=o.op, arg=o.arg)
        ret.append(op)
    return ret
