#!/bin/bash

set -e

ctx logger info "Printing environment variables..."
ctx logger info "$(env)"
ctx logger info "Printing node properties..."
ctx logger info "$(ctx node properties)"
ctx logger info "Printing instance properties..."
ctx logger info "$(ctx instance runtime_properties)"
ctx logger info "Exiting script"

