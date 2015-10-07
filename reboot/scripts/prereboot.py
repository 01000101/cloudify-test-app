import subprocess
from cloudify import ctx

nSec = 15

ctx.logger.info('Rebooting the host VM in {0} seconds...' . format(nSec))
proc = subprocess.Popen(['shutdown', '-r', nSec], stdout=subprocess.PIPE, shell=True)
(out, err) = proc.communicate()
ctx.logger.info('Reboot request output: {0} ({1})' . format(out, err))