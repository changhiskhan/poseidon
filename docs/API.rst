
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
