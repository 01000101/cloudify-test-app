#!/bin/bash

set -e

mkdir -p /tmp/keys
ctx logger info "Generating Oracle RAC SSH keys..."
ssh-keygen -b 2048 -t rsa -N "" -f /tmp/oracle.key
ctx logger info "Printing node properties..."
ctx logger info "$(ctx node properties)"
ctx logger info "Printing instance properties..."
ctx logger info "$(ctx instance runtime_properties)"
ctx logger info "Exiting script"
