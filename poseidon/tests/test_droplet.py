"""
Tests here are marked slow because they involve actually creating and destroying
a droplet
"""

import pytest
from poseidon.droplet import Droplets, DropletActions
from poseidon.ssh import SSHClient
from test_api import client


# TODO: test resize, restore, rebuild, change_kernel,
#       enable_ipv6, enable_private_networking
#       disable_backups


class DropletFixture(object):

    def __init__(self, client, name, region, size, image_id, **kwargs):
        self.client = client
        self.name = name
        self.region = region
        self.size = size
        self.image_id = image_id
        self.options = kwargs
        self._droplet = None

    def create(self):
        old_droplets = self.client.droplets.list()
        self._droplet = self.client.droplets.create(
            self.name, self.region, self.size, self.image_id,
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
    id = api.images.list()[0]['id']
    image_id = api.images.get(id).id

    fixture = DropletFixture(api, name, region, size, image_id)
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
    assert droplet.droplet_name == fixture.name
    assert droplet.region['slug'] == fixture.region
    assert droplet.size['slug'] == fixture.size
    assert droplet.image['id'] == fixture.image_id


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
    # HURF
    if client.droplets.get(fixture.droplet.id).status == 'off':
        fixture.droplet.power_on()
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
    assert client.droplets.get(fixture.droplet.id).droplet_name == 'new-name'

@pytest.mark.slow
def test_connect(fixture):
    con = fixture.droplet.connect(interactive=True)
    assert isinstance(con, SSHClient)
    assert con.interactive
