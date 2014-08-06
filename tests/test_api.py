import os
import time
import pytest
import poseidon.api as P

# TODO need test account?

TEST_API_KEY=os.environ.get('TEST_DIGITALOCEAN_API_KEY', None)


@pytest.fixture
def client():
    client = P.connect(api_key=TEST_API_KEY)
    assert isinstance(client, P.Client)
    return client

def test_keys(client):
    assert hasattr(client, 'keys')
    assert isinstance(client.keys, P.Keys)
    old_keys = client.keys.list() # it works
    public_key = ("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAQQDWF7SdoK0JvdjGR/8MHjj"
                  "b7qtKVSdqoVZ2bCX0SXdn2pxZitnFjUx+lQ4osMGjOOTE/Hi86qQnFGE8Ym"
                  "Sur/LT example")
    rs = client.keys.create('test-key', public_key)
    new_id = rs['id']
    assert public_key == rs['public_key']
    new_keys = client.keys.list()
    assert len(new_keys) > len(old_keys)

    client.keys.update(new_id, 'test-key2')
    time.sleep(2) # race condition
    key = client.keys.get(new_id)
    assert key['name'] == 'test-key2'

    client.keys.delete(new_id)
    assert len(client.keys.list()) == len(old_keys)


@pytest.mark.slow
def test_droplets(client):
    """
    WARNING this test takes a while :)
    """
    assert hasattr(client, 'droplets')
    assert isinstance(client.droplets, P.Droplets)
    old_droplets = client.droplets.list() # it works

    name = 'test-droplet'
    region = 'sfo1'
    size = '512mb'
    id = client.images.list()[0]['id']
    image = client.images.get(id)

    droplet = client.droplets.create(name, region, size, image.id)

    try:
        # verify we got what we made
        assert isinstance(droplet, P.DropletActions)
        assert droplet.droplet_name == name
        assert droplet.region['slug'] == region
        assert droplet.size['slug'] == size
        assert droplet.image['slug'] == image.slug

        assert len(client.droplets.list()) > len(old_droplets)

        # just check that the request works for now
        droplet.kernels()
        old_snapshots = droplet.snapshots()
        droplet.backups()

        # A few actions
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
    finally:
        droplet.delete()

    assert len(client.droplets.list()) == len(old_droplets)


def test_regions(client):
    assert hasattr(client, 'regions')
    assert isinstance(client.regions, P.Regions)
    regions = client.regions.list() # it works
    expected = set([u'New York 1', u'Amsterdam 1', u'San Francisco 1',
                    u'New York 2', u'Amsterdam 2', u'Singapore 1', u'London 1'])
    results = set([x['name'] for x in regions])
    assert expected == results


def test_sizes(client):
    assert hasattr(client, 'sizes')
    assert isinstance(client.sizes, P.Sizes)
    sizes = client.sizes.list() # it works
    results = set([x['slug'] for x in sizes])
    expected = set([u'512mb', u'1gb', u'2gb', u'4gb', u'8gb', u'16gb', u'32gb',
                    u'48gb', u'64gb'])
    assert expected == results


def test_actions(client):
    assert hasattr(client, 'actions')
    assert isinstance(client.actions, P.Actions)
    actions = client.actions.list() # it works
    assert len(actions) > 0 # need a test account
    action = client.actions.get(actions[0]['id'])
    assert action == actions[0]


def test_domains(client):
    assert hasattr(client, 'domains')
    assert isinstance(client.domains, P.Domains)
    old_domains = client.domains.list() # it works
    ip_address = '127.0.0.1'
    test = 'b7qtKVSdqoVZ2bCX0SXdn2pxZitnFjUx.com'
    rs = client.domains.create(test, ip_address)
    new_name = rs['name']
    assert new_name == test
    new_domains = client.domains.list()
    assert len(new_domains) > len(old_domains)

    domain = client.domains.get(new_name)
    assert domain['name'] == test

    client.domains.delete(new_name)
    assert len(client.domains.list()) == len(old_domains)


def test_domain_records(client):
    pass


def test_images(client):
    pass
