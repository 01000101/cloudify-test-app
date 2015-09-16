from cloudify import ctx

ctx.logger.info('Initializing plugin script: scripts/PoC.py')
    
for rel in ctx.instance.relationships:
    target = rel.target.runtime_properties
    ctx.logger.info('relationship:')
    ctx.logger.info('  ip: ' . format(target['ip']))
    ctx.logger.info('  all: ' . format(target))
   
ctx.logger.info('Node properties: '
    .format(ctx.node.properties))
 
ctx.logger.info('Runtime properties: '
    .format(ctx.instance.runtime_properties))

ctx.logger.info('Relationships: '
    .format(ctx.instance.relationships))
    
ctx.logger.info('Plugin script completed')