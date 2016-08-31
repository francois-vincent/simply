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
            'images': {'h1': 'testimage-deployed-host', 'h2': 'testimage-deployed-host'},
            'hosts': {'h1': 'test-deployed-host1', 'h2': 'test-deployed-host2'},
            'parameters': {'h1': '', 'h2': ''},
        },
        'deployed': {
            'backend': 'docker',
            'images': {'h1': 'testimage-deployed-host'},
            'pre': [('build', 'testimage')],
            'post': ['stop', 'commit', 'rm'],
        },
    }


def test_method(self, host):
    """ method to test method injection into Platform class
        [deco:collapse_and]
    """
    return True
