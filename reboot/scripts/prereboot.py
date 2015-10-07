import subprocess
from cloudify import ctx

nSec = 15

ctx.logger.info('Rebooting the host VM in {0} seconds...' . format(nSec))
out = subprocess.check_output('sudo shutdown -r 15', stderr=subprocess.STDOUT, stdout=subprocess.STDOUT, shell=True)
ctx.logger.info('Reboot request output: {0}' . format(out))