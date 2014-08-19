import os
import time
import pytest
import poseidon.api as P
from poseidon import connect
from poseidon.client import Client


# TODO need test account?

TEST_API_KEY=os.environ.get('TEST_DIGITALOCEAN_API_KEY', None)


@pytest.fixture
def client():
    client = connect(api_key=TEST_API_KEY)
    assert isinstance(client, Client)
    return client


def test_keys(client):
    # TODO this test is a little flakey after the update call
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

    time.sleep(2)
    client.keys.update(new_id, 'test-key2')
    time.sleep(2)
    key = client.keys.get(new_id)
    assert key['name'] == 'test-key2'

    client.keys.delete(new_id)
    assert len(client.keys.list()) == len(old_keys)


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
    domain = client.domains.create(test, ip_address)
    new_name = domain['name']
    assert new_name == test
    new_domains = client.domains.list()
    assert len(new_domains) > len(old_domains)

    records = client.domains.records(domain['name'])
    assert isinstance(records, P.DomainRecords)
    result = records.create('A', name='foo-record', data='127.0.0.1')
    id = result['id']
    expected = records.get(id)
    assert result['name'] == expected['name']

    records.rename(id, 'new-record')
    result = records.get(id)
    assert result['name'] == 'new-record'

    domain = client.domains.get(new_name)
    assert domain['name'] == test

    client.domains.delete(new_name)
    assert len(client.domains.list()) == len(old_domains)
