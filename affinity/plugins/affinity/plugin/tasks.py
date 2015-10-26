'''(Anti-)Affinity Server Groups Pool plugin for Cloudify's OpenStack plugin'''

from os import sep, path
import filelock
import json
from tempfile import gettempdir
from cloudify import ctx, manager
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify.decorators import operation
from openstack_plugin_common import with_nova_client


# Metadata
__author__ = "Joshua Cornutt"
__copyright__ = "Copyright 2015, Gigaspaces"
__license__ = "Proprietary"
__maintainer__ = "Joshua Cornutt"
__email__ = "josh@gigaspaces.com"
__status__ = "Development"


CFG_FILE_PATH = gettempdir() + sep + 'affinityplugin.json'
LOCK = filelock.FileLock('cloudify_affinity_plugin')
LOCK.timeout = 60


def discover_dependent_hosts():
    '''Find any dependent node hosts of the Facilitator module'''
    host_list = []

    # Use the REST API to get the list of all nodes in this deployment
    client = manager.get_rest_client()
    rnodes = client.node_instances.list(deployment_id=ctx.deployment.id)

    # Iterate through each node and find ones that
    # have our Facilitator as a depends_on relationship
    for rnode in rnodes:
        node = manager.get_node_instance(rnode.id)

        for rel in node.relationships:
            ctx.logger.info('Relationship: {0}' . format(rel))
            if rel.get('type') == 'cloudify.relationships.depends_on':
                if rel.get('target_id') == ctx.instance.id:
                    # Find the dependent nodes' host (VM)
                    host_list.append(manager.get_node_instance(node.host_id))

    return host_list


# Returns a list of OpenStack Server Groups
# Guaranteed not to be an empty array
def get_openstack_server_groups(nova_client):
    '''Queries OpenStack for a list of all Server Groups'''
    _data = []

    if True:
        return [{
            'id': 'test-1-1-1-1',
            'deployment': None,
            'removed': False
        }, {
            'id': 'test-2-2-2-2',
            'deployment': None,
            'removed': False
        }, {
            'id': 'test-3-3-3-3',
            'deployment': None,
            'removed': False
        }]

    try:
        # This will cause a NonRecoverableError when executing
        # against an OpenStack instance that does NOT support,
        # or allow, server_groups.list()
        groups = nova_client.server_groups.list()

        if not len(groups):
            NonRecoverableError('nova.server_groups.list() returned '
                                'an empty result set. No Server Groups '
                                'are available for use.')
    except BaseException as ex:
        NonRecoverableError('nova.server_groups.list() is not allowed '
                            '(please update the policy.json file to allow '
                            'access to this call) [Exception: {0}]'
                            . format(ex))

    # Iterate through each Server Group returned
    for group in groups:
        ctx.logger.info('group: {0}' . format(group))
        ctx.logger.info(' id: {0}' . format(group.id))
        ctx.logger.info(' name: {0}' . format(group.name))
        ctx.logger.info(' members: {0}' . format(group.members))
        ctx.logger.info(' policies: {0}' . format(group.policies))

        _data.append({
            'id': group.id,     # OpenStack ID of the Server Group
            'deployment': None, # Cloudify deployment using the Server Group
            'removed': False    # Flag indicating if the Server Group
                                # still exists in OpenStack
        })

    return _data


def server_group_exists_in_config(_osid, _cfg):
    '''Checks if an OpenStack Server Group (osId)
       exists in the configuration data (cfgData)'''
    return [e for e in _cfg if e.get('id') == _osid]


# This is NOT a thread safe operation.
# Use external locking.
def get_config_data():
    '''Load our configuration data (JSON)'''
    with open(CFG_FILE_PATH, 'r') as f_cfg:
        return json.load(f_cfg)


# This is NOT a thread safe operation.
# Use external locking.
def overwrite_config_data(_cfg):
    '''Overwrite our configuration data (JSON)'''
    with open(CFG_FILE_PATH, 'w') as f_cfg:
        json.dump(_cfg, f_cfg)


def print_config_data():
    '''Prints the current configuration data to ctx.logger'''
    _cfg = get_config_data()
    for group in _cfg:
        ctx.logger.debug('Configuration data:\n'
                         'id: {0}, deployment: {1}, removed: {2}'
                         . format(
                             group.get('id'),
                             group.get('deployment'),
                             group.get('removed')
                         ))


