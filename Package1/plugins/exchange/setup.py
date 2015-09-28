from setuptools import setup

setup(
    name='key-exchange-plugin',
    description='A Cloudify plugin to exchange information between dynamically instanciated nodes',
    version='0.1',
    author='Joshua Cornutt',
    author_email='josh@gigaspaces.com',
    packages=['plugin'],
    install_requires=[
        'cloudify-plugins-common>=3.2.1'
    ],
)