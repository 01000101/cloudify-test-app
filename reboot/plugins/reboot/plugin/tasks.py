"""Reboot Plugin

This plugin is used to allow for graceful rebooting of dependent instances
"""

import os
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

def spinUntilRebootStart(nova_client, server_id, timeout=120, sleep_interval=1):
    ctx.logger.info('Waiting for {0} to start rebooting (timeout={1}, interval={2}s)' . format(
        server_id,
        timeout,
        sleep_interval
    ))
    
    # Spin until it goes down and reports back up
    for i in range(1, timeout, 1):
        # Query the server details
        server = nova_client.servers.get(server_id)
        
        # If it's not in REBOOT state, it hasn't started rebooting yet
        if server.status == 'REBOOT':
            ctx.logger.info('[{0}/{1}, STATUS:{2}] {3} has started rebooting' . format(
                i,
                timeout,
                server.status,
                server_id
            ))
            
            break
        else:
            ctx.logger.info('[{0}/{1}, STATUS:{2}] Waiting for {3} to start rebooting' . format(
                i,
                timeout,
                server.status,
                server_id
            ))
        
        # Sleep
        sleep(sleep_interval)
        
    NonRecoverableError('Timed out waiting for {0} to start rebooting' . format(server_id))

def spinUntilRebootEnd(nova_client, server_id, timeout=120, sleep_interval=1):
    ctx.logger.info('Waiting for {0} to finish rebooting (timeout={1}, interval={2}s)' . format(
        server_id,
        timeout,
        sleep_interval
    ))
    
    # Spin until it goes down and reports back up
    for i in range(1, timeout, 1):
        # Query the server details
        server = nova_client.servers.get(server_id)
        
        # If it's not in ACTIVE state, it hasn't finished rebooting yet
        if server.status == 'ACTIVE':
            ctx.logger.info('[{0}/{1}, STATUS:{2}] {3} has finished rebooting' . format(
                i,
                timeout,
                server.status,
                server_id
            ))
            
            break
        else:
            ctx.logger.info('[{0}/{1}, STATUS:{2}] Waiting for {3} to finish rebooting' . format(
                i,
                timeout,
                server.status,
                server_id
            ))
        
        # Sleep
        sleep(sleep_interval)
        
    NonRecoverableError('Timed out waiting for {0} to finish rebooting' . format(server_id))

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
        
        # Get a server with the specified IP
        servers = nova_client.servers.list(
            detailed = False,
            search_opts = {
                'ip': rebootAgent['ip'] 
            }
        )
        
        # If no servers (or... too many?) were returned, skip this one
        if len(servers) != 1:
            ctx.logger.info('Missing, or too many, results returned for server {0}' . format(
                rebootAgent['ip']
            ))
            ctx.logger.info('Skipping {0}' . format(
                rebootAgent['ip']
            ))
            continue
        
        server = servers[0]
        
        # Reboot the server
        ctx.logger.info('Rebooting {0}' . format(rebootAgent['ip']))
        server.reboot()
        spinUntilRebootStart(nova_client, server.id)
        spinUntilRebootEnd(nova_client, server.id)
        
        
    # Sleep... ZZzzz
    ctx.logger.info('Sleeping for 120 seconds to let servers finish post-boot tasks')
    sleep(120)
