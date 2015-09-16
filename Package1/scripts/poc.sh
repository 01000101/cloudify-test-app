#!/bin/bash

set -e

ctx logger info "Printing environment variables..."
ctx logger info "$(env)"
ctx logger info "Printing node properties..."
ctx logger info "$(ctx node properties)"
ctx logger info "Printing instance properties..."
ctx logger info "$(ctx instance runtime_properties)"
ctx logger info "Exiting script"

for rel in ctx.instance.relationships:
    target_instance = rel.target
    ctx logger info "Printing relationship properties..."
    ctx logger info "${rel.target.runtime_properties}"
    ctx logger info "Printing relationship IP..."
    ctx logger info "${rel.target.runtime_properties['ip']}"
    target_ip = rel.target.runtime_properties['ip']