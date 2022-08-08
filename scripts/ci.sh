#!/bin/bash -x

export CRYPTOGRAPHY_DONT_BUILD_RUST=1

# Install/run tox
pip install tox
tox
