#!/usr/bin/env bash

# Needed for proper Click module execution.
. /etc/profile.d/encoding.sh

ADDITIONAL_ARGS=( )

[[ -n "${KEYCLOAK_BASE_URL}" ]] || { echo "KEYCLOAK_BASE_URL not provided." ; exit 1 ; }
[[ -n "${KEYCLOAK_USERNAME}" ]] || { echo "KEYCLOAK_USERNAME not provided." ; exit 1 ; }
[[ -n "${KEYCLOAK_PASSWORD}" ]] || { echo "KEYCLOAK_PASSWORD not provided." ; exit 1 ; }
[[ -n "${DEPLOY_CONFIG_DIR}" ]] || { echo "DEPLOY_CONFIG_DIR not provided." ; exit 1 ; }
[[ -n "${DEPLOY_ENV}" ]] || { echo "DEPLOY_ENV not provided." ; exit 1 ; }

if [[ -n "${KEYCLOAK_TIMEOUT}" ]] ; then
    ADDITIONAL_ARGS=( "${ADDITIONAL_ARGS[@]}" "--keycloak-timeout" "${KEYCLOAK_TIMEOUT}" )
fi

if [[ -n "${ENCRYPTION_PREFIX}" ]] ; then
    ADDITIONAL_ARGS=( "${ADDITIONAL_ARGS[@]}" "--encryption-prefix" "${ENCRYPTION_PREFIX}" )
fi

if [[ -n "${AWS_PROFILE}" ]] ; then
    ADDITIONAL_ARGS=( "${ADDITIONAL_ARGS[@]}" "--aws-profile" "${AWS_PROFILE}" )
fi

keycloak-config-tool \
        --keycloak-base-url "${KEYCLOAK_BASE_URL}" \
        --keycloak-username "${KEYCLOAK_USERNAME}" \
        --keycloak-password "${KEYCLOAK_PASSWORD}" \
        --deploy-config-dir "${DEPLOY_CONFIG_DIR}" \
        --deploy-env "${DEPLOY_ENV}" \
        "${ADDITIONAL_ARGS[@]}"

if [[ -n "${COMPLETION_SIGNAL_PORT}" ]] ; then
    echo "==== Processing completed, listening on port ${COMPLETION_SIGNAL_PORT} to signal completion."
    nc -l ${COMPLETION_SIGNAL_PORT}
fi
