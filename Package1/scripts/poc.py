from cloudify import ctx

ctx.logger.info('Initializing plugin script: scripts/poc.py')
node_list = []

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
    
ctx.logger.info('Plugin script completed')