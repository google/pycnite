"""Diff pycnite's disassembly against cpython's dis to verify the output."""

import compileall
from dataclasses import dataclass
import difflib
import dis
import os
import sys

from typing import List

# Make sure we import from the local copy of pycnite
sys.path = [os.path.dirname(os.path.dirname(__file__))] + sys.path

from pycnite import bytecode
from pycnite import linetable
from pycnite import pyc
from pycnite import types


@dataclass
class CodeTree:
    name: str
    line: int
    opcodes: List[types.Opcode]
    children: "List[CodeTree]"


def compile_pyc(src_file):
    compileall.compile_file(src_file)
    with open(src_file, "r") as f:
        src = f.readlines()
    base = os.path.basename(src_file)
    base = os.path.splitext(base)[0]
    version = "".join(str(x) for x in sys.version_info[:2])
    path = f"__pycache__/{base}.cpython-{version}.pyc"
    code = pyc.load_file(path)
    return code


def opcodes_from_dis(code, filename):
    bc = dis.Bytecode(code)
    ret = []
    lineno = code.co_firstlineno
    for ins in bc:
        if ins.starts_line is not None:
            lineno = ins.starts_line
        ret.append(
            types.Opcode(
                offset=ins.offset,
                line=lineno,
                op=ins.opcode,
                name=ins.opname,
                arg=ins.arg,
                argval=ins.argval,
            )
        )
    return ret


def codetree_from_dis(code, filename):
    opcodes = opcodes_from_dis(code, filename)
    name = code.co_name
    line = code.co_firstlineno
    children = [
        codetree_from_dis(op.argval, filename)
        for op in opcodes
        if op.argval.__class__.__name__ == "code"
    ]
    return CodeTree(name=name, line=line, opcodes=opcodes, children=children)


def codetree_from_pycnite(dis_code):
    opcodes = dis_code.opcodes
    name = dis_code.code.co_name
    line = dis_code.code.co_firstlineno
    children = [codetree_from_pycnite(d) for d in dis_code.children]
    return CodeTree(name=name, line=line, opcodes=opcodes, children=children)


def diff_trees(tree1, tree2, indent=0):
    line = lambda o: f"{o.line:>5}{o.offset:>6}  {o.name}"
    t1 = [line(o) for o in tree1.opcodes]
    t2 = [line(o) for o in tree2.opcodes]
    diff = list(difflib.unified_diff(t1, t2))
    name = f"{tree1.line:>5} {' '*indent}{tree1.name}"
    if diff:
        print(f"FAILED: {name}")
        for d in diff:
            print("  ", d)
    else:
        print(f"PASSED: {name}")
    for c1, c2 in zip(tree1.children, tree2.children):
        diff_trees(c1, c2, indent=indent + 2)


def diff_against_python(src_file):
    # Compile and disassemble with python
    with open(src_file, "r") as f:
        src = f.read()
    bcode = compile(src, filename=src_file, mode="exec")
    python_tree = codetree_from_dis(bcode, src_file)

    # Compile and disassemble with pycnite
    code = compile_pyc(src_file)
    dis_code = bytecode.dis_all(code)
    pycnite_tree = codetree_from_pycnite(dis_code)

    # Run the diff
    diff_trees(python_tree, pycnite_tree)


def run(src_file):
    code = compile_pyc(src_file)
    d = bytecode.dis_all(code)
    # d.pretty_print()
    diff_against_python(src_file)


if __name__ == "__main__":
    src_file = sys.argv[1]
    run(src_file)
