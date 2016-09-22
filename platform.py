# encoding: utf-8

from .utils import mixin_factory
import backends
import frontends


def get_class(conf):
    return mixin_factory('Platform', Platform, backends.get_class(conf), frontends.get_class(conf))


def factory(conf, **kwargs):
    return get_class(conf)(conf, **kwargs)


class Platform(object):
    """
    A platform is an abstraction of a host with a backend (docker, ...) and a frontend (an OS)
    """

    def __init__(self, conf, **kwargs):
        self.__dict__.update(conf)
        self.__dict__.update(kwargs)
        self.init_backend(conf)
        self.init_frontend(conf)

    def __getattr__(self, item):
        if hasattr(self.backend, item):
            return getattr(self.backend, item)
        elif hasattr(self.frontend, item):
            return getattr(self.frontend, item)
        raise AttributeError("{} {} can't find {} in backend {} nor frontend {}".
                           format(self.__class__.__name__, self.name, item,
                                  self.backend.name, self.frontend.type))

    def __enter__(self):
        self.setup_backend()
        self.setup_frontend()
        return self

    def __exit__(self, *args):
        pass
