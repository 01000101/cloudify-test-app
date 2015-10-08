"""Reboot Plugin

This plugin is used to allow for graceful rebooting of dependent instances
"""

import os
import pprint
from time import sleep
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.decorators import operation
from openstack_plugin_common import with_nova_client

# Metadata
__author__ =     "Joshua Cornutt"
__copyright__ =  "Copyright 2015, Gigaspaces"
__license__ =    "Proprietary"
__maintainer__ = "Joshua Cornutt"
__email__ =      "josh@gigaspaces.com"
__status__ =     "Development"

# Globals
rebootAgents = []
        
# Find any dependent nodes of the Facilitator
def discoverDependents():
    node_list = []
    
    for rel in ctx.instance.relationships:
        if rel.type == 'cloudify.relationships.depends_on':
            node_list.append({
                'ip': rel.target.instance.host_ip,
                'reboot_started': False
            })
    
    return node_list

# Entry point for the Facilitator
@operation
@with_nova_client
def configure(nova_client, **kwargs):
    global rebootAgents
    
    # Get a handle to our OpenStack Nova connection
    ctx.logger.info('Discovering dependent nodes')
    rebootAgents = discoverDependents()
    
    # If less than 1 node was discovered, that's a problem...
    ctx.logger.info('{0} node(s) discovered' . format(len(rebootAgents)))
    if len(rebootAgents) < 1:
        raise NonRecoverableError('Reboot plugin requires at least 1 dependent node')

    # Populate an array of IPs
    for rebootAgent in rebootAgents:
        ctx.logger.info('Querying Nova for {0}' . format(
            rebootAgent['ip']
        ))
        
        servers = nova_client.servers.list(
            search_opts = {
                'ip': rebootAgent['ip'] 
            }
        )
        
        if len(servers) != 1:
            ctx.logger.info('Multiple results returned for server {0}' . format(
                rebootAgent['ip']
            ))
            ctx.logger.info('Skipping {0}' . format(
                rebootAgent['ip']
            ))
            continue
        
        server = servers[0]
        
        ctx.logger.info('Rebooting {0}' . format(rebootAgent['ip']))
        server.reboot()
            
        reboot_timeout = 30
        while reboot_timeout > 0:
            ctx.logger.info('Querying state of {0}' . format(rebootAgent['ip']))
            server = nova_client.servers.get(server.id)
            
            ctx.logger.info(pprint.pformat(
                vars(server)
            ))
            
            if server.status != 'ACTIVE':
                break
            else:
                reboot_timeout -= 1
                sleep(2)
        
        
    # Sleep... ZZzzz
    ctx.logger.info('Sleeping for 30 seconds')
    sleep(30)
