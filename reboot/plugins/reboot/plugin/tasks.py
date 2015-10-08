"""Reboot Plugin

This plugin is used to allow for graceful rebooting of dependent instances
"""

import os
from time import sleep
import socket
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

# Connect to server, return True on success / False on error
def agentIsAlive(agent):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    cfy_agent = ctx.node.properties.get('cloudify_agent', dict())
    agent_port = cfy_agent.get('remote_execution_port', ctx.bootstrap_context.cloudify_agent.remote_execution_port)
    
    ctx.logger.info('Connecting to {0}:{1}' . format(agent['ip'], agent_port))
    
    try:
        err = sock.connect_ex((agent['ip'], agent_port))
        sock.close()
        
        ctx.logger.info('  connect_ex(): {0}' . format(err))
        return True
    except socket.error as err:
        ctx.logger.info('  connect_ex(EXCEPTION): {0}' . format(err))
        return False

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
        ctx.logger.info('Querying Nova for {0}' . format(rebootAgent['ip']))
        
        servers = nova_client.servers.list(
            search_opts = {
                'ip': rebootAgent['ip'] 
            }
        )
        
        ctx.logger.info('Nova returned {0} results: {1}' . format(
            len(servers),
            servers
        ))
        
        if len(servers) > 0:
            for server in servers:
                ctx.logger.info(' Properties: {0}' . format(
                    vars(server)
                ))
            
                ctx.logger.info('Rebooting {0}' . format(rebootAgent['ip']))
                server.reboot()
                
                while server.status == 'ACTIVE':
                    ctx.logger.info(' Properties: {0}' . format(
                        vars(server)
                    ))
                    
                    sleep(5)
        else:
            ctx.logger.info('{0} was not found' . format(rebootAgent['ip']))
    
    # Wait for all systems to go dark
    if ctx.operation.retry_number == 0:
        agents_rebooted = 0
        
        # Print out the agents
        for rebootAgent in rebootAgents:
            ctx.logger.info(' IP: {0}' . format(rebootAgent['ip']))
            
        # Spin until all agents have stopped responding (started rebooting)
        while agents_rebooted < len(rebootAgents):
            for rebootAgent in rebootAgents:
                if not rebootAgent['reboot_started']:
                    if not agentIsAlive(rebootAgent):
                        ctx.logger.info('{0} has started rebooting' . format(rebootAgent['ip']))
                        rebootAgent['reboot_started'] = True
                        agents_rebooted += 1
                    else:
                        ctx.logger.info('{0} has not yet started rebooting' . format(rebootAgent['ip']))
            sleep(1)
    
    # Spin until all agents have started responding again (finished rebooting)
    for rebootAgent in rebootAgents:
        if not agentIsAlive(rebootAgent):
            return ctx.operation.retry(
                message = '{0} is still rebooting' . format(rebootAgent['ip']),
                retry_after = 10
            )
        else:
            ctx.logger.info('{0} has finished rebooting' . format(rebootAgent['ip']))

    # Sleep... ZZzzz
    ctx.logger.info('Sleeping for 30 seconds')
    sleep(30)