# This is NOT a thread safe operation.
# Use external locking.
def create_config_data_if_needed(_os_data):
    '''Create, or update, our configuration file.
       This takes in OpenStack Server Groups (osData)
       and either dumps this to file (create) or
       it will make sure the data is consistent between
       what exists in OpenStack and what we have in
       our configuration file.'''
    _cfg = _os_data
    _cfg_exists = path.exists(CFG_FILE_PATH)

    # Configuration file exists
    ctx.logger.info('{0} configuration file: {1}' . format(
        'Updating' if _cfg_exists else 'Creating',
        CFG_FILE_PATH
    ))

    if _cfg_exists:
        # If the file exists, read in our configuration data
        _cfg = get_config_data()

        # Check for inconsistencies and resolve them
        for group in _os_data:
            # Config is outdated, add in new Server Group
            if not server_group_exists_in_config(group.get('id'), _cfg):
                ctx.logger.info('Adding {0} to the configuration file'
                                . format(group.get('id')))
                _cfg.append({
                    'id': group.get('id'),
                    'deployment': None,
                    'removed': False
                })

        for k, group in enumerate(_cfg):
            # Config has Server Groups that no longer exist
            if not server_group_exists_in_config(group.get('id'), _os_data):
                ctx.logger.info('Marking {0} for removal from the '
                                'configuration file'
                                . format(group.get('id')))
                _cfg[k].removed = True

    # Write our changes to our configuration file
    overwrite_config_data(_cfg)


# This is NOT a thread safe operation.
# Use external locking.
def acquire_server_group():
    '''Searches for a free, clean Server Group
       for this deployment to use (this operation
       updates the configuration file to reflect
       the acquisition)'''
    # Read our configuration data (JSON)
    _cfg = get_config_data()

    # Find a Server Group that's both
    # available and clean
    for k, group in enumerate(_cfg):
        if (not group.get('deployment')) and (not group.get('removed')):
            # Let other deployments know that we're
            # using this particular Server Group
            _cfg[k]['deployment'] = ctx.deployment.id

            # Write updated data to our config file
            with open(CFG_FILE_PATH, 'w') as f_cfg:
                json.dump(_cfg, f_cfg)

            return group


def release_server_groups():
    '''Searches for all server groups that
       are currently acquired by the active deployment
       and releases the server group for use by other
       deployments'''
    # Read our configuration data (JSON)
    _cfg = get_config_data()

    # Search for any Server Groups
    # marked as dirty (removed) and remove
    # the from the configuration data.
    # Removes the object if it's corrupted
    _cfg[:] = [x for x in _cfg if x.get('removed', True)]

    # Search for any Server Groups that
    # are in use by our current deployment.
    # Mark those Server Groups as available.
    for k, group in enumerate(_cfg):
        if group.get('deployment') == ctx.deployment.id:
            _cfg[k]['deployment'] = None

    # Replace the configuration file with
    # our new configuration data
    overwrite_config_data(_cfg)


# Entry point for the Facilitator
@operation
@with_nova_client
def configure(nova_client, **kwargs):
    '''Entry point for the Facilitator module'''
    del kwargs
    ctx.logger.info('Querying OpenStack for (Anti-)Affinity Server Groups')
    _os_data = get_openstack_server_groups(nova_client)

    try:
        with LOCK:
            ctx.logger.info('Creating / Updating configuration data')
            create_config_data_if_needed(_os_data)
            print_config_data()

            ctx.logger.info('Selecting an OpenStack Server Group to use')
            selected_group = acquire_server_group()
            print_config_data()

            if not selected_group:
                NonRecoverableError('There are no available OpenStack '
                                    'Server Groups for use')

            ctx.logger.info('Using OpenStack Server Group {0}'
                            . format(selected_group.get('id')))

        # Iterate through each dependent node instance and
        # update their runtime_properties
        hosts = discover_dependent_hosts()
        for host in hosts:
            ctx.logger.info('Assigning (Anti-)Affinity Group '
                            '{0} to host {1}'
                            . format(selected_group.get('id'), host.id))
            #host.runtime_properties['server_group'] = selected_group.get('id')
    except filelock.Timeout:
        RecoverableError('Timeout waiting for OpenStack Server Groups '
                         'configuration file to be released for use')


@operation
def delete(**kwargs):
    '''Cloudify "delete" lifecycle operation'''
    del kwargs
    try:
        with LOCK:
            ctx.logger.info('Releasing (Anti-)Affinity Group(s) '
                            'from deployment {0}'
                            . format(ctx.deployment.id))
            release_server_groups()
    except filelock.Timeout:
        RecoverableError('Timeout waiting for OpenStack Server Groups '
                         'configuration file to be released for use')
