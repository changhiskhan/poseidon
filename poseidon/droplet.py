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

    name = 'droplets'

    def kernels(self, id):
        return self._prop(id, 'kernels')

    def snapshots(self, id):
        return self._prop(id, 'snapshots')

    def backups(self, id):
        return self._prop(id, 'backups')

    def actions(self, id):
        return self._prop(id, 'actions')

    def _prop(self, id, prop):
        return super(MutableCollection, self).get((id, prop))[prop]

    def create(self, name, region, size, image, ssh_keys=None,
               backups=None, ipv6=None, private_networking=None, wait=True):
        """
        Parameters
        ----------
        ssh_keys: list, optional
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
        info = super(Droplets, self).get(id)
        return DropletActions(self.api, self, **info)

    def by_name(self, name):
        for d in self.list():
            if d['name'] == name:
                return self.get(d['id'])
        raise KeyError("Could not find droplet with name %s" % name)

    def update(self, id, **kwargs):
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
        for k, v in kwargs.iteritems():
            if k == 'name':
                k = 'droplet_name'
            setattr(self, k, v)

    @property
    def name(self):
        return 'droplets/%s/actions' % self.id

    def get_action(self, action_id):
        return self.get((action_id,)).get('action')

    def _action(self, type, wait=True, **kwargs):
        result = self.post(type=type, **kwargs)
        if wait:
            self.wait()
        return result

    def reboot(self, wait=True):
        return self._action('reboot', wait)

    def power_cycle(self, wait=True):
        return self._action('power_cycle', wait)

    def shutdown(self, wait=True):
        return self._action('shutdown', wait)

    def power_off(self, wait=True):
        return self._action('power_off', wait)

    def power_on(self, wait=True):
        return self._action('power_on', wait)

    def password_reset(self, wait=True):
        return self._action('password_reset', wait)

    def enable_ipv6(self, wait=True):
        return self._action('enable_ipv6', wait)

    def disable_backups(self, wait=True):
        return self._action('disable_backups', wait)

    def enable_private_networking(self, wait=True):
        return self._action('enable_private_networking', wait)

    def resize(self, size, wait=True):
        return self._action('resize', size=size, wait=wait)

    def restore(self, image, wait=True):
        return self._action('restore', image=image, wait=wait)

    def rebuild(self, image, wait=True):
        return self._action('rebuild', image=image, wait=wait)

    def rename(self, name, wait=True):
        return self._action('rename', name=name, wait=wait)

    def change_kernel(self, kernel_id, wait=True):
        return self._action('change_kernel', kernel=kernel_id, wait=wait)

    def take_snapshot(self, name, wait=True):
        return self._action('snapshot', name=name, wait=wait)

    def kernels(self):
        return self.parent.kernels(self.id)

    def snapshots(self):
        return self.parent.snapshots(self.id)

    def backups(self):
        return self.parent.backups(self.id)

    def actions(self):
        return self.parent.actions(self.id)

    def delete(self, wait=True):
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
        """
        rs = SSHClient(self.ip_address, interactive=interactive)
        return rs
