import os
import tempfile
import subprocess
from fabric.api import *
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.decorators import operation

# Globals
XCHG_RESULT = []
xchgAgents = []
        
# Find any dependent nodes to retrieve keys from
def discoverDependents():
    node_list = []
    
    for rel in ctx.instance.relationships:
        if rel.type == 'cloudify.relationships.depends_on':
            node_list.append({
                'ip': rel.target.instance.host_ip,
                'key_path_remote': rel.target.instance.runtime_properties['key_path'] + '.pub'
            })
    
    return node_list

# This function retrieves the public key from the remote server,
# updates XCHG_NODES, and cleans up
def retrievePublicKey():
    ctx.logger.info("Executing on {0} as {1}" . format(env.host, env.user))
    
    # Find ourselves...
    for idx, xchgAgent in xchgAgents:
        if xchgAgent['ip'] == env.host:
            # Generate temporary file
            fd, sPath = tempfile.mkstemp()
            with os.fdopen(fd, 'w+') as temp_file:
                # Copy the remote public key to the temporary file
                ctx.logger.info('fabric.operations.get({0}, {1})' . format(xchgAgent['key_path_remote'], sPath))
                get(xchgAgent['key_path_remote'], temp_file)
                
                # Log where we stashed the public key
                xchgAgents[idx]['key_path_local'] = sPath
            
            return

# This function faciliates the exchange of keys between servers
def exchangePublicKeys():
    global XCHG_RESULT
    global xchgAgents
    exchanges = []
    
    ctx.logger.info("Executing on {0} as {1}" . format(env.host, env.user))
    
    # Find ourselves...
    for idxTo, xchgAgentTo in xchgAgents:
        if xchgAgent['ip'] == env.host:
            # Iterate through all nodes (except for ourself)
            for xchgAgentFrom in xchgAgents:
                if xchgAgentFrom['ip'] != xchgAgentTo['ip']:
                    ctx.logger.info('Moving public key from {0} to {1}' . format(
                        xchgAgentFrom['ip'],
                        xchgAgentTo['ip']
                    ))
                
                    # Copy the public key from local to a remote node
                    res = put(nxchgAgentFrom['key_path_local'], '/tmp/')
                    
                    ctx.logger.info(' -> file moved to {0}:{1}' . format(
                        xchgAgentTo['ip'],
                        res[0]
                    ))
                    
                    # Log the exchange (from IP, public key path)
                    exchanges.append({
                        'from': xchgAgentFrom['ip'],
                        'key_path': res[0]
                    })
    
            # Log the entire exchange for this node to the outputs list
            XCHG_RESULT.append({
                'to': xchgAgentTo['ip'],
                'exchanges': exchanges
            })


@operation
def configure(**kwargs):
    global XCHG_NODES
    global xchgAgents
    env.hosts = []
    
    ctx.logger.info('Discovering dependent nodes')
    xchgAgents = discoverDependents()
    
    # If less than 2 nodes were discovered, that's a problem...
    ctx.logger.info('{0} nodes discovered' . format(len(xchgAgents)))
    if len(xchgAgents) < 2:
        raise NonRecoverableError("Exchange plugin requires at least 2 dependent nodes")
    
    # Add each found node IP to the Fabric hosts list
    for xchgAgent in xchgAgents:
        ctx.logger.info(' IP: {0}' . format(xchgAgent['ip']))
        env.hosts.append(xchgAgent['ip'])
    
    # Give Fabric our connection settings
    env.user = ctx.bootstrap_context.cloudify_agent.user
    env.key_filename = ctx.bootstrap_context.cloudify_agent.agent_key_path
    env.password = None
    env.disable_known_hosts = True
    
    # Retrieve public keys from each of the nodes
    execute(retrievePublicKey)

    # Swap the public keys from the nodes and send them back to the nodes (exchanging them)
    execute(exchangePublicKeys)
    
    # Create our output
    ctx.logger.info('Exchanges: {0}' . format(XCHG_RESULT))
    ctx.instance.runtime_properties['exchange_result'] = XCHG_RESULT
    
@operation
def install_linux_agent(**kwargs):
    # Create a temporary file to store our key in
    fd, sPath = tempfile.mkstemp()
    # Close the file we just made
    os.close(fd)
    
    # Generate the SSH keys
    ctx.logger.info('Generating keys: {0}[.pub]' . format(sPath))
    if subprocess.call('ssh-keygen -t rsa -b 2048 -N "" -f ' + sPath, shell=True) != 0:
        if (not os.path.exists(sPath)) or (not os.path.exists(sPath + '.pub')):
            raise NonRecoverableError("Error generating keys")

    # Confirm the keys are OK
    ctx.logger.info('Reading generated public key')
    with open(sPath + '.pub', 'r') as f:
        ctx.logger.info('{0}: {1}' . format(sPath + '.pub', f.read()))
    
    # Store the location of the key to our runtime properties
    ctx.instance.runtime_properties['key_path'] = sPath
    
    ctx.logger.info('Plugin script completed')
