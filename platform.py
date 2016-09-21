# encoding: utf-8

import backends
import frontends


class Platform(object):
    """
    A platform is an abstraction of an host with a backend (docker, ...) and a frontend (distribution)
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
