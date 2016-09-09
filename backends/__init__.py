# encoding: utf-8

from importlib import import_module


def factory(platform, conf):
    backend = import_module('.' + conf['backend'], 'simply.backends')
    return backend.get_instance(platform, conf)
