import time

from poseidon.api import Resource
from poseidon.ssh import SSHConnection

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
