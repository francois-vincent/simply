# encoding: utf-8

import pytest

from ..platform import Platform, Backend, collapse_none


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

