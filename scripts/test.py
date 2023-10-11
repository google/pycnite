"""Run various pycnite functions manually over a file, for quick testing."""

import compileall
import os
import sys

from pycnite import bytecode
from pycnite import linetable
from pycnite import pyc


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


def run(src_file):
    code = compile_pyc(src_file)
    d = bytecode.dis_all(code)
    d.pretty_print()
    lt = linetable.linetable_reader(code)


if __name__ == "__main__":
    src_file = sys.argv[1]
    run(src_file)
