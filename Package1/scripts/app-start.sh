#!/bin/bash

set -e

function get_response_code() {

    port=$1

    set +e

    curl_cmd=$(which curl)
    wget_cmd=$(which wget)

    if [[ ! -z ${curl_cmd} ]]; then
        response_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${port})
    elif [[ ! -z ${wget_cmd} ]]; then
        response_code=$(wget --spider -S "http://localhost:${port}" 2>&1 | grep "HTTP/" | awk '{print $2}' | tail -1)
    else
        ctx logger error "Failed to retrieve response code from http://localhost:${port}: Neither 'cURL' nor 'wget' were found on the system"
        exit 1;
    fi

    set -e

    echo ${response_code}

}

function wait_for_server() {

    port=$1
    server_name=$2

    started=false

    ctx logger info "Running ${server_name} liveness detection on port ${port}"

    for i in $(seq 1 120)
    do
        response_code=$(get_response_code ${port})
        ctx logger info "[GET] http://localhost:${port} ${response_code}"
        if [ ${response_code} -eq 200 ] ; then
            started=true
            break
        else
            ctx logger info "${server_name} has not started. waiting..."
            sleep 1
        fi
    done
    if [ ${started} = false ]; then
        ctx logger error "${server_name} failed to start. waited for a 120 seconds."
        exit 1
    fi
}

ctx logger info "Updating the platform..."
sudo apt-get update
sudo apt-get upgrade -y
ctx logger info "Updates applied"
ctx logger info "Rebooting..."
sudo shutdown -r now
ctx logger info "Reboot completed"


NODEJS_BINARIES_PATH=$(ctx instance runtime_properties nodejs_binaries_path)
NODEJS_APP_PATH=$(ctx instance runtime_properties nodejs_application_path)

# This is used by the application itself
export APP_PORT=$(ctx node properties port)

ctx logger info "Starting Node.js application on port ${APP_PORT}"
COMMAND="${NODEJS_BINARIES_PATH}/bin/node ${NODEJS_APP_PATH}/server.js"

ctx logger info "${COMMAND}"
nohup ${COMMAND} > /dev/null 2>&1 &
PID=$!

wait_for_server ${APP_PORT} 'nodejs_application'

# this runtime porperty is used by the app-stop.sh script.
ctx instance runtime_properties pid ${PID}

ctx logger info "Sucessfully started the Node.js application (${PID})"