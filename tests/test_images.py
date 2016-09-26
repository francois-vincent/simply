# encoding: utf-8

from .. import ROOTDIR
from ..platform import factory
from ..utils import ConfAttrDict


def test_debian8_py2():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='debian8_py2',
        parameters='-i -v {}:/root/simply'.format(ROOTDIR)
    )
    platform = factory(conf)
    assert platform.setup('all_containers')
    assert 'Python 2.7' in platform.execute('python -V', stdout_only=False).stderr
    assert platform.execute('pip install pytest')
    assert 'version' in platform.execute('py.test --version', stdout_only=False).stderr


def test_conda2():
    conf = ConfAttrDict(
        backend='docker',
        frontend='busybox',
        image='conda2',
        parameters='-i -v {}:/root/simply'.format(ROOTDIR)
    )
    platform = factory(conf)
    assert platform.setup('all_containers')
    assert 'Python 2.7' in platform.execute('python -V', stdout_only=False).stderr
    assert platform.execute('pip install pytest')
    assert 'version' in platform.execute('py.test --version', stdout_only=False).stderr


def test_conda3():
    conf = ConfAttrDict(
        backend='docker',
        frontend='busybox',
        image='conda3',
        parameters='-i -v {}:/root/simply'.format(ROOTDIR)
    )
    platform = factory(conf)
    assert platform.setup('all_containers')
    assert 'Python 3.' in platform.execute('python -V', stdout_only=False).stderr
    assert platform.execute('pip install pytest')
    assert 'version' in platform.execute('py.test --version', stdout_only=False).stderr
