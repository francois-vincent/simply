# encoding: utf-8

import pytest

from ..platform import Platform, Backend, single_multiple


def test_manager():
    class FailingBackend(Backend):
        def build(self):
            raise IndexError('fake')

    class GoodBackend(Backend):
        def build(self):
            return self

    with pytest.raises(AttributeError):
        Platform('').build()

    with pytest.raises(AttributeError):
        Platform('').pre_setup('build')

    with pytest.raises(IndexError):
        Platform('', backend=FailingBackend()).build()

    assert Platform('', backend=GoodBackend()).build()


def test_single_multiple():
    class Test(Platform):
        hosts = {'h1': 'container1', 'h2': 'container2'}
        @single_multiple
        def get_hosts(self, host, a, b=None):
            return self.hosts[host]
        @single_multiple
        def get_none(self, host, *args, **kwargs):
            pass

    t = Test('')
    assert t.get_hosts('', host='h1') == Test.hosts['h1']
    assert t.get_hosts('') == Test.hosts
    assert t.get_none() is t
    assert t.get_none(host='h1') is t
