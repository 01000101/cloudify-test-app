from cloudify import ctx

ctx.logger.info('Initializing plugin script: scripts/PoC.py')
    
for rel in ctx.instance.relationships:
    inst = rel.target.instance
    node = rel.target.node
    ctx.logger.info('Relationship ({0}):' . format(rel.type))
    ctx.logger.info(' Node:')
    ctx.logger.info('  id: {0}' . format(node.id))
    ctx.logger.info('  name: {0}' . format(node.name))
    ctx.logger.info('  properties: {0}' . format(node.properties))
    ctx.logger.info('  all: {0}' . format(node))
    ctx.logger.info(' Instance:')
    ctx.logger.info('  id: {0}' . format(inst.id))
    ctx.logger.info('  runtime: {0}' . format(inst.runtime_properties))
    ctx.logger.info('  host_ip: {0}' . format(inst.host_ip))
    ctx.logger.info('  relationships: {0}' . format(inst.relationships))
    ctx.logger.info('  all: {0}' . format(inst))
   
ctx.logger.info('Node properties: {0}'
    .format(ctx.node.properties))
 
ctx.logger.info('Runtime properties: {0}'
    .format(ctx.instance.runtime_properties))

ctx.logger.info('Relationships: {0}'
    .format(ctx.instance.relationships))
    
ctx.logger.info('Plugin script completed')