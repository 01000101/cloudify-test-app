"""Key Exchange Plugin

This plugin is used to exchange public key files between all "agents" (servers)
by a "Facilitator" (Cloudify Manager).  This plugin relies on Fabric for
server communication. 
"""

import os, tempfile
import Crypto # RSA key generating
import fabric # Inter-server process execution
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
XCHG_RESULT = []
xchgAgents = []
        
# Find any dependent nodes to retrieve keys from and build
# the main data structure for the exchange
def discoverDependents():
    node_list = []
    
    for rel in ctx.instance.relationships:
        if rel.type == 'cloudify.relationships.depends_on':
            node_list.append({
                'ip': rel.target.instance.host_ip,
                'remote_public_key': rel.target.instance.runtime_properties['public_key_path'],
                'remote_private_key': rel.target.instance.runtime_properties['public_key_path'],
                'local_public_key': ''
            })
    
    return node_list

# This function retrieves the public key from the remote server,
# updates xchgAgents, and cleans up
def retrievePublicKey():
    global xchgAgents
    
    ctx.logger.info("Executing on {0} as {1}" . format(
        fabric.api.env.host,
        fabric.api.env.user
    ))
    
    # Find ourselves...
    for idx in range(len(xchgAgents)):
        if xchgAgents[idx]['ip'] == fabric.api.env.host:
            # Generate temporary file
            fd, sPath = tempfile.mkstemp()
            with os.fdopen(fd, 'w+') as temp_file:
                # Copy the remote public key to the temporary file
                ctx.logger.info('fabric.operations.get({0}, {1})' . format(xchgAgents[idx]['remote_public_key'], sPath))
                fabric.api.get(xchgAgents[idx]['remote_public_key'], temp_file)
                
                # Log where we stashed the public key
                xchgAgents[idx]['local_public_key'] = sPath
            
            return

# This function faciliates the exchange of keys between servers
def exchangePublicKeys():
    global XCHG_RESULT
    global xchgAgents
    exchanges = []
    
    ctx.logger.info("Executing on {0} as {1}" . format(
        fabric.api.env.host,
        fabric.api.env.user
    ))
    
    # Find ourselves...
    for xchgAgentTo in xchgAgents:
        if xchgAgentTo['ip'] == fabric.api.env.host:
            # Iterate through all nodes (except for ourself)
            for xchgAgentFrom in xchgAgents:
                if xchgAgentFrom['ip'] != xchgAgentTo['ip']:
                    ctx.logger.info('Moving public key from {0} to {1}' . format(
                        xchgAgentFrom['ip'],
                        xchgAgentTo['ip']
                    ))
                
                    # Copy the public key from local to a remote node
                    res = fabric.api.put(xchgAgentFrom['local_public_key'], '/tmp/')
                    
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
            
def publicKeyCleanup():
    for xchgAgent in xchgAgents:
        pubkey_path = xchgAgent['local_public_key']
        
        ctx.logger.info('Purging local key for {0} at {1}' . format(
            xchgAgent['ip'],
            pubkey_path
        ))
        
        if not os.path.exists(pubkey_path):
            RecoverableError('Could not find local key for {0} at {1}' . format(
                xchgAgent['ip'],
                pubkey_path
            ))
            
        try:
            os.unlink(pubkey_path)
        except OSError:
            RecoverableError('Could not purge local key for {0} at {1}' . format(
                xchgAgent['ip'],
                pubkey_path
            ))

# Entry point for the Facilitator
@operation
def configure(**kwargs):
    global XCHG_NODES
    global xchgAgents
    fabric.api.env.hosts = []
    
    ctx.logger.info('Discovering dependent nodes')
    xchgAgents = discoverDependents()
    
    # If less than 2 nodes were discovered, that's a problem...
    ctx.logger.info('{0} nodes discovered' . format(len(xchgAgents)))
    if len(xchgAgents) < 2:
        raise NonRecoverableError('Exchange plugin requires at least 2 dependent nodes')
    
    # Add each found node IP to the Fabric hosts list
    for xchgAgent in xchgAgents:
        ctx.logger.info(' IP: {0}' . format(xchgAgent['ip']))
        fabric.api.env.hosts.append(xchgAgent['ip'])
    
    # Give Fabric our connection settings
    cfy_agent_user = None
    cfy_agent_key = None
    
    ctx.logger.info('agent: {0}' . format(ctx.node.properties.get('cloudify_agent')))
    
    # Get the user/key from either the manager or user provided properties
    fabric.api.env.user = ctx.node.properties.get('cloudify_agent', dict()).get(
        'user', ctx.bootstrap_context.cloudify_agent.user
    )
    
    fabric.api.env.key_filename = ctx.node.properties.get('cloudify_agent', dict()).get(
        'key', ctx.bootstrap_context.cloudify_agent.agent_key_path
    )
    
    fabric.api.env.password = None
    fabric.api.env.disable_known_hosts = True
    
    # Retrieve public keys from each of the nodes
    fabric.api.execute(retrievePublicKey)

    # Swap the public keys from the nodes and send them back to the nodes (exchanging them)
    fabric.api.execute(exchangePublicKeys)
    
    # Purge locally stored public keys
    publicKeyCleanup()
    
    # Create our output
    ctx.logger.info('Exchanges: {0}' . format(XCHG_RESULT))
    ctx.instance.runtime_properties['exchange_result'] = XCHG_RESULT

# Entry point for the Agent
@operation
def install_linux_agent(**kwargs):
    # Create a temporary directory to store our keys in
    sPath = tempfile.mkdtemp()
    sPrivPath = sPath + '/tmp.key'
    sPubPath = sPath + '/tmp.key.pub'
    
    # Create/open the files for public/private keys
    with open(sPrivPath, 'w+') as fPriv, \
         open(sPubPath, 'w+') as fPub:
        # Generate the RSA keys
        ctx.logger.info('Generating RSA keys');
        Crypto.Random.atfork() 
        key = Crypto.PublicKey.RSA.generate(2048)
        pubkey = key.publickey()
        
        # Write the keys with proper OpenSSH encoding
        ctx.logger.info('Writing generated RSA keys to the filesystem')
        fPriv.write(key.exportKey('PEM'))
        fPub.write(pubkey.exportKey('OpenSSH'))
    
    # Output some basics to the user
    ctx.logger.info('Private key path: {0}' . format(sPrivPath))
    ctx.logger.info('Public key path: {0}' . format(sPubPath))

    # Store the location of the keys to our runtime properties
    ctx.instance.runtime_properties['public_key_path'] = sPubPath
    ctx.instance.runtime_properties['private_key_path'] = sPrivPath
    
    ctx.logger.info('Plugin script completed')
