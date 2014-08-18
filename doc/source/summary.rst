Getting Started
===============

Installation
------------

.. code:: bash

    pip install -U poseidon

In order to authenticate with DigitalOcean, it is highly recommended that you
generate an API key via the DigitalOcean website and export it as the value of
the ``DIGITALOCEAN_API_KEY`` environment variable:

.. code:: bash

   export DIGITALOCEAN_API_KEY=<value>


Examples
--------

Once you have installed poseidon and setup the API key, connecting to API is
simple:

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

   # requires "GITHUB_TOKEN" envvar
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
-------

To run the test suite make sure you have the ``pytest`` module.

.. code:: bash

    pip install -U pytest
    py.test


Because the test for droplets goes through the exercise of creating a new droplet,
modifying it, then finally destroying it, the test takes a while to run.
To only run the other tests, use the "not slow" marker from "pytest":

.. code:: bash

    py.test -v -m "not slow"
