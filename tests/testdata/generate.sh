#!/bin/bash

# Requires pyenv to be installed and activated in your shell

# Install python versions if required

versions=('3.8' '3.9' '3.10' '3.11')

for version in "${versions[@]}"
do
  pyenv install -s "$version"
done

# Generate pyc files
for version in "${versions[@]}"
do
  pyenv local "$version"
  python --version
  python -m compileall src
  suffix="cpython-$(echo $version | tr -d '.').pyc"
  mv src/__pycache__/*.$suffix $version
done
