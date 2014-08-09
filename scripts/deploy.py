import poseidon as P
con = P.connect()
droplet = con.create('example.changshe.io', 'sfo1', '512mb', 'ubuntu1404',
                     ssh_keys=['changhispad'])
con.records.create('A', 'example.changshe.io', data=droplet.ip_address)
ssh = droplet.connect()
ssh.apt('git')
ssh.wait('cd /tmp')
ssh.git('changhiskhan', 'hello_world')
ssh.pip_r('requirements.txt')
ssh.nohup('python app.py')
