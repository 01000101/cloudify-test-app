from cloudify import ctx

PUB_KEY_FILE = '/tmp/temp.key.pub'
PUB_KEY_DATA = ''
SSH_AUTH_FILE = '/home/ubuntu/.ssh/authorized_keys'

ctx.logger.info('Initializing plugin script: scripts/poc-allow-ssh.py')

ctx.logger.info('Node properties: {0}'
    .format(ctx.node.properties))
 
ctx.logger.info('Runtime properties: {0}'
    .format(ctx.instance.runtime_properties))

ctx.logger.info('Relationships: {0}'
    .format(ctx.instance.relationships))
    
ctx.logger.info('Copying temporary SSH key to filesystem')
ctx.download_resource(ctx.node.properties['tmp_pub_key_path'], PUB_KEY_FILE)

ctx.logger.info('Retrieving temporary SSH key into memory')
with open(PUB_KEY_FILE, 'r') as f:
    PUB_KEY_DATA = f.read()
    
ctx.logger.info('Temporary SSH key: {0}' . format(PUB_KEY_DATA))

ctx.logger.info('Adding temporary SSH key to authorized_keys list')
with open(SSH_AUTH_FILE, 'a') as f:
    f.write(PUB_KEY_DATA)

ctx.logger.inf('Restarting the SSH service')
subprocess.call(['sudo', 'ssh', 'restart'])

ctx.logger.info('Plugin script completed')