from __future__ import print_function, absolute_import

import os
from setuptools import setup, find_packages

VERSION = "0.3.1"

def write_version_py(filename=None):
    cnt = """\
version = '%s'
"""
    if not filename:
        filename = os.path.join(
            os.path.dirname(__file__), 'poseidon', 'version.py')

    a = open(filename, 'w')
    try:
        print(VERSION)
        a.write(cnt % (VERSION,))
    finally:
        a.close()

write_version_py()

DOWNLOAD_URL = ('https://github.com/changhiskhan/poseidon/archive/%s.tar.gz' %
                VERSION)
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Operating System :: OS Independent',
    'Intended Audience :: Developers',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7'
]

SUMMARY = "Digital Ocean API v2 with SSH integration"

DESCRIPTION = """
********************************
poseidon: tame the digital ocean
********************************

Python library for managing your Digital Ocean account

.. image:: https://pypip.in/v/poseidon/badge.png
    :target: https://crate.io/packages/poseidon/
    :alt: Latest PyPI version

.. image:: https://pypip.in/d/poseidon/badge.png
    :target: https://crate.io/packages/poseidon/
    :alt: Number of PyPI downloads

The DigitalOcean API allows you to manage Droplets and resources within the
DigitalOcean cloud in a simple, programmatic way using conventional HTTP
requests. The endpoints are intuitive and powerful, allowing you to easily make
calls to retrieve information or to execute actions.

This library starts with a python wrapper for the API and aims to build tools to
make it easier to manage, provision, and deploy to Digital Ocean.

Highlights
==========

- **Full featured**: API wrapper covering the published DigitalOcean API v2

- **Tested**: integration test coverage against most of the API

- **SSH integration**: integrates ``paramiko`` library so you can SSH in
and issue commands

- **Deployment conveniences**: methods like ``apt``, ``pip``, and ``git`` for
easier deployment

Example
=======

Deploy a new Flask app from github

.. code:: python

    import poseidon as P
    client = P.connect()
    ssh_key_id = client.keys.list()[0]['id']
    droplet = client.droplets.create('example.changshe.io', 'sfo1', '512mb',
                                  'ubuntu-14-04-x64', ssh_keys=[ssh_key_id])
    domain = client.domains.create('example.changshe.io', droplet.ip_address)
    records = client.domains.records(domain['name'])
    records.create('A', data=droplet.ip_address)
    ssh = droplet.connect()
    ssh.apt('git python-pip')
    ssh.git(username='changhiskhan', repo='hello_world')
    ssh.chdir('hello_world')
    ssh.pip_r('requirements.txt')
    ssh.nohup('python app.py') # DNS takes a while to propagate
    print ssh.ps()
"""

setup(
    name='poseidon',
    version=VERSION,
    author='Chang She',
    packages = find_packages(),
    url='https://github.com/changhiskhan/poseidon',
    license='MIT',
    keywords=['digitalocean', 'digital ocean', 'digital', 'ocean', 'api', 'v2',
              'web programming', 'cloud', 'digitalocean api v2'],
    description=DESCRIPTION,
    classifiers=CLASSIFIERS,
    download_url=DOWNLOAD_URL,
    package_data={'': ['requirements.txt']},
    install_requires = [
        'requests',
        'paramiko',
    ],
)
