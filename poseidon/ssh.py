import os
from cStringIO import StringIO
try:
    import pandas as pd
    has_pandas = True
except ImportError:
    has_pandas = False

try:
    import paramiko
    has_paramiko = True
except ImportError:
    has_paramiko = False



class SSHClient(object):
    """
    Thin wrapper to connect to client over SSH and execute commands
    """

    def __init__(self, host, username='root', password=None):
        self.host = host
        self.username = username
        self.password = password
        self._con = None

    @property
    def con(self):
        if self._con is None:
            self._connect()
        return self.con

    def _connect(self):
        if not has_paramiko:
            raise ImportError("Unable to import paramiko")
        self._con = paramiko.SSHClient()
        self._con.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        self._con.connect(self.host, username=self.username,
                          password=self.password)

    def close(self):
        if self._con is not None:
            self._con.close()
            self._con = None

    def exec_command(self, cmd):
        """
        Proceed with caution, if you run a command that causes a prompt and then
        try to read/print the stdout it's going to block forever

        Returns
        -------
        (stdin, stdout, stderr)
        """
        return self._con.exec_command(cmd)

    def wait(self, cmd):
        """
        Execute command and wait for it to finish. Proceed with caution because
        if you run a command that causes a prompt this will hang
        """
        return self._wrap_cmd(cmd)

    def nohup(self, cmd):
        """
        Execute the command using nohup
        """
        cmd = "nohup %s &" % cmd
        self._con.exec_command(cmd)

    def sudo(self, password=None):
        """
        Enter sudo mode
        """
        if self.username == 'root':
            raise ValueError('Already root user')
        if password is None:
            password = self.password
        if password is None:
            raise ValueError("Password must not be empty")
        stdin, stdout, stderr = self.exec_command('sudo su')
        stdin.write("%s\n" % password)
        stdin.flush()
        output = stdout.read()
        errors = stderr.read()
        if errors:
            raise ValueError(errors)
        return output

    def unsudo(self):
        """
        Assume already in sudo
        """
        return self._wrap_cmd('exit')

    def _wrap_cmd(self, cmd, raise_on_error=True):
        _, stdin, stdout, stderr = self.exec_command(cmd)
        stdout.channel.recv_exit_status()
        output = stdout.read()
        errors = stderr.read()
        if errors and raise_on_error:
            raise ValueError(errors)
        return output

    def apt(self, package_names, raise_on_error=True):
        """
        Install specified packages using apt-get. -y and --force-yes options are
        automatically used. Waits for command to finish.

        Parameters
        ----------
        package_names: list-like of str
        raise_on_error: bool, default True
            If True then raise ValueError if stderr is not empty
        """
        if isinstance(package_names, basestring):
            package_names = [package_names]
        cmd = "apt-get install -y --force-yes %s" % (' '.join(package_names))
        return self._wrap_cmd(cmd, raise_on_error=raise_on_error)

    def curl(self, url, raise_on_error=True, **kwargs):
        import simplejson as json
        def format_param(name):
            if len(name) == 1:
                prefix = '='
            else:
                prefix = '--'
            return prefix + name
        def format_value(value):
            if value is None:
                return ''
            return json.dumps(value)
        options = ['%s %s' % (format_param(k), format_value(v))
                   for k, v in kwargs]
        cmd = 'curl %s "%s"' % (' '.join(options), url)
        return self._wrap_cmd(cmd, raise_on_error=raise_on_error)

    def pip(self, package_names, raise_on_error=True):
        """
        Install specified python packages using pip. -U option added
        Waits for command to finish.

        Parameters
        ----------
        package_names: list-like of str
        raise_on_error: bool, default True
            If True then raise ValueError if stderr is not empty
        """
        if isinstance(package_names, basestring):
            package_names = [package_names]
        cmd = "pip install -U %s" % (' '.join(package_names))
        return self._wrap_cmd(cmd, raise_on_error=raise_on_error)

    def pip_freeze(self, raise_on_error=True):
        """
        Run `pip freeze` and return output
        Waits for command to finish.
        """
        return self._wrap_cmd('pip freeze', raise_on_error=raise_on_error)

    def pip_r(self, requirements, raise_on_error=True):
        """
        Install all requirements contained in the given file path
        Waits for command to finish.

        Parameters
        ----------
        requirements: str
            Path to requirements.txt
        raise_on_error: bool, default True
            If True then raise ValueError if stderr is not empty
        """
        cmd = "pip install -r %s" % os.path.expanduser(requirements)
        return self._wrap_cmd(cmd, raise_on_error=raise_on_error)

    def ps(self, options=None, all=True, verbose=True, as_frame=True,
           raise_on_error=True):
        if options is None:
            options = ''
        if all:
            options += 'A'
        if verbose:
            options += 'f'
        if len(options) > 0 and options[0] != '-':
            options = '-' + options

        results = self._wrap_cmd('ps %s' % options,
                                 raise_on_error=raise_on_error)
        if as_frame:
            if not has_pandas:
                raise ImportError("Unable to import pandas")
            df = pd.read_fwf(StringIO(results))
            cmd_loc = df.columns.get_loc('CMD')
            if cmd_loc < len(df.columns):
                col = cmd_loc.fillna('')
                for i in range(cmd_loc + 1, len(df.columns)):
                    col = col + df.icol(i).fillna('')
                df['CMD'] = col
            return df

        return results
