# encoding: utf-8
"""
Platform description file
Contains
- a sequence of platforms to build / deploy
- specific methods to add to class Platform
"""

sequence = ['testimage', 'deployed', 'test_platform']
platforms = {
        'test_platform': {
            'backend': 'docker',
            'images': {'h1': 'testimage-deployed-host1', 'h2': 'testimage-deployed-host2'},
            'recipes': {'h1': 'depends:deployed', 'h2': 'depends:deployed'},
            'hosts': {'h1': 'test-deployed-host1', 'h2': 'test-deployed-host2'},
            'parameters': {'h1': '', 'h2': ''},
        },
        'deployed': {
            'backend': 'docker',
            'images': {'h1': 'testimage-deployed-host1', 'h2': 'testimage-deployed-host2'},
            'recipes': {'h1': 'depends:testimage', 'h2': 'depends:testimage'},
            'pre': [],
            'post': ['stop', 'commit'],
        },
        'testimage': {
            'backend': 'docker',
            'images': {'h1': 'testimage'},
            'recipes': {'h1': 'build:testimage'},
        }
    }


def test_method(self, host):
    """ method to test method injection into Platform class
        [deco:collapse_and]
    """
    return True
