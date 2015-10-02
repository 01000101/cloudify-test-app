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
        
class ExchangeNode:
    def __init__(self, ip='', path=''):
        self.ip = ip
        self.path = path
        
# Find any dependent nodes to retrieve keys from
def discoverDependents():
    node_list = []
    
    for rel in ctx.instance.relationships:
        if rel.type == 'cloudify.relationships.depends_on':
            node_list.append(rel.target.instance.host_ip)
    
    return node_list

@parallel
def retrievePublicKey():
    ctx.logger.info("Executing on {0} as {1}" . format(
        env.host,
        env.user
    ))
    
    PUBKEY = open('/tmp/{0}.key.pub' . format(env.host), 'w+')
    fabric.operations.get(XCHG_KEY_PATH + '.pub', PUBKEY)
    PUBKEY.close()

@operation
def configure(**kwargs):
    global XCHG_SSH_USER
    global XCHG_SSH_AUTH_FILE
    
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
    
    # Give Fabric our remote hosts list
    env.hosts = nodeIpList
    
    # Retrieve public keys from each of the nodes
    with settings(
        user=ctx.bootstrap_context.cloudify_agent.user,
        key_filename=ctx.bootstrap_context.cloudify_agent.agent_key_path,
        disable_known_hosts=True
    ):
        execute(retrievePublicKey)
    
    # Output the retrieved public keys
    for idx, nodeIp in enumerate(nodeIpList):
        ctx.logger.info('Reading Node #{0} ({1}) public key' . format(
            idx,
            nodeIp
        ))
        with open('/tmp/{0}.key.pub' . format(nodeIp), 'r') as f:
            ctx.logger.info(' {0}: {1}' . format(
                '/tmp/{0}.key.pub' . format(nodeIp),
                f.read()
            ))

    # Swap the public keys from the nodes and send them back to the nodes (exchanging them)
    for nodeTo in et.nodes:
        for nodeFrom in et.nodes:
            if nodeTo != nodeFrom:
                ctx.logger.info('Copying public key from {0} to {1}' . format(nodeFrom.ip, nodeTo.ip))
                cmd = 'scp -o "StrictHostKeyChecking no" -i {0} {1} {2}@{3}:{1}' . format(
                    et.privateKey,
                    nodeFrom.path,
                    XCHG_SSH_USER,
                    nodeTo.ip
                )
                if subprocess.call(cmd, shell=True) != 0:
                    raise NonRecoverableError("Error copying public key from {0}:{1}" . format(
                        nodeFrom.ip,
                        nodeFrom.path
                    ))

    # Delete the temporary SSH public key from each node (removes the last key entry)
    for idx, node in enumerate(et.nodes):
        cmd = 'ssh -o "StrictHostKeyChecking no" -i {0} {1}@{2} {3} {4}' . format(
            et.privateKey,
            XCHG_SSH_USER,
            node.ip,
            """ sed -i "'\$d'" """,
            XCHG_SSH_AUTH_FILE
        )
        ctx.logger.info('Executing: {0}' . format(cmd))
        
        if subprocess.call(cmd, shell=True) != 0:
            raise RecoverableError("Error removing temporary SSH public key from {0}" . format(
                node.ip
            ))

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
