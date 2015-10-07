from os import system
from cloudify import ctx

nSec = 15

ctx.logger.info('Rebooting the host VM in {0} seconds...' . format(nSec))
system('shutdown -r -t {0}' . format(nSec))