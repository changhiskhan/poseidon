import time

from poseidon.api import Resource, MutableCollection
from poseidon.ssh import SSHClient


class Droplets(MutableCollection):
    """
    A Droplet is a DigitalOcean virtual machine. By sending requests to the
    Droplet endpoint, you can list, create, or delete Droplets.

    Some of the attributes will have an object value. The region, image, and
    size objects will all contain the standard attributes of their associated
    types. Find more information about each of these objects in their
    respective sections.
    """

    resource_path = 'droplets'

    def kernels(self, id):
        """
        Return all kernels for a given droplet

        Parameters
        ----------
        id: int
            Droplet id
        """
        return self._prop(id, 'kernels')

    def snapshots(self, id):
        """
        Return all snapshots for a given droplet

        Parameters
        ----------
        id: int
            Droplet id

        Notes
        -----
        backups are automatic, are setup at droplet creation, cost extra,
        and does not require the droplet to be powered off
        snapshots are manual, on demand, free, but requires the droplet
        to be powered off first
        """
        return self._prop(id, 'snapshots')

    def backups(self, id):
        """
        Return all backups for a given droplet

        Parameters
        ----------
        id: int
            Droplet id

        Notes
        -----
        backups are automatic, are setup at droplet creation, cost extra,
        and does not require the droplet to be powered off
        snapshots are manual, on demand, free, but requires the droplet
        to be powered off first
        """
        return self._prop(id, 'backups')

    def actions(self, id):
        """
        Return all actions for a given droplet (completed and otherwise)

        Parameters
        ----------
        id: int
            Droplet id
        """
        return self._prop(id, 'actions')

    def _prop(self, id, prop):
        return super(MutableCollection, self).get((id, prop))[prop]

    def create(self, name, region, size, image, ssh_keys=None,
               backups=None, ipv6=None, private_networking=None, wait=True):
        """
        Create a new droplet

        Parameters
        ----------
        name: str
            Name of new droplet
        region: str
            slug for region (e.g., sfo1, nyc1)
        size: str
            slug for droplet size (e.g., 512mb, 1024mb)
        image: int or str
            image id (e.g., 12352) or slug (e.g., 'ubuntu-14-04-x64')
        ssh_keys: list, optional
            default SSH keys to be added on creation
            this is highly recommended for ssh access
        backups: bool, optional
            whether automated backups should be enabled for the Droplet.
            Automated backups can only be enabled when the Droplet is created.
        ipv6: bool, optional
            whether IPv6 is enabled on the Droplet
        private_networking: bool, optional
            whether private networking is enabled for the Droplet. Private
            networking is currently only available in certain regions
        wait: bool, default True
            if True then block until creation is complete
        """
        if ssh_keys and not isinstance(ssh_keys, (list, tuple)):
            raise TypeError("ssh_keys must be a list")
        resp = self.post(name=name, region=region, size=size, image=image,
                         ssh_keys=ssh_keys,
                         private_networking=private_networking,
                         backups=backups, ipv6=ipv6)
        droplet = self.get(resp[self.singular]['id'])
        if wait:
            droplet.wait()
        # HACK sometimes the IP address doesn't return correctly
        droplet = self.get(resp[self.singular]['id'])
        return droplet

    def get(self, id):
        """
        Retrieve a droplet by id

        Parameters
        ----------
        id: int
            droplet id

        Returns
        -------
        droplet: DropletActions
        """
        info = self._get_droplet_info(id)
        return DropletActions(self.api, self, **info)

    def _get_droplet_info(self, id):
        return super(Droplets, self).get(id)

    def by_name(self, name):
        """
        Retrieve a droplet by name (return first if duplicated)

        Parameters
        ----------
        name: str
            droplet name

        Returns
        -------
        droplet: DropletActions
        """
        for d in self.list():
            if d['name'] == name:
                return self.get(d['id'])
        raise KeyError("Could not find droplet with name %s" % name)

    def update(self, id, **kwargs):
        """
        A droplet cannot be updated via POST
        """
        raise NotImplementedError("Not supported by API")



