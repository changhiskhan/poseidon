#!/usr/bin/env python
"""
Take a snapshot of a droplet
"""
import plac

import poseidon.api as po


def get_first():
    """
    return first droplet
    """
    client = po.connect() # this depends on the DIGITALOCEAN_API_KEY envvar
    all_droplets = client.droplets.list()
    id = all_droplets[0]['id'] # I'm cheating because I only have one droplet
    return client.droplets.get(id)


def take_snapshot(droplet, name):
    """
    Take a snapshot of a droplet

    Parameters
    ----------
    name: str
        name for snapshot
    """
    print "powering off"
    droplet.power_off()
    droplet.wait() # wait for pending actions to complete
    print "taking snapshot"
    droplet.take_snapshot(name)
    droplet.wait()
    snapshots = droplet.snapshots()
    print "Current snapshots"
    print snapshots


def main(name):
    droplet = get_first()
    take_snapshot(droplet, name)


if __name__ == '__main__':
    plac.call(main)
