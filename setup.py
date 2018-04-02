#!/usr/bin/env python

from os.path import dirname, join
from distutils.core import setup


module_name = 'kachelmann_wetter_getter'

with open(join(dirname(__file__), module_name, 'VERSION'), 'rt') as f:
    version = f.read().strip()

setup(
    name='kachelmann-wetter-getter',
    version=version,
    description='Get weather data from https://kachelmannwetter.com/',
    author='/u/plistig',
    author_email='https://www.reddit.com/message/compose/?to=plistig',
    python_requires='>=3.6',  # f-strings
    install_requires=(
        'cchardet >= 2.1.1',
        'dataclasses >= 0.5',
        'html5lib >= 1.0.1',
        'lxml >= 4.2.1',
        'requests >= 2.18.4',
        'semver >= 2.7.9',
    ),
    packages=(module_name,),
    package_data={
        module_name: ('*.py', 'VERSION'),
    },
)
