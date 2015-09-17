import os
import subprocess
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

PRIV_KEY_FILE = '/tmp/temp.key'
SSH_AUTH_FILE = '/home/ubuntu/.ssh/authorized_keys'
ORACLE_KEY_PATH = ctx.node.properties['oracle_key_path'] + '.pub'
N1_ORACLE_KEY = '/tmp/node1.rac.key.pub'
N2_ORACLE_KEY = '/tmp/node2.rac.key.pub'
node_list = []

ctx.logger.info('Initializing plugin script: scripts/poc.py')

# Find exactly two dependent nodes to retrieve keys from
ctx.logger.info('Discovering dependent nodes')
for rel in ctx.instance.relationships:
    if rel.type == 'cloudify.relationships.depends_on':
        node_list.append(rel.target)

ctx.logger.info('{0} nodes discovered' . format(len(node_list)))
if len(node_list) != 2:
    raise NonRecoverableError("Node requires exactly 2 dependent nodes")

N1_IP = node_list[0].instance.host_ip
N2_IP = node_list[1].instance.host_ip
ctx.logger.info(' Node #1: {0}' . format(N1_IP))
ctx.logger.info(' Node #2: {0}' . format(N2_IP))

# Retrieve the temporary SSH private key from the blueprint
ctx.logger.info('Copying temporary SSH key to filesystem')
ctx.download_resource(ctx.node.properties['tmp_priv_key_path'], PRIV_KEY_FILE)
with open(PRIV_KEY_FILE, 'r') as f:
    ctx.logger.info('{0}: {1}' . format(PRIV_KEY_FILE, f.read()))

ctx.logger.info('Setting temporary SSH key permissions')
os.chmod(PRIV_KEY_FILE, 0600)

# Retrieve Oracle RAC public keys from each of the nodes
ctx.logger.info('Copying Oracle RAC public key from {0} to {1}' . format(N1_IP + ':' + ORACLE_KEY_PATH, N1_ORACLE_KEY))
cmd = '/usr/bin/scp -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ubuntu@' + N1_IP + ':' + ORACLE_KEY_PATH + ' ' + N1_ORACLE_KEY
if subprocess.call(cmd, shell=True) != 0:
    raise NonRecoverableError("Error copying Oracle RAC public key from {0}" . format(N1_IP + ':' + ORACLE_KEY_PATH))

ctx.logger.info('Copying Oracle RAC public key from {0} to {1}' . format(N2_IP + ':' + ORACLE_KEY_PATH, N2_ORACLE_KEY))
cmd = '/usr/bin/scp -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ubuntu@' + N2_IP + ':' + ORACLE_KEY_PATH + ' ' + N2_ORACLE_KEY
if subprocess.call(cmd, shell=True) != 0:
    raise NonRecoverableError("Error copying Oracle RAC public key from {0}" . format(N2_IP + ':' + ORACLE_KEY_PATH))

# Output the retrieved public keys
ctx.logger.info('Reading Node #1 Oracle RAC public key')
with open(N1_ORACLE_KEY, 'r') as f:
    N1_ORACLE_KEY_DATA = f.read()
    ctx.logger.info('{0}: {1}' . format(N1_ORACLE_KEY, N1_ORACLE_KEY_DATA))
    
ctx.logger.info('Reading Node #2 Oracle RAC public key')
with open(N2_ORACLE_KEY, 'r') as f:
    N2_ORACLE_KEY_DATA = f.read()
    ctx.logger.info('{0}: {1}' . format(N2_ORACLE_KEY, N2_ORACLE_KEY_DATA))

# Swap the public keys from the nodes and send them back to the nodes (exchanging them)
ctx.logger.info('Copying Oracle RAC public key from {0} to {1}' . format(N2_ORACLE_KEY, N1_IP + ':' + ORACLE_KEY_PATH + '.peer'))
cmd = 'scp -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ' + N2_ORACLE_KEY + ' ubuntu@' + N1_IP + ':' + ORACLE_KEY_PATH + '.peer'
if subprocess.call(cmd, shell=True) != 0:
    raise NonRecoverableError("Error copying Oracle RAC public key from {0}" . format(N1_IP + ':' + ORACLE_KEY_PATH + '.peer'))

ctx.logger.info('Copying Oracle RAC public key from {0} to {1}' . format(N1_ORACLE_KEY, N2_IP + ':' + ORACLE_KEY_PATH + '.peer'))
cmd = 'scp -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ' + N1_ORACLE_KEY + ' ubuntu@' + N2_IP + ':' + ORACLE_KEY_PATH + '.peer'
if subprocess.call(cmd, shell=True) != 0:
    raise NonRecoverableError("Error copying Oracle RAC public key from {0}" . format(N2_IP + ':' + ORACLE_KEY_PATH + '.peer'))

# Delete the temporary SSH public key from each node
ctx.logger.info('Deleting temporary SSH public key from {0}:{1}' . format(N1_IP, SSH_AUTH_FILE))
cmd = 'ssh -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ubuntu@' + N1_IP + ' sed -i "/' + N1_ORACLE_KEY_DATA + '/d" ' + SSH_AUTH_FILE
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, err = p.communicate()
ctx.logger.info('output: {0}' . format(output))
ctx.logger.info('err: {0}' . format(err))

ctx.logger.info('Restarting the SSH service on {0}' . format(N1_IP))
cmd = 'ssh -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ubuntu@' + N1_IP + ' sudo service ssh restart'
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, err = p.communicate()
ctx.logger.info('output: {0}' . format(output))
ctx.logger.info('err: {0}' . format(err))

ctx.logger.info('Deleting temporary SSH public key from {0}:{1}' . format(N2_IP, SSH_AUTH_FILE))
cmd = 'ssh -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ubuntu@' + N2_IP + ' sed -i "/' + N2_ORACLE_KEY_DATA + '/d" ' + SSH_AUTH_FILE
if subprocess.call(cmd, shell=True) != 0:
    raise NonRecoverableError("Error removing temporary SSH public key from {0}" . format(N2_IP))
ctx.logger.info('Restarting the SSH service on {0}' . format(N2_IP))
cmd = 'ssh -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ubuntu@' + N2_IP + ' sudo service ssh restart'
if subprocess.call(cmd, shell=True) != 0:
    raise NonRecoverableError("Error restarting SSH service on {0}" . format(N2_IP))

ctx.logger.info('Oracle RAC keys successfully exchanged between {0} and {1}' . format(N1_IP, N2_IP))
ctx.logger.info('Plugin script completed')