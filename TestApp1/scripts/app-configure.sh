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

function extract() {
    archive=$1
    destination=$2

    if [ ! -d ${destination} ]; then

        if [[ ${archive} == *".zip"* ]]; then

            set +e
            unzip_cmd=$(which unzip)
            set -e

            if [[ -z ${unzip_cmd} ]]; then
                ctx logger error "Cannot extract ${archive}: 'unzip' command not found"
                exit 1
            fi
            inner_name=$(unzip -qql "${archive}" | sed -r '1 {s/([ ]+[^ ]+){3}\s+//;q}')
            ctx logger info "Unzipping ${archive}"
            unzip ${archive}

            ctx logger info "Moving ${inner_name} to ${destination}"
            mv ${inner_name} ${destination}

        else

            # assuming tarball if the archive is not a zip.
            # we dont check that tar exists since if we made it
            # this far, it definitely exists (nodejs used it)
            inner_name=$(tar -tf "${archive}" | grep -o '^[^/]\+' | sort -u)
            ctx logger info "Untaring ${archive}"
            tar -zxvf ${archive}

            ctx logger info "Moving ${inner_name} to ${destination}"
            mv ${inner_name} ${destination}

        fi
    fi
}

NODEJS_BINARIES_PATH=$(ctx instance runtime_properties nodejs_binaries_path)
NODEJS_APP_PATH=$(ctx instance runtime_properties nodejs_application_path)

APPLICATION_URI=$(ctx node properties application_uri)
APPLICATION_ROOT=${NODEJS_APP_PATH}/$(ctx node properties application_root)
AFTER_SLASH=${APPLICATION_URI##*/}
APP_ARCHIVE_NAME=${AFTER_SLASH%%\?*}

ctx logger info "Downloading application from ${APPLICATION_URI}"
download $(ctx instance properties application_uri) ${APP_ARCHIVE_NAME}
ctx logger info "Extracting application into ${NODEJS_APP_PATH}"
extract ${APP_ARCHIVE_NAME} ${NODEJS_APP_PATH}

ctx logger info "Changing directory to ${APPLICATION_ROOT}"
cd ${APPLICATION_ROOT}

ctx logger info "Installing application dependencies using npm"
${NODEJS_BINARIES_PATH}/bin/npm install --save-dev
ctx logger info "Sucessfully installed nodecellar"