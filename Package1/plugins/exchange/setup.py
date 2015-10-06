from setuptools import setup

setup(
    name='key-exchange-plugin',
    description='A Cloudify plugin to exchange public keys between dynamically instanciated nodes',
    version='0.85',
    author='Joshua Cornutt',
    author_email='josh@gigaspaces.com',
    packages=['plugin'],
    install_requires=[
        'cloudify-plugins-common>=3.2.1'
    ],
)