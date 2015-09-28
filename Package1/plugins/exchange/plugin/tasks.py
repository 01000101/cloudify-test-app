import os
import subprocess
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError, RecoverableError
# put the operation decorator on any function that is a task
from cloudify.decorators import operation

# Globals
PRIV_KEY_FILE = '/tmp/temp.key'
SSH_AUTH_FILE = '/home/ubuntu/.ssh/authorized_keys'
ORACLE_KEY_PATH = ctx.node.properties['oracle_key_path'] + '.pub'
N1_ORACLE_KEY = '/tmp/node1.rac.key.pub'
N2_ORACLE_KEY = '/tmp/node2.rac.key.pub'
node_list = []

@operation
def facilitate(**_):
    ctx.logger.info('facilitate() called')