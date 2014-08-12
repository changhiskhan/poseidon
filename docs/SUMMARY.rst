Python library for managing your Digital Ocean account API v2

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

- **SSH integration**: integrates `paramiko` library so you can SSH in and issue commands

- **Deployment conveniences**: methods like `apt`, `pip`, and `git` for easier deployment


Setup
=====

.. code:: bash

    pip install -U poseidon


Examples
========

Setup authentication by generating an API key and exporting it as the value of the
"DIGITALOCEAN_API_KEY" environment variable:

.. code:: bash

   export DIGITALOCEAN_API_KEY=<value>


Connect to API:

.. code:: python

   import poseidon.api as po
   client = po.connect() # or po.connect(api_key=<KEY>) for custom api key

Create a droplet:

.. code:: python

   image = 'ubuntu-14-04-x64'
   key_id = client.keys.list()[0]['id'] # must be created first
   droplet = client.droplets.create(name='test', region='sfo1', size='512mb',
                                    image=image_id, ssh_keys=[key_id])

Programmatically create a snapshot:

.. code:: python

   droplet.power_off() # snapshots are only allowed while powered off
   droplet.take_snapshot('test-snapshot')

Check that it worked:

.. code:: python

   snapshots = droplet.snapshots() # one of these should be named 'test-snapshot'

Issuing commands to the droplet via SSH
poseidon connects to your droplet via SSH using the ``paramiko`` library

Create a connection:

.. code:: python

   ssh = droplet.connect()

Install system packages:

.. code:: python

   ssh.apt('git python-pip')

Clone github repo:

.. code:: python

   # requires `GITHUB_TOKEN` envvar
   ssh.git(username='changhiskhan', repo='hello_world')

Change directory:

.. code:: python

   ssh.chdir('hello_world')

Install requirements:

.. code:: python

   ssh.pip_r('requirements.txt') # pip install -r requirements.txt

Launch the application:

.. code:: python

   ssh.nohup('python app.py')

Check processes:

.. code:: python

   print ssh.ps() # ps -Af


Testing
=======

To run the test suite make sure you have the ``pytest`` module.

.. code:: bash

    pip install -U pytest
    py.test


Because the test for droplets goes through the exercise of creating a new droplet,
modifying it, then finally destroying it, the test takes a while to run.
To only run the other tests, use the "not slow" marker from "pytest":

.. code:: bash

    py.test -v -m "not slow"
