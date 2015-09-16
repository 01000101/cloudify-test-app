from cloudify import ctx

ctx.logger.info('Initializing plugin script: scripts/PoC.py')
    
for rel in ctx.instance.relationships:
    inst = rel.target.instance
    node = rel.target.node
    ctx.logger.info('Relationship:')
    ctx.logger.info(' Node:')
    ctx.logger.info('  id: ' . format(node.id))
    ctx.logger.info('  name: ' . format(node.name))
    ctx.logger.info('  properties: ' . format(node.properties))
    ctx.logger.info('  all: ' . format(node))
    ctx.logger.info(' Instance:')
    ctx.logger.info('  runtime: ' . format(inst.runtime_properties))
    ctx.logger.info('  all: ' . format(inst))
    
   
ctx.logger.info('Node properties: '
    .format(ctx.node.properties))
 
ctx.logger.info('Runtime properties: '
    .format(ctx.instance.runtime_properties))

ctx.logger.info('Relationships: '
    .format(ctx.instance.relationships))
    
ctx.logger.info('Plugin script completed')