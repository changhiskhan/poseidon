Python library for managing your Digital Ocean account API v2

The DigitalOcean API allows you to manage Droplets and resources within the
DigitalOcean cloud in a simple, programmatic way using conventional HTTP
requests. The endpoints are intuitive and powerful, allowing you to easily make
calls to retrieve information or to execute actions.

All of the functionality that you are familiar with in the DigitalOcean control
panel is also available through the API, allowing you to script the complex
actions that your situation requires.

This library starts with a python wrapper for the API and aims to build tools to
make it easier to manage, provision, and deploy to Digital Ocean.


Setup
*****

.. code:: bash

    pip install -U poseidon

To run the unit tests make sure you have the 'pytest' module.
If not, run

.. code:: bash

   pip install -U pytest


Examples
********

Setup authentication by generating an API key and exporting it as the value of the
"DIGITALOCEAN_API_KEY" environment variable:

.. code:: bash

   export DIGITALOCEAN_API_KEY=<value>


Connect to API
~~~~~~~~~~~~~~

.. code:: python

   import poseidon.api as po
   client = po.connect() # or po.connect(api_key=<KEY>) for custom api key


Create a droplet
~~~~~~~~~~~~~~~~

.. code:: python

   image_id = 135123 # replace with your own
   droplet = client.droplets.create(name='test', region='sfo1', size='512mb',
                                    image=image_id)


Programmatically create a snapshot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    droplet.power_off() # snapshots are only allowed while powered off
    droplet.take_snapshot('test-snapshot')


Check that it worked
~~~~~~~~~~~~~~~~~~~~

.. code:: python

    snapshots = droplet.snapshots() # one of these should be named 'test-snapshot'


Other simple droplet commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    droplet.reboot()
    droplet.shutdown()
    droplet.power_on()
    droplet.power_cycle()
    droplet.password_reset()
    droplet.enable_ipv6()
    droplet.disable_backups()
    droplet.enable_private_networking()


Droplet commands that take a parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    droplet.resize('1024mb')
    droplet.restore(image_id) # integer
    droplet.rebuild(image_id)
    droplet.rename('new-name')
    droplet.change_kernel(12534)


Waiting for pending actions to complete
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    droplet.wait() # polls every 5 seconds until no more in-progress actions

Delete droplet
~~~~~~~~~~~~~~

.. code:: python

    droplet.delete()

Keys
~~~~

.. code:: python

    # list keys
    client.keys.list() # it works

    # create a new key
    public_key = ("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAQQDWF7SdoK0JvdjGR/8MHjj"
                  "b7qtKVSdqoVZ2bCX0SXdn2pxZitnFjUx+lQ4osMGjOOTE/Hi86qQnFGE8Ym"
                  "Sur/LT example")
    key = client.keys.create('test-key', public_key)
    print rs['public_key']
    print rs['name']

    # rename the key
    client.keys.update(key['id'], 'test-key2')

    # delete the key
    client.keys.delete(new_id)


Domains
~~~~~~~

.. code:: python

    # list domains
    client.domains.list() # it works

    # create new domain
    ip_address = '127.0.0.1'
    test = 'b7qtKVSdqoVZ2bCX0SXdn2pxZitnFjUx.com' # must be unique
    domain = client.domains.create(test, ip_address)
    print domain['name']

    # retrieve a domain by name
    new_domain = client.domains.get(domain['name'])

    # delete a domain by name
    client.domains.delete(new_domain['name'])


Regions
~~~~~~~

.. code:: python

    client.regions.list()


Sizes
~~~~~

.. code:: python

    client.sizes.list()


Testing
*******

.. code:: bash

    pip install -U pytest
    py.test

Because the test for droplets goes through the exercise of creating a new droplet,
modifying it, then finally destroying it, the test takes a long time to run.
To only run the other tests, use the "not slow" marker from "pytest":

.. code:: bash

    ~$ py.test -v -m "not slow"
    ===================================== test session starts ======================================
    platform linux2 -- Python 2.7.6 -- py-1.4.23 -- pytest-2.6.0 --
    collected 8 items

    tests/test_api.py@72::test_regions PASSED
    tests/test_api.py@82::test_sizes PASSED
    tests/test_api.py@92::test_actions PASSED
    tests/test_api.py@101::test_keys PASSED
    tests/test_api.py@122::test_domains PASSED
    tests/test_api.py@141::test_domain_records PASSED
    tests/test_api.py@145::test_images PASSED

    ============================ 1 tests deselected by "-m 'not slow'" =============================
    ============================ 7 passed, 1 deselected in 6.85 seconds ============================


TODO
****

1. Refactor the result format to allow for easy multipage resultset paging
2. Additional unit tests
3. Tools for scaling, provisioning, deployment
