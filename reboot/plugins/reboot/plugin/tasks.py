"""Reboot Plugin

This plugin is used to allow for graceful rebooting of dependent instances
"""

import os
from time import sleep
import socket
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.decorators import operation

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
    sock = socket.socket()
    
    cfy_agent = ctx.node.properties.get('cloudify_agent', dict())
    agent_port = cfy_agent.get('remote_execution_port', ctx.bootstrap_context.cloudify_agent.remote_execution_port)
    
    try:
        sock.connect((agent['ip'], agent_port))
        sock.close()
        return True
    except:
        return False

# Entry point for the Facilitator
@operation
def configure(**kwargs):
    global rebootAgents
    
    ctx.logger.info('Discovering dependent nodes')
    rebootAgents = discoverDependents()
    
    # If less than 1 node was discovered, that's a problem...
    ctx.logger.info('{0} nodes discovered' . format(len(rebootAgents)))
    if len(rebootAgents) < 1:
        raise NonRecoverableError('Reboot plugin requires at least 1 dependent node')
    
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
            sleep(2)
    
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
