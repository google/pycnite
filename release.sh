#!/bin/bash

# Releases to PyPI. Run in a virtualenv with `build` and `twine` pip-installed.
# To upload a test release to TestPyPI:
#   ./release.sh test
# To upload a release to PyPI:
#   ./release.sh release

set -e

if [ "$#" -ne 1 ]; then
    printf 'missing release mode\n'
    false
elif [ "$1" = "test" ]; then
    test_release=true
elif [ "$1" = "release" ]; then
    test_release=false
else
    printf 'invalid release mode\n'
    false
fi

python -m build
if $test_release; then
    twine upload --repository testpypi dist/*
else
    twine upload dist/*
fi

rm -rf dist/
rm -rf pycnite.egg-info

if $test_release; then
  printf '\nTest release uploaded. Pip install command:'
  printf '\npip install -U --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple pycnite\n'
else
  printf '\nRelease uploaded.\n'
fi
