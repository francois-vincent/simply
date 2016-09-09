# encoding: utf-8

from importlib import import_module


def factory(platform, conf):
    frontend = import_module('.' + conf['frontend'], 'simply.frontends')
    return frontend.get_instance(platform, conf)
