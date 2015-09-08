#!/bin/bash

set -e

function download() {
   url=$1
   name=$2

   if [ -f "`pwd`/${name}" ]; then
        ctx logger info "`pwd`/${name} already exists, No need to download"
   else
        # download to given directory
        ctx logger info "Downloading ${url} to `pwd`/${name}"

        set +e
        curl_cmd=$(which curl)
        wget_cmd=$(which wget)
        set -e

        if [[ ! -z ${curl_cmd} ]]; then
            curl -L -o ${name} ${url}
        elif [[ ! -z ${wget_cmd} ]]; then
            wget -O ${name} ${url}
        else
            ctx logger error "Failed to download ${url}: Neither 'cURL' nor 'wget' were found on the system"
            exit 1;
        fi
   fi
}

function untar() {
    tar_archive=$1
    destination=$2

    inner_name=$(tar -tf "${tar_archive}" | grep -o '^[^/]\+' | sort -u)

    if [ ! -d ${destination} ]; then
        ctx logger info "Untaring ${tar_archive}"
        tar -zxvf ${tar_archive}

        ctx logger info "Moving ${inner_name} to ${destination}"
        mv ${inner_name} ${destination}
    fi
}

TEMP_DIR="/tmp/$(ctx execution-id)"
NODEJS_PKG_NAME='node-v0.10.26-linux-x64.tar.gz'
NODEJS_PKG_URI="http://nodejs.org/dist/v0.10.26/${NODEJS_PKG_NAME}"
NODEJS_BIN_DIR="${TEMP_DIR}/nodejs-binaries"

ctx logger info "Creating directory ${TEMP_DIR}..."
mkdir -p ${TEMP_DIR}

ctx logger info "Changing working directory to ${TEMP_DIR}..."
cd ${TEMP_DIR}

# Download & unpack Node.js binaries
ctx logger info "Downloading Node.js package from ${NODEJS_PKG_URI}"
download ${NODEJS_PKG_URI} ${NODEJS_PKG_NAME}
ctx logger info "Extracting ${NODEJS_PKG_NAME} to ${NODEJS_BIN_DIR}"
untar ${NODEJS_PKG_NAME} ${NODEJS_BIN_DIR}

# Set our global properties
ctx instance runtime_properties nodejs_application_path ${TEMP_DIR}
ctx instance runtime_properties nodejs_binaries_path ${NODEJS_BIN_DIR}
ctx logger info "Sucessfully installed Node.js binaries"