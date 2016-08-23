# encoding: utf-8

from importlib import import_module

from utils import (run_sequence, extract_column, read_configuration, collapse_none,
                    collapse_and, multiple, set_methods_from_conf)


class Backend(object):
    """
    Base class for all backends
    """
    @staticmethod
    def factory(platform, conf):
        backend = import_module('.' + conf['backend'], 'simply.backends')
        return backend.get_backend_class()(conf, platform)


class Platform(object):
    """
    A platform is a set of hosts managed through a backend.
    hosts = dict(hostname=address) where address can be an ip, a container name, etc...
    """

    @classmethod
    def factory(cls, conf):
        if isinstance(conf, basestring):
            conf = read_configuration(conf)
        set_methods_from_conf(cls, conf)
        platforms_conf = conf['platforms']
        sequence = conf['sequence'] if len(platforms_conf) > 1 else platforms_conf
        return [cls(platform, platforms_conf[platform]) for platform in sequence]

    def __init__(self, name, conf):
        self.name = name
        self.__dict__.update(conf)
        self.user = getattr(self, 'user', None)
        self.effective_user = self.user or 'root'
        self.backend = Backend.factory(self, conf)

    def __getattr__(self, item):
        if hasattr(self.backend, item):
            return getattr(self.backend, item)
        raise AttributeError("{} {} can't find {}, missing or bad backend".
                           format(self.__class__.__name__, self.name, item))

    def setup(self):
        run_sequence(self, *self.pre)
        yield self
        run_sequence(self, *self.post)

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

    # High Level utility methods
    # You can add methods via platform description file

    @collapse_none
    def get_processes(self, host, filter=None):
        """ Get the list of running processes, with optional filter
        """
        processes = extract_column(self.run_command('ps -A', host=host, user='root'), -1, 1)
        if filter is None:
            return processes
        return [proc for proc in processes if filter in proc]

    @collapse_none
    def create_user(self, host, user, groups=(), home=None, shell=None):
        """ Create a user with optional groups, home and shell
        """
        cmd = 'useradd {}{}{}'.\
            format(user,
                   ' -d {}'.format(home) if home else '',
                   ' -s {}'.format(shell) if shell else '')
        self.run_command(cmd, hot=host)
        existing_groups = extract_column(self.run_command('cat /etc/group', host=host), 0, sep=':')
        for group in groups:
            if group not in existing_groups:
                self.run_command('addgroup {}'.format(group), hot=host)
            self.run_command('usermod -a -G {} {}'.format(group, user), host=host)

    @collapse_and
    def path_exists(self, path, host):
        return self.test_comand('test -e {}'.format(path), host=host)


class AbstractPlatform(object):
    """
    This class is not intended to be instanciated nor derived
    It is only here to describe the Platform API
    """

    def __init__(self):
        raise NotImplementedError("{} is not instanciable".format(self.__class__.__name__))

    def start(self):
        """ Runs the platform
        """
        return self

    @multiple
    def run_command(self, command, host, input_data=None, raises=False):
        """ Runs a command and returns stdout (or dict)
        :param command: the command to run in bash
        :param host: a host name
        :param input_data: data to stream to stdin
        :param raises: if True, raises if the command fails on any host
        :return: stdout if host is specified or a dict {host: stdout, ...}
        """
        return 'stdout'

    @collapse_and
    def test_command(self, command, host):
        """ Runs a command and return True if it succeeds on all hosts, False if it fails on any host
        """
        return True
