#!/bin/bash

set -e

NODEJS_BINARIES_PATH=$(ctx instance runtime_properties nodejs_binaries_path)
NODEJS_APP_PATH=$(ctx instance runtime_properties nodejs_application_path)

ctx logger info "NODEJS_BINARIES_PATH: ${NODEJS_BINARIES_PATH}"
ctx logger info "NODEJS_APP_PATH: ${NODEJS_APP_PATH}"

ctx download-resource 'app/package.json' "${NODEJS_APP_PATH}/package.json"
ctx download-resource 'app/server.js' "${NODEJS_APP_PATH}/server.js"

cd ${NODEJS_APP_PATH}

ctx logger info "Installing application dependencies using npm"
${NODEJS_BINARIES_PATH}/bin/npm install --save-dev
ctx logger info "Sucessfully installed nodecellar"