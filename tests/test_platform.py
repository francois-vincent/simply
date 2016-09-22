# encoding: utf-8

from ..platform import factory
from ..utils import ConfAttrDict


def test_platform_init():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='busybox',
    )
    platform = factory(conf)
    assert platform.backend == conf.backend
    assert platform.frontend == conf.frontend
    assert platform.init_backend
    assert platform.init_frontend
    assert platform.user is None
    assert platform.effective_user == 'root'
    assert platform.image == conf.image
    assert platform.image_spec == ''
    assert platform.container
    assert platform.parameters is None


