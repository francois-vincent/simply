# encoding: utf-8

from importlib import import_module


def get_module(conf):
    return import_module('.' + (conf if isinstance(conf, basestring) else conf['frontend']), 'simply.frontends')


def get_class(conf):
    return get_module(conf).this_class
