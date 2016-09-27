# encoding: utf-8

import pytest

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


def test_platform_getattr():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='scratch',
    )
    platform = factory(conf)
    assert platform.init_backend
    assert platform.init_frontend
    with pytest.raises(AttributeError):
        platform.toto


def test_platform_pull():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='busybox',
        image_spec='.pull',
    )
    platform = factory(conf)
    assert platform.build_image('uproot')
    assert platform.image_exist()


def test_platform_build():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='scratch',
    )
    platform = factory(conf)
    assert platform.build_image('uproot')
    assert platform.image_exist()


def test_platform_run():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='busybox',
        image_spec='.pull',
    )
    platform = factory(conf)
    try:
        assert platform.setup('all_containers')
        assert platform.get_real_containers()
    finally:
        platform.reset()


def test_platform_execute():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='busybox',
        image_spec='.pull',
    )
    platform = factory(conf)
    try:
        assert platform.setup('all_containers')
        exe = platform.execute('mkdir -p /root/test_dir', stdout_only=False)
        assert exe.returncode == 0
        assert exe.stdout == ''
        assert platform.path_exists('/root/test_dir')
    finally:
        platform.reset()
