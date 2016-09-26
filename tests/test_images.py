# encoding: utf-8

from .. import ROOTDIR
from ..platform import factory
from ..utils import ConfAttrDict


def test_build():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='debian8_py2',
        parameters='-i -v {}:/root/simply'.format(ROOTDIR)
    )
    platform = factory(conf)
    assert platform.setup('all_containers')
    assert '2.7' in platform.execute('python -V', stdout_only=False).stderr
    assert platform.execute('pip install clingon')
    assert 'version' in platform.execute('clingon -V', stdout_only=False).stderr
