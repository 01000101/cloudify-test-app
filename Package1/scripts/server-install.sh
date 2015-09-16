#!/bin/bash

set -e

mkdir -p /tmp/keys
ctx logger info "Generating Oracle RAC SSH keys..."
ssh-keygen -b 2048 -t rsa -N "" -f /tmp/oracle.key
ctx logger info "Exiting script"
