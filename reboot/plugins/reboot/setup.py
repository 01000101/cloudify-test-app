from setuptools import setup

setup(
    name='reboot',
    description='A Cloudify plugin to gracefully handle instance rebooting',
    version='0.01',
    author='Joshua Cornutt',
    author_email='josh@gigaspaces.com',
    packages=['plugin'],
    install_requires=[
        'cloudify-plugins-common>=3.2',
        'cloudify-openstack-plugin>=1.2'
    ]
)
