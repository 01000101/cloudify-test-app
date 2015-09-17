import subprocess
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

PRIV_KEY_FILE = '/tmp/temp.key'
ORACLE_KEY_PATH = ctx.node.properties['oracle_key_path'] + '.pub'
NODE1_ORACLE_KEY = '/tmp/node1.rac.key.pub'
NODE2_ORACLE_KEY = '/tmp/node2.rac.key.pub'
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
    
ctx.logger.info('Preparing to query nodes for Oracle RAC keys')
ctx.logger.info(' Node #1: {0}' . format(node_list[0].instance.host_ip))
ctx.logger.info(' Node #2: {0}' . format(node_list[1].instance.host_ip))

# Retrieve the temporary SSH private key from the blueprint
ctx.logger.info('Copying temporary SSH key to filesystem')
ctx.download_resource(ctx.node.properties['tmp_priv_key_path'], PRIV_KEY_FILE)
with open(PRIV_KEY_FILE, 'r') as f:
    ctx.logger.info('{0}: {1}' . format(PRIV_KEY_FILE, f.read()))
    
# Retrieve Oracle RAC public keys from each of the nodes
ctx.logger.info('Copying Oracle RAC public key from {0} to {1}' . format(node_list[0].instance.host_ip + ':' + ORACLE_KEY_PATH, NODE1_ORACLE_KEY))
cmd = '/usr/bin/scp -o "StrictHostKeyChecking no" -i ' + PRIV_KEY_FILE + ' ubuntu@' + node_list[0].instance.host_ip + ':' + ORACLE_KEY_PATH + ' ' + NODE1_ORACLE_KEY
ctx.logger.info(' Executing: {0}' . format(cmd))
p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, err = p.communicate()
ctx.logger.info('output: {0}' . format(output))
ctx.logger.info('err: {0}' . format(err))

ctx.logger.info('Copying Oracle RAC public key from {0} to {1}' . format(node_list[1].instance.host_ip + ':' + ORACLE_KEY_PATH, NODE2_ORACLE_KEY))
cmd = '/usr/bin/scp -i ' + PRIV_KEY_FILE + ' ubuntu@' + node_list[1].instance.host_ip + ':' + ORACLE_KEY_PATH + ' ' + NODE2_ORACLE_KEY
ctx.logger.info(' Executing: {0}' . format(cmd))
if subprocess.call(cmd, shell=True) != 0:
    raise NonRecoverableError("Error copying Oracle RAC public key from {0}" . format(node_list[1].instance.host_ip + ':' + ORACLE_KEY_PATH))

# Output the retrieved public keys
ctx.logger.info('Reading Node #1 Oracle RAC public key')
with open(NODE1_ORACLE_KEY, 'r') as f:
    ctx.logger.info('{0}: {1}' . format(NODE1_ORACLE_KEY, f.read()))
ctx.logger.info('Reading Node #2 Oracle RAC public key')
with open(NODE2_ORACLE_KEY, 'r') as f:
    ctx.logger.info('{0}: {1}' . format(NODE2_ORACLE_KEY, f.read()))

# Swap the public keys from the nodes and send them back to the nodes (exchanging them)
ctx.logger.info('Copying Oracle RAC public key from {0} to {1}' . format(NODE2_ORACLE_KEY, node_list[0].instance.host_ip + ':' + ORACLE_KEY_PATH + '.peer'))
if subprocess.call('scp -i ' + PRIV_KEY_FILE + ' ' + NODE2_ORACLE_KEY + ' ubuntu@' + node_list[0].instance.host_ip + ':' + ORACLE_KEY_PATH + '.peer', shell=True) != 0:
    raise NonRecoverableError("Error copying Oracle RAC public key from {0}" . format(node_list[0].instance.host_ip + ':' + ORACLE_KEY_PATH + '.peer'))
ctx.logger.info('Copying Oracle RAC public key from {0} to {1}' . format(NODE1_ORACLE_KEY, node_list[1].instance.host_ip + ':' + ORACLE_KEY_PATH + '.peer'))
if subprocess.call('scp -i ' + PRIV_KEY_FILE + ' ' + NODE1_ORACLE_KEY + ' ubuntu@' + node_list[1].instance.host_ip + ':' + ORACLE_KEY_PATH + '.peer', shell=True) != 0:
    raise NonRecoverableError("Error copying Oracle RAC public key from {0}" . format(node_list[1].instance.host_ip + ':' + ORACLE_KEY_PATH + '.peer'))

ctx.logger.info('Oracle RAC keys successfully exchanged between {0} and {1}' . format(node_list[0].instance.host_ip, node_list[1].instance.host_ip))
ctx.logger.info('Plugin script completed')