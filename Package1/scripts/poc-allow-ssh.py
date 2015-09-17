import os
from cloudify import ctx

PUB_KEY_FILE = '/tmp/temp.key.pub'
PUB_KEY_DATA = ''
SSH_AUTH_FILE = '/home/ubuntu/.ssh/authorized_keys'
ORACLE_KEY_PATH = ctx.node.properties['oracle_key_path']

ctx.logger.info('Initializing plugin script: scripts/poc-allow-ssh.py')

# Install temporary public SSH key into authorized_keys so LAST_NODE can access this system
ctx.logger.info('Copying temporary SSH key to filesystem')
ctx.download_resource(ctx.node.properties['tmp_pub_key_path'], PUB_KEY_FILE)

ctx.logger.info('Retrieving temporary SSH key into memory')
with open(PUB_KEY_FILE, 'r') as f:
    PUB_KEY_DATA = f.read()
    
ctx.logger.info('Temporary SSH key: {0}' . format(PUB_KEY_DATA))

ctx.logger.info('Adding temporary SSH key to authorized_keys list')
with open(SSH_AUTH_FILE, 'a') as f:
    f.write(PUB_KEY_DATA)

ctx.logger.info('Reading authorized_keys list')
with open(SSH_AUTH_FILE, 'r') as f:
    ctx.logger.info('authorized_keys: {0}' . format(f.read()))

# Generate Oracle RAC keys
ctx.logger.info('Creating path to store Oracle RAC keys: {0}' . format(os.path.dirname(ORACLE_KEY_PATH)))
subprocess.call(['mkdir', '-p', os.path.dirname(ORACLE_KEY_PATH)])
ctx.logger.info('Generating Oracle RAC keys: {0}' . format(ORACLE_KEY_PATH))
subprocess.call(['ssh-keygen', '-t', 'rsa', '-b', '2048', '-N', '""', '-f', ORACLE_KEY_PATH])

# Enable LAST_NODE to access this system via SSH
ctx.logger.info('Restarting the SSH service')
subprocess.call(['sudo', 'ssh', 'restart'])

ctx.logger.info('Plugin script completed')