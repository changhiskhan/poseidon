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
con = P.connect()
ssh_key_id = con.keys.list()[0]['id']
droplet = con.droplets.create('example.changshe.io', 'sfo1', '512mb',
                              'ubuntu-14-04-x64', ssh_keys=[ssh_key_id])
records = con.domains.create('example.changshe.io', droplet.ip_address)
records.create('A', data=droplet.ip_address)
ssh = droplet.connect()
ssh.apt('git python-pip')
ssh.git('changhiskhan', 'hello_world')
ssh.chdir('hello_world')
ssh.pip_r('requirements.txt')
ssh.nohup('python app.py') # flask goes to ip:5000 by default, DNS takes a while
print ssh.ps()
