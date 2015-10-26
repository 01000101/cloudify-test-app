'''(Anti-)Affinity Server Groups Pool plugin for Cloudify's OpenStack plugin'''

from setuptools import setup

setup(
    name='affinity',
    description='A Cloudify plugin to handle server groups',
    version='0.1',
    author='Joshua Cornutt',
    author_email='josh@gigaspaces.com',
    packages=['plugin'],
    install_requires=[
        'cloudify-plugins-common>=3.2.1',
        'cloudify-openstack-plugin>=1.2.1',
        'filelock>=2.0.4'
    ]
)