class DropletActions(Resource):
    """
    Droplet actions are tasks that can be executed on a Droplet. These can be
    things like rebooting, resizing, snapshotting, etc.

    Droplet action requests are generally targeted at the "actions" endpoint
    for a specific Droplet. The specific actions are usually initiated by
    sending a POST request with the action and arguments as parameters.

    Droplet actions themselves create a Droplet actions object. These can be
    used to get information about the status of an action.
    """
    def __init__(self, api, collection, **kwargs):
        super(DropletActions, self).__init__(api)
        self.id = kwargs.pop('id')
        self.parent = collection
        self._init_attrs(**kwargs)

    def _init_attrs(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def refresh(self):
        info = self.parent._get_droplet_info(self.id)
        self._init_attrs(**info)

    @property
    def resource_path(self):
        return 'droplets/%s/actions' % self.id

    def get_action(self, action_id):
        """
        Retrieve a single action based on action_id
        """
        return self.get((action_id,)).get('action')

    def _action(self, type, wait=True, **kwargs):
        result = self.post(type=type, **kwargs)
        if wait:
            self.wait()
        return result

    def reboot(self, wait=True):
        """
        According to DigitalOcean API this is best efforts only

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('reboot', wait)

    def power_cycle(self, wait=True):
        """
        Hard reset

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('power_cycle', wait)

    def shutdown(self, wait=True):
        """
        According to DigitalOcean API this is best efforts only

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('shutdown', wait)

    def power_off(self, wait=True):
        """
        Equivalent to hitting the power button. This is a "hard shutoff"

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('power_off', wait)

    def power_on(self, wait=True):
        """
        Turn on this droplet.

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed

        Raises
        ------
        APIError if droplet is already powered on
        """
        return self._action('power_on', wait)

    def password_reset(self, wait=True):
        """
        Send password reset email for this droplet

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('password_reset', wait)

    def enable_ipv6(self, wait=True):
        """
        Turn on IPv6 networking for this droplet

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed

        Raises
        ------
        APIError if region does not support IPv6
        """
        return self._action('enable_ipv6', wait)

    def disable_backups(self, wait=True):
        """
        Disable automatic backups for the droplet. Automatic backups
        can only be turned on at droplet creation

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed

        Raises
        ------
        APIError if region does not support IPv6
        """
        return self._action('disable_backups', wait)

    def enable_private_networking(self, wait=True):
        """
        Turn on private networking for this droplet. Private networking
        enables non-public IP for droplet

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed

        Raises
        ------
        APIError if region does not support private networking
        """
        return self._action('enable_private_networking', wait)

    def resize(self, size, wait=True):
        """
        Change the size of this droplet (must be powered off)

        Parameters
        ----------
        size: str
            size slug, e.g., 512mb
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('resize', size=size, wait=wait)

    def restore(self, image, wait=True):
        """
        Restore this droplet with given image id

        A Droplet restoration will rebuild an image using a backup image.
        The image ID that is passed in must be a backup of the current Droplet
        instance. The operation will leave any embedded SSH keys intact.

        Parameters
        ----------
        image: int or str
            int for image id and str for image slug
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('restore', image=image, wait=wait)

    def rebuild(self, image, wait=True):
        """
        Rebuild this droplet with given image id

        Parameters
        ----------
        image: int or str
            int for image id and str for image slug
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('rebuild', image=image, wait=wait)

    def rename(self, name, wait=True):
        """
        Change the name of this droplet

        Parameters
        ----------
        name: str
            New name for the droplet
        wait: bool, default True
            Whether to block until the pending action is completed

        Raises
        ------
        APIError if region does not support private networking
        """
        return self._action('rename', name=name, wait=wait)

    def change_kernel(self, kernel_id, wait=True):
        """
        Change the kernel of this droplet

        Parameters
        ----------
        kernel_id: int
            Can be retrieved from output of self.kernels()
        wait: bool, default True
            Whether to block until the pending action is completed

        Raises
        ------
        APIError if region does not support private networking
        """
        return self._action('change_kernel', kernel=kernel_id, wait=wait)

    def take_snapshot(self, name, wait=True):
        """
        Take a snapshot of this droplet (must be powered off)

        Parameters
        ----------
        name: str
            Name of the snapshot
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        return self._action('snapshot', name=name, wait=wait)

    def kernels(self):
        """
        List of available kernels for this droplet

        Example
        -------
        [{
          "id": 61833229,
          "name": "Ubuntu 14.04 x32 vmlinuz-3.13.0-24-generic",
          "version": "3.13.0-24-generic"
         },
         {
          "id": 485432972,
          "name": "Ubuntu 14.04 x64 vmlinuz-3.13.0-24-generic (1221)",
          "version": "3.13.0-24-generic"
         }]
        """
        return self.parent.kernels(self.id)

    def snapshots(self):
        """
        List of snapshots that have been created for this droplet
        """
        return self.parent.snapshots(self.id)

    def backups(self):
        """
        List of automated backups that have been created for this droplet
        """
        return self.parent.backups(self.id)

    def actions(self):
        """
        Action history on this droplet
        """
        return self.parent.actions(self.id)

    def delete(self, wait=True):
        """
        Delete this droplet

        Parameters
        ----------
        wait: bool, default True
            Whether to block until the pending action is completed
        """
        resp = self.parent.delete(self.id)
        if wait:
            self.wait()
        return resp

    def wait(self):
        """
        wait for all actions to complete on a droplet
        """
        interval_seconds = 5
        while True:
            actions = self.actions()
            slept = False
            for a in actions:
                if a['status'] == 'in-progress':
                    # n.b. gevent will monkey patch
                    time.sleep(interval_seconds)
                    slept = True
                    break
            if not slept:
                break

    @property
    def ip_address(self):
        """
        Public ip_address
        """
        ip = None
        for eth in self.networks['v4']:
            if eth['type'] == 'public':
                ip = eth['ip_address']
                break
        if ip is None:
            raise ValueError("No public IP found")
        return ip

    @property
    def private_ip(self):
        """
        Private ip_address
        """
        ip = None
        for eth in self.networks['v4']:
            if eth['type'] == 'private':
                ip = eth['ip_address']
                break
        if ip is None:
            raise ValueError("No private IP found")
        return ip

    def connect(self, interactive=False):
        """
        Open SSH connection to droplet

        Parameters
        ----------
        interactive: bool, default False
            If True then SSH client will prompt for password when necessary
            and also print output to console
        """
        rs = SSHClient(self.ip_address, interactive=interactive)
        return rs
