Working with Droplets via SSH
=============================

In addition to an API wrapper, ``poseidon`` allows you to connect to a droplet
and issue terminal commands via SSH


Connect to droplet via SSH
--------------------------

Assume you have a droplet called "test", you can use the name to retrieve the
droplet and create an SSH connection to it.

.. code:: python

   import poseidon.api as po
   client = po.connect()
   droplet = client.droplets.by_name('test')
   ssh = droplet.connect(interactive=True)

When the ``interactive`` parameter is True, the SSH connection will prompt for
a password when appropriate (e.g., when calling ``sudo`` without a password).
It will also cause the connection to print the output to the console.

You can of course close the connection:

.. code:: python

   ssh.close()



Issuing commands over SSH
-------------------------

Once you have the SSH connection, you can execute arbitrary commands over SSH

``exec_command`` returns ``paramiko`` Channel objects that act like python's
stdin, stdout, stderr

.. code:: python

   cmd = 'echo foo'
   stdin, stdout, stderr = ssh.exec_command(cmd)

There is a convenience method ``wait`` that reads the stdout and returns it.
If anything is in stderr then an exception is raised.

.. code:: python

   output = ssh.wait('echo foo') # output=='foo\n'

Be careful with using ``wait`` because if you issue a command that results in
a prompt, it will cause your python session to block forever.


Change the current directory
----------------------------

You can use the ``chdir`` method to change the current directory. Because each
command is essentially a new connection, issuing ``cd`` command does not work
across multiple commands. As a result, ``poseidon`` actually saves the value of
the directory you passed into ``chdir`` and issues the ``cd`` command with every
new command.


Starting processes via ``nohup``
--------------------------------

If you want to start long running processes that survive the session, use the
``nohup`` convenience method. It is equivalent to issuing ``nohup <cmd> &`` in
bash

.. code:: python

   ssh.nohup('python start_server.py')


Installing system packages via ``apt``
--------------------------------------

If you need to install system packages, you can give them to the ``apt`` method
as a list. This is equivalent to issuing ``apt-get install -y <packages>``

.. code:: python

   ssh.apt('git python-pip')


Cloning repositories via ``git``
--------------------------------

Use the git convenience method to clone a repository. You can omit the ``token``
parameter if you have the ``GITHUB_TOKEN`` environment variable. If the droplet does
not have git installed, you will have to use ``apt`` to install it first.

.. code:: python

   ssh.git('changhiskhan', 'test')


Working with python via ``pip``
-------------------------------

Use the ``pip`` method to install a single or a list of python packages. This assumes
``python-pip`` is installed on your system. If not, you can use the ``apt`` method to
do so

.. code:: python

   ssh.pip('flask')

To get a list of currently install packages, you can use the ``pip_freeze`` method.
This is equivalent to ``pip freeze`` and returns the output.

.. code:: python

   print ssh.pip_freeze()

If you wish to install all packages in a remote file, use the ``pip_r`` method. This
is equivalent to issuing ``pip install -r /path/to/requirements.txt`` on the droplet.
Note that the path you pass in is the *remote* path.

.. code:: python

   ssh.pip_r('/path/to/requirements.txt')


Monitoring processes via ``ps`` and ``top``
-------------------------------------------

The ``ps`` method returns stats about the running processes. It is equivalent
to running ``ps -Af`` by default and takes in optional arguments.

.. code:: python

   result = ssh.ps()

The top method actually uses ps and is equivalent to
``ps -Afo %cpu,%mem,user,comm``

.. code:: python

   result = ssh.top()


If you have pandas>=0.13.1 the output is returned as a DataFrame
