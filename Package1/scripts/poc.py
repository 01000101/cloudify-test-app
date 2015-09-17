from cloudify import ctx

PRIV_KEY_FILE = '/tmp/temp.key'
PRIV_KEY_DATA = ''
node_list = []

ctx.logger.info('Initializing plugin script: scripts/poc.py')

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
with open(PRIV_KEY_FILE, 'r') as f
    PRIV_KEY_DATA = f.read()
    
ctx.logger.info('Temporary SSH key: {0}' . format(PRIV_KEY_DATA))
    
ctx.logger.info('Plugin script completed')