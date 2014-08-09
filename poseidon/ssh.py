import os
import getpass
from cStringIO import StringIO

# make these optional so not everyone has to build C binaries
try:
    import pandas as pd
    if pd.__version__ <= '0.13.1':
        raise ImportError
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

    def __init__(self, host, username='root', password=None, port=None,
                 interactive=False):
        """
        Parameters
        ----------
        interactive: bool, default False
            If True then prompts for password whenever necessary
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.interactive = interactive
        self.pwd = '~'
        self._con = None

    @property
    def con(self):
        if self._con is None:
            self._connect()
        return self._con

    def _connect(self):
        if not has_paramiko:
            raise ImportError("Unable to import paramiko")
        self._con = paramiko.SSHClient()
        self._con.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        kwargs = {}
        for k in ['username', 'password', 'port']:
            if getattr(self, k, None):
                kwargs[k] = getattr(self, k)
        self._con.connect(self.host, **kwargs)

    def chdir(self, new_pwd, relative=True):
        if new_pwd and self.pwd and relative:
            new_pwd = os.path.join(self.pwd, new_pwd)
        self.pwd = new_pwd

    def add_public_key(self, key_path):
        self.password = self.validate_password(self.password)
        key_contents = open(os.path.expanduser(key_path)).read()
        cmd = 'mkdir -p ~/.ssh && cat "%s"  ~/.ssh/authorized_keys'
        self.wait(cmd % key_contents)

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
        if self.pwd is not None:
            cmd = 'cd %s ; %s' % (self.pwd, cmd)
        if self.interactive:
            print cmd
        return self.con.exec_command(cmd)

    def wait(self, cmd, raise_on_error=True):
        """
        Execute command and wait for it to finish. Proceed with caution because
        if you run a command that causes a prompt this will hang
        """
        _, stdout, stderr = self.exec_command(cmd)
        stdout.channel.recv_exit_status()
        output = stdout.read()
        if self.interactive:
            print output
        errors = stderr.read()
        if self.interactive:
            print errors
        if errors and raise_on_error:
            raise ValueError(errors)
        return output

    def nohup(self, cmd):
        """
        Execute the command using nohup and &
        """
        cmd = "nohup %s &" % cmd
        self.exec_command(cmd)

    def sudo(self, password=None):
        """
        Enter sudo mode
        """
        if self.username == 'root':
            raise ValueError('Already root user')
        password = self.validate_password(password)
        stdin, stdout, stderr = self.exec_command('sudo su')
        stdin.write("%s\n" % password)
        stdin.flush()
        errors = stderr.read()
        if errors:
            raise ValueError(errors)

    def validate_password(self, password):
        if password is None:
            password = self.password
        if password is None and self.interactive:
            password = getpass.getpass()
        if password is None:
            raise ValueError("Password must not be empty")
        return password

    def unsudo(self):
        """
        Assume already in sudo
        """
        self.wait('exit')

    def apt(self, package_names, raise_on_error=False):
        """
        Install specified packages using apt-get. -y options are
        automatically used. Waits for command to finish.

        Parameters
        ----------
        package_names: list-like of str
        raise_on_error: bool, default False
            If True then raise ValueError if stderr is not empty
            debconf often gives tty error
        """
        if isinstance(package_names, basestring):
            package_names = [package_names]
        cmd = "apt-get install -y %s" % (' '.join(package_names))
        return self.wait(cmd, raise_on_error=raise_on_error)

    def curl(self, url, raise_on_error=True, **kwargs):
        import simplejson as json
        def format_param(name):
            if len(name) == 1:
                prefix = '-'
            else:
                prefix = '--'
            return prefix + name
        def format_value(value):
            if value is None:
                return ''
            return json.dumps(value)
        options = ['%s %s' % (format_param(k), format_value(v))
                   for k, v in kwargs.items()]
        cmd = 'curl %s "%s"' % (' '.join(options), url)
        return self.wait(cmd, raise_on_error=raise_on_error)

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
        return self.wait(cmd, raise_on_error=raise_on_error)

    def pip_freeze(self, raise_on_error=True):
        """
        Run `pip freeze` and return output
        Waits for command to finish.
        """
        return self.wait('pip freeze', raise_on_error=raise_on_error)

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
        cmd = "pip install -r %s" % requirements
        return self.wait(cmd, raise_on_error=raise_on_error)

    def ps(self, args=None, options='', all=True, verbose=True,
           as_frame='auto', raise_on_error=True):
        if args is None:
            args = ''
        if all:
            args += 'A'
        if verbose:
            args += 'f'
        if len(args) > 0 and args[0] != '-':
            args = '-' + args

        results = self.wait(('ps %s %s' % (args, options)).strip(),
                            raise_on_error=raise_on_error)

        if as_frame == 'auto':
            as_frame = has_pandas

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

    def top(self):
        return self.ps('o', TOP_OPTIONS)

    def git(self, username, repo, alias=None, token=None):
        """
        Parameters
        ----------
        token: str, default None
            Assumes you have GITHUB_TOKEN in envvar if None

        https://github.com/blog/1270-easier-builds-and-deployments-using-git-
        over-https-and-oauth
        """
        if alias is None:
            alias = repo
        if token is None:
            token = os.environ.get('GITHUB_TOKEN')
        self.wait('mkdir -p %s' % alias)
        old_dir = self.pwd
        try:
            self.chdir(alias, relative=True)
            cmd = 'git init && git pull https://%s@github.com/%s/%s.git'
            # last line to stderr
            return self.wait(cmd % (token, username, repo),
                             raise_on_error=False)
        finally:
            self.chdir(old_dir, relative=False)

TOP_OPTIONS = '%cpu,%mem,user,comm'
