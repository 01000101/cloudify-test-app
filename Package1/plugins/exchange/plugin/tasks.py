import os
import tempfile
import uuid
import subprocess
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
# put the operation decorator on any function that is a task
from cloudify.decorators import operation

# Globals
SSH_AUTH_FILE = '/home/ubuntu/.ssh/authorized_keys'
XCHG_KEY_PATH = ''

class ExchangeTracker:
    def __init__(self, privateKeyPath=''):
        self.privateKey = privateKeyPath
        self.nodes = []
        
class ExchangeNode:
    def __init__(self, ip='', path=''):
        self.ip = ip
        self.path = path

# Generate the path to a temporary file
def getTemporaryFile():
    tmpKeyPath = '/tmp/' + str(uuid.uuid4())
    while os.path.isfile(tmpKeyPath):
        tmpKeyPath = '/tmp/' + str(uuid.uuid4())
    return tmpKeyPath

# Find any dependent nodes to retrieve keys from
def discoverDependents():
    node_list = []
    
    for rel in ctx.instance.relationships:
        if rel.type == 'cloudify.relationships.depends_on':
            node_list.append(rel.target.instance.host_ip)
    
    return node_list

def retrievePublicKey(et, nodeIp):
    # Generate a unique temporary file for use
    node = ExchangeNode(nodeIp, getTemporaryFile())
    
    # Retrieve Oracle RAC public keys from each of the nodes
    ctx.logger.info('Copying public key from {0}:{1} to {2}' . format(
        node.ip,
        XCHG_KEY_PATH + '.pub',
        node.path
    ))
    cmd = '/usr/bin/scp -o "StrictHostKeyChecking no" -i {0} ubuntu@{1}:{2} {3}' .format(
        et.privateKey,
        node.ip,
        XCHG_KEY_PATH + '.pub',
        node.path
    )
    if subprocess.call(cmd, shell=True) != 0:
        raise NonRecoverableError("Error copying public key from {0}:{1}" . format(
            node.ip,
            XCHG_KEY_PATH + '.pub'
        ))
    
    return node

@operation
def configure(**kwargs):
    global XCHG_KEY_PATH
    XCHG_KEY_PATH = ctx.node.properties['exchange_key_path']
    
    # Init a tracking class & create a temporary dir for use
    et = ExchangeTracker(getTemporaryFile())
    
    ctx.logger.info('Discovering dependent nodes')
    nodeIpList = discoverDependents()
    
    # If less than 2 nodes were discovered, that's a problem...
    ctx.logger.info('{0} nodes discovered' . format(len(nodeIpList)))
    if len(nodeIpList) < 2:
        raise NonRecoverableError("Exchange plugin requires at least 2 dependent nodes")
    
    # Output each node IP
    for nodeIp in nodeIpList:
        ctx.logger.info(' IP: {0}' .format(nodeIp))
    
    # Retrieve the temporary SSH private key from the blueprint
    ctx.logger.info('Copying temporary SSH key to {0}' .format(et.privateKey))
    ctx.download_resource(ctx.node.properties['tmp_priv_key_path'], et.privateKey)
    
    # SSH/SCP will complain if the private is not permissioned properly
    ctx.logger.info('Setting temporary SSH key permissions to 0600')
    os.chmod(et.privateKey, 0600)
    
    # Retrieve public keys from each of the nodes
    for nodeIp in nodeIpList:
        et.nodes.append(retrievePublicKey(et, nodeIp))
    
    # Output the retrieved public keys
    for idx, node in enumerate(et.nodes):
        ctx.logger.info('Reading Node #{0} ({1}) public key' .format(
            idx,
            node.ip
        ))
        with open(node.path, 'r') as f:
            ctx.logger.info(' {0}: {1}' . format(
                node.path,
                f.read()
            ))

    # Swap the public keys from the nodes and send them back to the nodes (exchanging them)
    for nodeTo in et.nodes:
        for nodeFrom in et.nodes:
            if nodeTo != nodeFrom:
                ctx.logger.info('Copying public key from {0} to {1}' . format(nodeFrom.ip, nodeTo.ip))
                cmd = 'scp -o "StrictHostKeyChecking no" -i {0} {1} ubuntu@{2}:{1}' .format(
                    et.privateKey,
                    nodeFrom.path,
                    nodeTo.ip
                )
                if subprocess.call(cmd, shell=True) != 0:
                    raise NonRecoverableError("Error copying public key from {0}:{1}" . format(
                        nodeFrom.ip,
                        nodeFrom.path
                    ))

    # Delete the temporary SSH public key from each node (removes the last key entry)
    for idx, node in enumerate(et.nodes):
        cmd = 'ssh -o "StrictHostKeyChecking no" -i {0} ubuntu@{1} ' + """ sed -i "'\$d'" """ + '{2}' .format(
            et.privateKey,
            node.ip,
            SSH_AUTH_FILE
        )
        if subprocess.call(cmd, shell=True) != 0:
            raise RecoverableError("Error removing temporary SSH public key from {0}" . format(
                node.ip
            ))

    ctx.logger.info('Plugin script completed')
    
@operation
def install_linux_agent(**kwargs):
    global XCHG_KEY_PATH
    XCHG_KEY_PATH = ctx.node.properties['exchange_key_path']
    tmp_pub_key = getTemporaryFile()
    
    # Install temporary public SSH key into authorized_keys so LAST_NODE can access this system
    ctx.logger.info('Copying temporary SSH key to filesystem')
    ctx.download_resource(ctx.node.properties['tmp_pub_key_path'], tmp_pub_key)
    
    ctx.logger.info('Retrieving temporary SSH key into memory')
    with open(tmp_pub_key, 'r') as f:
        PUB_KEY_DATA = f.read()
        
    ctx.logger.info('Temporary SSH key: {0}' . format(PUB_KEY_DATA))
    
    ctx.logger.info('Adding temporary SSH key to authorized_keys list')
    with open(SSH_AUTH_FILE, 'a') as f:
        f.write(PUB_KEY_DATA)
    
    ctx.logger.info('Reading authorized_keys list')
    with open(SSH_AUTH_FILE, 'r') as f:
        ctx.logger.info('authorized_keys: {0}' . format(f.read()))
    
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
    
    # Enable LAST_NODE to access this system via SSH
    ctx.logger.info('Restarting the SSH service')
    if subprocess.call(['sudo', 'service', 'ssh', 'restart']) != 0:
        raise NonRecoverableError("Error restarting the SSH service")
    
    ctx.logger.info('Plugin script completed')
