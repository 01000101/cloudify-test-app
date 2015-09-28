import os
import subprocess
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
# put the operation decorator on any function that is a task
from cloudify.decorators import operation


@operation
def configure(**kwargs):
    ctx.logger.info('exchange.configure() called')