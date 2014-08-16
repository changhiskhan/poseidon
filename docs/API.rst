DigitalOcean API v2
===================

Using the ``requests`` library, poseidon offers a Python wrapper for
DigitalOcean's API v2.


Droplets
--------

Working with Droplets is going to be the bulk of how this API will be used.


Connect to API
~~~~~~~~~~~~~~

As a reminder, creating an API client instance is just a call to the
``connect`` function

.. code:: python

   import poseidon.api as po
   client = po.connect()


Create a droplet
~~~~~~~~~~~~~~~~

You can use the client to create a droplet given the appropriate specifications:

.. code:: python

   slug = 'ubuntu-14-04-x64'
   droplet = client.droplets.create(name='test', region='sfo1', size='512mb',
                                    image=slug)


Deleting a droplet
~~~~~~~~~~~~~~~~~~

.. code:: python

   droplet.delete()


Turning droplet on and off
~~~~~~~~~~~~~~~~~~~~~~~~~~

If the droplet is in the off state, you can always turn it on:

.. code:: python

   droplet.power_on()


Shutdown and reboot are proper shutdown and reboot sequences. They are equivalent
to typing ``sudo shutdown now`` or ``sudo shutdown -r now``.

.. code:: python

   droplet.shutdown()
   droplet.power_on()
   droplet.reboot()


Hanging processes can sometime interrupt the normal shutdown/reboot sequence. In
that case, if you're unable to properly let the droplet shutdown, you can use a
hard shut-off. This is equivalent to holding the power button on your computer and
can result in corrupted data

.. code:: python

   droplet.power_off()

``power_cycle`` is the equivalent of a "hard reset"

.. code:: python

   droplet.power_cycle()


Backups and restoration
~~~~~~~~~~~~~~~~~~~~~~~

When the droplet is in the "off" state, you can take a snapshot

.. code:: python

   droplet.take_snapshot('name-of-snapshot')
   snapshots = droplet.snapshots() # one should be 'name-of-snapshot'


Unlike snapshots, backups are automatically performed if you enabled
them at droplet creation time. You can choose to turn it off later.

.. code:: python

   droplet.disable_backups()


If you have an image, whether through snapshot or backup, you can use
it to restore or rebuild a droplet.

Restores must use an image created from the same droplet

.. code:: python

   droplet.restore(image_id) # image_id must be an integer


Rebuild allows you to build the droplet from scratch with any valid image

.. code:: python

   droplet.rebuild(image_id)


Other droplet actions
~~~~~~~~~~~~~~~~~~~~~

You can change the name of your droplet:

.. code:: python

   droplet.rename('new-name')

If your droplet can be resized, you can programmatically resize it via the API

.. code:: python

    droplet.resize('1gb')

If you forgot your password, you can always reset it:

.. code:: python

    droplet.password_reset()


If you forgot to enable IPv6 at droplet creation time, you can still enable it
after:

.. code:: python

    droplet.enable_ipv6()


You can enable private networking if you're building a distributed system and
need to have components talk to each other:

.. code:: python

    droplet.enable_private_networking()


You can list the available kernels for this droplet

.. code:: python

   droplet.kernels()

And you can change the kernel for this droplet:

.. code:: python

    droplet.change_kernel(12534) # kernel_id


Droplet action history
~~~~~~~~~~~~~~~~~~~~~~

DigitalOcean keeps a history of actions performed on the droplet via the API.
When there is a pending action, no new actions are allowed to be performed.
``poseidon`` automatically waits until an action is complete before the action
function will return. You can explicitly tell a droplet to wait until all
in-progress actions are complete.

.. code:: python

    droplet.wait() # polls every 5 seconds



Keys
----

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
-------

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


DomainRecords
-------------

TODO


Actions
-------

TODO

Images
------

TODO

ImageActions
------------

TODO


Regions
-------

You can view available regions. Use the region names here as a reference
for droplet creation, transfer, etc.

.. code:: python

    client.regions.list()


Sizes
-----

You can view available droplet sizes. You can use this as a reference
to see what sizes are available in what regions and what the slug names
are for droplet creation or resizing

.. code:: python

    client.sizes.list()
