# encoding: utf-8

from .. import backends
from .. import frontends
from ..utils import ConfAttrDict


class FakePlatform(object):
    user = None
    execute = None


def test_backend():
    backend = backends.factory(FakePlatform, ConfAttrDict(backend='docker', image='toto'))
    assert backend.type == 'docker'
    assert backend.platform == FakePlatform
    backend2 = backends.factory(FakePlatform, ConfAttrDict(backend='docker', image='toto'))
    assert backend is not backend2


def test_frontend():
    frontend = frontends.factory(FakePlatform, ConfAttrDict(frontend='debian'))
    assert frontend.type == 'debian'
    assert frontend.platform == FakePlatform
    frontend2 = frontends.factory(FakePlatform, ConfAttrDict(frontend='debian'))
    assert frontend is frontend2
