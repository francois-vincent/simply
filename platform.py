# encoding: utf-8

import os.path

from .utils import run_sequence, extract_column


def platform_method(func):
    setattr(Platform, func.__name__, single_multiple(func))


def single_multiple(meth):
    def wrapper(self, *args, **kwargs):
        host = kwargs.pop('host', None)
        if host:
            ret = meth(self, host, *args, **kwargs)
            return self if ret is None else ret
        else:
            ret = {k: meth(self, k, *args, **kwargs) for k in self.hosts}
            return self if all(x is None for x in ret.itervalues()) else ret
    return wrapper


class Backend(object):
    """
    Base class for all backends
    """


class Platform(object):
    """
    A platform is a set of hosts managed through a backend.
    hosts = dict(hostname=address) where address can be an ip, a container name, etc...
    There are 3 types of backends:
    - buildable platforms like test backends (docker or VM),
    - runnable (thus stoppable) backends (docker or VM),
    - non buildable non runnable backends.
    """

    def __init__(self, name, backend=None):
        self.name = name
        self.backend = backend
        if isinstance(backend, basestring):
            self.read_configuration(backend)
        # self.user = user
        # self.effective_user = user or 'root'

    def read_configuration(self, conf_file):
        if not os.path.isfile(conf_file):
            raise RuntimeError("File %s not found" % conf_file)
        self.conf = {}
        execfile(conf_file, {}, self.conf)

    def __getattr__(self, item):
        if hasattr(self.backend, item):
            return getattr(self.backend, item)
        raise AttributeError("{} {} can't find {}, missing or bad backend".
                           format(self.__class__.__name__, self.name, item))

    def pre_setup(self, *args):
        return run_sequence(self, *args)

    def post_teardown(self, *args):
        self.post = args
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        run_sequence(self, getattr(self, 'post', ()))

    def name_from_host(self, host):
        for k, v in self.hosts.iteritems():
            if v == host:
                return k
        raise LookupError("{} {} not found".format(self.host_name, host))

    # Utility methods
    # You can add

    @single_multiple
    def get_processes(self, host, filter=None):
        """ Get the list of running processes, with optional filter
        """
        processes = extract_column(self.run_command('ps -A', host, user='root'), -1, 1)
        if filter is None:
            return processes
        return [proc for proc in processes if filter in proc]

    @single_multiple
    def create_user(self, host, user, groups=(), home=None, shell=None):
        """ Create a user with optional groups, home and shell
        """
        cmd = 'useradd {}{}{}'.\
            format(user,
                   ' -d {}'.format(home) if home else '',
                   ' -s {}'.format(shell) if shell else '')
        self.run_command(cmd, host)
        existing_groups = extract_column(self.run_command('cat /etc/group', host), 0, sep=':')
        for group in groups:
            if group not in existing_groups:
                self.run_command('addgroup {}'.format(group), host)
            self.run_command('usermod -a -G {} {}'.format(group, user), host)


class AbstractPlatform(object):
    """
    This class is not intended to be instanciated nor derived
    It is only here to describe the Platform API
    """

    def __init__(self):
        raise NotImplementedError("{} is not instanciable".format(self.__class__.__name__))

    def run_platform(self):
        """ Runs the platform if it is runnable
        """
        return self

    def run_command(self, command, host=None, input_data=None, raises=False):
        """ Runs a command and returns stdout (or dict)
        :param command: the command to run in bash
        :param host: a host name
        :param input_data: data to stream to stdin
        :param raises: if True, raises is any one of the commands fails
        :return: stdout if host is specified or a dict {host: stdout, ...}
        """
        return 'stdout'
