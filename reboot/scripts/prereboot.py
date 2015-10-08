from novaclient import nova
from cloudify import ctx

# Get the provider_context for OpenStack Nova communication
ctx.logger.info('provider_context: {0}' . format(ctx.provider_context))
