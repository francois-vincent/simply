# encoding: utf-8

import pytest


@pytest.mark.parametrize("image", ['conda2', 'conda3', 'debian8'])
def test_matrix(image):
    print('test on image <{}>'.format(image))
