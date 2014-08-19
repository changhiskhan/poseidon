"""
Lucky number 13: deploy a dev Flask app from a github repo in 13 lines

one time setup needed:

1. export DIGITALOCEAN_API_KEY=<PAT>
2. export GITHUB_TOKEN=<token>
3. you must own domain and point DNS servers to digital ocean

Caveat emptor:
1. DNS takes a while to propagate so use ip address first
2. This is not a production deployment
"""

import poseidon as P
client = P.connect()
ssh_key_id = client.keys.list()[0]['id']
droplet = client.droplets.create('example.changshe.io', 'sfo1', '512mb',
                              'ubuntu-14-04-x64', ssh_keys=[ssh_key_id])
domain = client.domains.create('example.changshe.io', droplet.ip_address)
records = client.domains.records(domain['name'])
records.create('A', data=droplet.ip_address)
ssh = droplet.connect()
ssh.apt('git python-pip')
ssh.git(username='changhiskhan', repo='hello_world')
ssh.chdir('hello_world')
ssh.pip_r('requirements.txt')
ssh.nohup('python app.py') # flask goes to ip:5000 by default, DNS takes a while
print ssh.ps()
