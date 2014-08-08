import os
import time
import pytest
from pytest_mock import mock

import threading
import paramiko
import socket
import poseidon.ssh as S


def get_path(filename):
    root_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(root_path, filename)


# ripped from paramiko unit tests

KEY = b'\x44\x78\xf0\xb9\xa2\x3c\xc5\x18\x20\x09\xff\x75\x5b\xc1\xd2\x6c'

class NullServer (paramiko.ServerInterface):

    def get_allowed_auths(self, username):
        if username == 'slowdive':
            return 'publickey,password'
        return 'publickey'

    def check_auth_password(self, username, password):
        if (username == 'slowdive') and (password == 'pygmalion'):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        if (key.get_name() == 'ssh-dss') and key.get_fingerprint() == KEY:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def check_channel_exec_request(self, channel, command):
        if command != 'yes':
            return False
        return True


class SSHClientFixture(object):

    def __init__(self):
        self.sock = socket.socket()
        self.sock.bind(('localhost', 0))
        self.sock.listen(1)
        self.addr, self.port = self.sock.getsockname()
        self.event = threading.Event()

    def tearDown(self):
        if self.event is not None:
            self.event.set()
        for attr in "tc ts socks sockl".split():
            if hasattr(self, attr):
                getattr(self, attr).close()
        time.sleep(0.1)

    def run(self):
        self.socks, addr = self.sock.accept()
        self.ts = paramiko.Transport(self.socks)
        host_key = paramiko.RSAKey.from_private_key_file(
            get_path('test_rsa.key'))
        self.ts.add_server_key(host_key)
        server = NullServer()
        self.ts.start_server(self.event, server)

    def stdout(self, response, delay=False):
        if delay:
            def stdout():
                time.sleep(0.1)
                self._stdout(response)
            threading.Thread(target=stdout).start()
        else:
            self._stdout(response)

    def _stdout(self, response):
        schan = self.ts.accept(1.0)
        schan.send('%s' % response)
        schan.close()

    def stderr(self, response, delay=False):
        if delay:
            def stderr():
                time.sleep(0.1)
                self._stderr(response)
            threading.Thread(target=stderr).start()
        else:
            self._stdout(response)

    def _stderr(self, response):
        schan = self.ts.accept(1.0)
        schan.send_stderr('%s' % response)
        schan.close()


@pytest.fixture()
def pair(request):
    server = SSHClientFixture()
    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()

    client = S.SSHClient(server.addr, port=server.port,
                         username='slowdive',
                         password='pygmalion')

    def fin():
        server.tearDown()
        client.close()
    request.addfinalizer(fin)

    return client, server


@pytest.fixture()
def client():
    return S.SSHClient('localhost', username='foo', password='')


def test_basic(pair, mock):
    client, server = pair
    # connect
    con = client.con
    assert isinstance(con, paramiko.SSHClient)

    stdin, stdout, stderr = client.exec_command('yes')
    assert isinstance(stdin, paramiko.channel.ChannelFile)
    assert isinstance(stdout, paramiko.channel.ChannelFile)
    assert isinstance(stderr, paramiko.channel.ChannelFile)

    server.stdout('ok')
    assert stdout.read().strip() == 'ok'

    client.close()
    assert client._con is None


def test_wait(pair):
    client, server = pair
    server.stdout('ok', delay=True)
    output = client.wait('yes')
    assert output == 'ok'


def test_nohup(client, mock):
    mock.patch.object(S.SSHClient, 'exec_command')
    client.nohup('foo')
    client.exec_command.assert_called_with('nohup foo &')


def test_unsudo(client, mock):
    mock.patch.object(S.SSHClient, 'wait')
    client.unsudo()
    client.wait.assert_called_with('exit')


def test_apt(client, mock):
    mock.patch.object(S.SSHClient, 'wait')
    client.apt(['foo', 'bar', 'baz'])
    expected = 'apt-get install -y --force-yes foo bar baz'
    client.wait.assert_called_with(expected, raise_on_error=True)


def test_curl(client, mock):
    mock.patch.object(S.SSHClient, 'wait')
    client.curl('api.foo.io', H="Authorization: Bearer <token>")
    expected = 'curl -H "Authorization: Bearer <token>" "api.foo.io"'
    client.wait.assert_called_with(expected, raise_on_error=True)


def test_pip(client, mock):
    mock.patch.object(S.SSHClient, 'wait')
    client.pip(['foo', 'bar', 'baz'])
    expected = 'pip install -U foo bar baz'
    client.wait.assert_called_with(expected, raise_on_error=True)


def test_pip_freeze(client, mock):
    mock.patch.object(S.SSHClient, 'wait')
    client.pip_freeze()
    client.wait.assert_called_with('pip freeze', raise_on_error=True)


def test_pip_r(client, mock):
    mock.patch.object(S.SSHClient, 'wait')
    fdir = '~/poseidon/requirements.txt'
    client.pip_r(fdir)
    fdir = os.path.expanduser(fdir)
    client.wait.assert_called_with('pip install -r %s' % fdir,
                                   raise_on_error=True)


def test_ps(client, mock):
    mock.patch.object(S.SSHClient, 'wait')
    client.ps()
    client.wait.assert_called_with('ps -Af', raise_on_error=True)


def test_top(client, mock):
    mock.patch.object(S.SSHClient, 'ps')
    client.top()
    client.ps.assert_called_with('o', S.TOP_OPTIONS)
