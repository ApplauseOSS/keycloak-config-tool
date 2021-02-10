#!/bin/bash -x

export CRYPTOGRAPHY_DONT_BUILD_RUST=1

# Install/run tox
pip install tox
tox

[[ $? != 0 ]] && exit 1

# Run tests via docker-compose
docker-compose up --build --exit-code-from keycloak_config
ret=$?
docker-compose down

exit $ret
