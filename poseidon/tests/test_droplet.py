"""
Tests here are marked slow because they involve actually creating and destroying
a droplet
"""
import os
import time

import pytest

import poseidon.api as P
from poseidon.droplet import Droplets, DropletActions
from poseidon.ssh import SSHClient
from test_api import client


# TODO: test resize, restore, rebuild, change_kernel,
#       enable_ipv6, enable_private_networking
#       disable_backups


class DropletFixture(object):

    def __init__(self, client, name, region, size, image, **kwargs):
        self.client = client
        self.name = name
        self.region = region
        self.size = size
        self.image = image
        self.options = kwargs
        self._droplet = None

    def create(self):
        old_droplets = self.client.droplets.list()
        self._droplet = self.client.droplets.create(
            self.name, self.region, self.size, self.image,
            **self.options)
        new_droplets = self.client.droplets.list()
        assert len(old_droplets) + 1 == len(new_droplets)
        return self._droplet

    def destroy(self):
        if self._droplet is not None:
            old_droplets = self.client.droplets.list()
            self._droplet.wait()
            self._droplet.delete()
            self._droplet = None
            new_droplets = self.client.droplets.list()
            assert len(old_droplets) - 1 == len(new_droplets)

    @property
    def droplet(self):
        if self._droplet is None:
            self.create()
        return self._droplet



@pytest.fixture(scope='module')
def fixture(request):
    api = client()
    name = 'test-droplet'
    region = 'sfo1'
    size = '512mb'
    image_slug = 'ubuntu-14-04-x64'
    ssh_key_id = None
    keys = api.keys.list()
    if keys and len(keys) > 0:
        ssh_key_id = keys[0]['id']
    fixture = DropletFixture(api, name, region, size, image_slug,
                             ssh_keys=[ssh_key_id])
    request.addfinalizer(fixture.destroy)
    return fixture


@pytest.mark.slow
def test_basic(client, fixture):
    """
    WARNING this test takes a while :)
    """
    assert hasattr(client, 'droplets')
    assert isinstance(client.droplets, Droplets)
    droplet = fixture.droplet # create new droplet

    # verify we got what we made
    assert isinstance(droplet, DropletActions)
    assert droplet.name == fixture.name
    assert droplet.region['slug'] == fixture.region
    assert droplet.size['slug'] == fixture.size
    assert droplet.image['slug'] == fixture.image

@pytest.mark.slow
def test_ssh_add_public_key(client, fixture):
    if fixture.options['ssh_keys'] is None:
        pytest.skip("Need to setup public key manually")
    droplet = fixture.droplet
    time.sleep(1)
    ssh = droplet.connect()
    file_path = os.path.expanduser('~/tmp/key.txt')
    content = 'test-key'
    with open(file_path, 'wb') as fh:
        fh.write(content)
        fh.flush()
    ssh.add_public_key(file_path, validate_password=False)
    output = ssh.wait('cat ~/.ssh/authorized_keys').strip()
    assert output[-len(content):] == content

# @pytest.mark.slow
# only in Singapore right now ?
# def test_resize(client, fixture):
#     fixture.droplet.power_off()
#     fixture.droplet.resize('1gb')
#     fixture.droplet.power_on()
#     assert fixture.droplet.size == '1gb'


@pytest.mark.slow
def test_enable_private_networking(client, fixture):
    fixture.droplet.power_off()
    fixture.droplet.enable_private_networking() # works
    fixture.droplet.power_on()


@pytest.mark.slow
def test_change_kernel(client, fixture):
    kernels = fixture.droplet.kernels()
    fixture.droplet.change_kernel(kernels[0]['id'])
    fixture.droplet.refresh()
    assert fixture.droplet.kernel['id'] == kernels[0]['id']


@pytest.mark.slow
def test_by_name(client, fixture):
    expected = fixture.droplet
    result = client.droplets.by_name(fixture.name)
    assert expected.id == result.id


@pytest.mark.slow
def test_kernels(client, fixture):
    assert len(fixture.droplet.kernels()) > 0


@pytest.mark.slow
def test_backups(client, fixture):
    # works
    fixture.droplet.backups()


@pytest.mark.slow
def test_take_snapshot(client, fixture):
    droplet = fixture.droplet
    old_snapshots = droplet.snapshots()
    # power off
    droplet.power_off()
    # take snapshot
    droplet.take_snapshot('foobarbaz')
    new_snapshots = droplet.snapshots()
    assert len(new_snapshots) > len(old_snapshots)
    for x in new_snapshots:
        if x['name'] == 'foobarbaz':
            snapshot = x

    # image and image actions
    client.images.list() # all images historical
    assert hasattr(client, 'images')
    assert isinstance(client.images, P.Images)

    id = snapshot['id']
    im = client.images.get(id)
    assert im.id == id

    assert isinstance(im, P.ImageActions)
    im.transfer('nyc1')
    # assert new_im.regions[0] == 'nyc1' # wait too long

    client.images.delete(snapshot['id'])


@pytest.mark.slow
def test_power_cycle(client, fixture):
    resp = fixture.droplet.power_cycle()
    assert resp['action']['type'] == 'power_cycle'
    assert client.droplets.get(fixture.droplet.id).status == 'active'


@pytest.mark.slow
def test_reboot(client, fixture):
    resp = fixture.droplet.reboot()
    assert resp['action']['type'] == 'reboot'
    assert client.droplets.get(fixture.droplet.id).status == 'active'

@pytest.mark.slow
def test_shutdown(client, fixture):
    resp = fixture.droplet.shutdown()
    assert resp['action']['type'] == 'shutdown'
    # shutdown is 'best efforts'
    if client.droplets.get(fixture.droplet.id).status == 'off':
        resp = fixture.droplet.power_on()
        assert resp['action']['type'] == 'power_on'
        assert client.droplets.get(fixture.droplet.id).status == 'active'


@pytest.mark.slow
def test_password_reset(client, fixture):
    resp = fixture.droplet.password_reset()
    assert resp['action']['type'] == 'password_reset'


@pytest.mark.slow
def test_rename(client, fixture):
    resp = fixture.droplet.rename('new-name')
    assert resp['action']['type'] == 'rename'
    # tests refresh
    fixture.droplet.refresh()
    assert fixture.droplet.name == 'new-name'

@pytest.mark.slow
def test_connect(fixture):
    con = fixture.droplet.connect(interactive=True)
    assert isinstance(con, SSHClient)
    assert con.interactive
