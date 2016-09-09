# encoding: utf-8

import backends
import frontends


class Platform(object):
    """
    A platform is a set of hosts managed through a backend.
    hosts = dict(hostname=address) where address can be an ip, a container name, etc...
    It is also a sequence of construction steps
    """

    def __init__(self, conf, **kwargs):
        self.__dict__.update(conf)
        self.__dict__.update(kwargs)
        self.user = getattr(self, 'user', None)
        self.effective_user = self.user or 'root'
        self.backend = backends.factory(self, conf)
        self.frontend = frontends.factory(self, conf)

    def __getattr__(self, item):
        if hasattr(self.backend, item):
            return getattr(self.backend, item)
        elif hasattr(self.frontend, item):
            return getattr(self.frontend, item)
        raise AttributeError("{} {} can't find {} in backend {} nor frontend {}".
                           format(self.__class__.__name__, self.name, item,
                                  self.backend.name, self.frontend.type))

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, *args):
        pass

    def name_from_host(self, host):
        for k, v in self.hosts.iteritems():
            if v == host:
                return k
        raise LookupError("{} {} not found".format(self.host_name, host))

