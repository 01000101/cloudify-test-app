from cloudify import ctx

PRIV_KEY_FILE = '/tmp/temp.key'
PRIV_KEY_DATA = ''
ORACLE_KEY_PATH = ctx.node.properties['oracle_key_path']
NODE1_ORACLE_KEY = '/tmp/node1.rac.key.pub'
NODE2_ORACLE_KEY = '/tmp/node2.rac.key.pub'
node_list = []

ctx.logger.info('Initializing plugin script: scripts/poc.py')

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
   
ctx.logger.info('Node properties: {0}'
    .format(ctx.node.properties))
 
ctx.logger.info('Runtime properties: {0}'
    .format(ctx.instance.runtime_properties))

ctx.logger.info('Relationships: {0}'
    .format(ctx.instance.relationships))
    
ctx.logger.info('Copying temporary SSH key to filesystem')
ctx.download_resource(ctx.node.properties['tmp_priv_key_path'], PRIV_KEY_FILE)

ctx.logger.info('Retrieving temporary SSH key into memory')
with open(PRIV_KEY_FILE, 'r') as f:
    PRIV_KEY_DATA = f.read()
    
ctx.logger.info('Temporary SSH key: {0}' . format(PRIV_KEY_DATA))

ctx.logger.info('Copying Oracle RAC public key from Node #1 to {0}' . format(NODE1_ORACLE_KEY))
subprocess.call(['scp', '-i', PRIV_KEY_FILE, 'ubuntu@' + node_list[0].instance.host_ip + ':' + ORACLE_KEY_PATH, NODE1_ORACLE_KEY])
ctx.logger.info('Copying Oracle RAC public key from Node #2 to {0}' . format(NODE2_ORACLE_KEY))
subprocess.call(['scp', '-i', PRIV_KEY_FILE, 'ubuntu@' + node_list[1].instance.host_ip + ':' + ORACLE_KEY_PATH, NODE2_ORACLE_KEY])

ctx.logger.info('Reading Node #1 Oracle key')
with open(NODE1_ORACLE_KEY, 'r') as f:
    ctx.logger.info('{0}: {1}' . format(NODE1_ORACLE_KEY, f.read()))

ctx.logger.info('Reading Node #2 Oracle key')
with open(NODE2_ORACLE_KEY, 'r') as f:
    ctx.logger.info('{0}: {1}' . format(NODE2_ORACLE_KEY, f.read()))

ctx.logger.info('Plugin script completed')