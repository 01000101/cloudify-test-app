import os
import tempfile
import uuid
import subprocess
from fabric.api import *
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.decorators import operation

# Globals
XCHG_SSH_AUTH_FILE = ''
XCHG_KEY_PATH = '/tmp/exchange/poc.key'
XCHG_SSH_USER = ''
XCHG_NODES = []
XCHG_RESULT = []
        
class ExchangeNode:
    def __init__(self, ip='', path=''):
        self.ip = ip
        self.path = path
        
class ExchangeResult:
    def __init__(self, ip='', exchanges=[]):
        self.ip = ip
        self.exchanges = exchanges
        
# Find any dependent nodes to retrieve keys from
def discoverDependents():
    node_list = []
    
    for rel in ctx.instance.relationships:
        if rel.type == 'cloudify.relationships.depends_on':
            node_list.append(rel.target.instance.host_ip)
    
    return node_list

# This function retrieves the public key from the remote server,
# updates XCHG_NODES, and cleans up
def retrievePublicKey():
    global XCHG_NODES
    
    ctx.logger.info("Executing on {0} as {1}" . format(
        env.host,
        env.user
    ))

    # Generate temporary file
    fd, sPath = tempfile.mkstemp()
    temp_file = os.fdopen(fd, 'w+')
    
    # Copy the remote public key to the temporary file
    ctx.logger.info('fabric.operations.get({0}, {1})' . format(XCHG_KEY_PATH + '.pub', sPath))
    res = get(XCHG_KEY_PATH + '.pub', temp_file)
    ctx.logger.info(' -> {0}' . format(res))
    
    # Log where we stashed the public key
    XCHG_NODES.append(ExchangeNode(env.host, sPath))
    
    # Close the temporary file
    temp_file.close()

def exchangePublicKeys():
    global XCHG_RESULT
    exchange = None
    nodeTo = None;
    
    ctx.logger.info("Executing on {0} as {1}" . format(
        env.host,
        env.user
    ))
    
    for node in XCHG_NODES:
        if node.ip == env.host:
            nodeTo = node
            break
    
    exchange = ExchangeResult(nodeTo.ip)
    
    for nodeFrom in XCHG_NODES:
        if nodeFrom != nodeTo:
            ctx.logger.info('Moving public key from {0} to {1}' . format(
                nodeFrom.ip,
                nodeTo.ip
            ))
            res = put(nodeFrom.path, '/tmp/')
            ctx.logger.info(' -> file moved to {0}:{1}' . format(
                nodeTo.ip,
                res
            ))
            
            # Log every exchange (to/from IP, public key path)
            exchange.exchanges.append(ExchangeNode(nodeFrom.ip, res[0]))
    
    # Log the entire exchange for this node
    XCHG_RESULT.append(exchange)

@operation
def configure(**kwargs):
    global XCHG_SSH_USER
    global XCHG_SSH_AUTH_FILE
    global XCHG_NODES
    
    XCHG_SSH_USER = ctx.node.properties['facilitator_agent_ssh_user']
    XCHG_SSH_AUTH_FILE = ctx.node.properties['facilitator_agent_authorized_keys_path']
    XCHG_PRIVATE_KEY_PATH = ctx.node.properties['facilitator_private_key_path']
    
    ctx.logger.info('Discovering dependent nodes')
    nodeIpList = discoverDependents()
    
    # If less than 2 nodes were discovered, that's a problem...
    ctx.logger.info('{0} nodes discovered' . format(len(nodeIpList)))
    if len(nodeIpList) < 2:
        raise NonRecoverableError("Exchange plugin requires at least 2 dependent nodes")
    
    # Output each node IP
    for nodeIp in nodeIpList:
        ctx.logger.info(' IP: {0}' . format(nodeIp))
    
    # Give Fabric our remote hosts list & settings
    env.hosts = nodeIpList
    env.user = ctx.bootstrap_context.cloudify_agent.user
    env.key_filename = ctx.bootstrap_context.cloudify_agent.agent_key_path
    env.password = None
    env.disable_known_hosts = True
    
    ctx.logger.info('Manager user: {0}' . format(env.user))
    ctx.logger.info('Manager key: {0}' . format(env.key_filename))
    
    # Retrieve public keys from each of the nodes
    execute(retrievePublicKey)

    # Swap the public keys from the nodes and send them back to the nodes (exchanging them)
    execute(exchangePublicKeys)
    
    # Create our output
    ctx.logger.info('XCHG_RESULT: {0}' . format(XCHG_RESULT))
    ctx.instance.runtime_properties['exchange_result'] = XCHG_RESULT

    ctx.logger.info('Plugin script completed')
    
@operation
def install_linux_agent(**kwargs):
    # Generate Oracle RAC keys
    ctx.logger.info('Creating path to store keys: {0}' . format(os.path.dirname(XCHG_KEY_PATH)))
    if not os.path.exists(os.path.dirname(XCHG_KEY_PATH)):
        os.makedirs(os.path.dirname(XCHG_KEY_PATH))
    
    if not os.path.exists(os.path.dirname(XCHG_KEY_PATH)):
        ctx.logger.info('Creating path failed')
        
    ctx.logger.info('Generating keys: {0}' . format(XCHG_KEY_PATH))
    if subprocess.call('ssh-keygen -t rsa -b 2048 -N "" -f ' + XCHG_KEY_PATH, shell=True) != 0:
        if not os.path.exists(XCHG_KEY_PATH):
            raise NonRecoverableError("Error generating keys")
    
    ctx.logger.info('Reading generated public key')
    with open(XCHG_KEY_PATH + '.pub', 'r') as f:
        ctx.logger.info('{0}: {1}' . format(XCHG_KEY_PATH + '.pub', f.read()))
    
    ctx.logger.info('Plugin script completed')
