# encoding: utf-8

import simply

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('HISTORY.rst') as f:
    history = f.read().replace('.. :changelog:', '')

requirements = ['future', 'wheel']
test_requirements = ['pytest']


setup(
    name='simply',
    version=simply.__version__,
    description="Test applications and packages in any Linux context",
    long_description=history + '\n\n',
    author=simply.__author__,
    author_email='francois.vincent01@gmail.com',
    url=simply.__github__,
    packages=['simply', 'simply.backends', 'simply.frontends'],
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='development tests integration_tests',
    classifiers=[
        # 'Development Status ::  3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Environment :: Console',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
