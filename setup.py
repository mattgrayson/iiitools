#!/usr/bin/env python

from distutils.core import setup

setup(
    name='iiitools',
    author='Matt Grayson',
    author_email='mattgrayson@uthsc.edu',
    url='http://library.uthsc.edu',
    description='Utilities for interacting with III Millennium WebPac. '
                'Primary goal is to retrieve and parse bibliographic '
                'records via the WebPac proto-MARC output.',
    long_description="""\
III Utils
-----
Utilities for interacting with III Millennium WebPac. Primary goal is to
retrieve and parse bibliographic records via the WebPac proto-MARC output.

Required: Python 2.5 or later
Required: httplib2 <http://code.google.com/p/httplib2/>
Required pymarc <http://github.com/edsu/pymarc>
-----

To install:
$ python setup.py install
""",
    version='1.04',
    py_modules=['iiitools'],
)