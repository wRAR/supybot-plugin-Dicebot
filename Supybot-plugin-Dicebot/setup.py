#!/usr/bin/env python

plugins = [
	'Dicebot',
    ]

import sys

if sys.version_info < (2, 3, 0):
    sys.stderr.write("Supybot requires Python 2.3 or newer.\n")
    sys.exit(-1)

import glob
import shutil
import os.path

from distutils.core import setup
from distutils.sysconfig import get_python_lib

pluginFiles = glob.glob(os.path.join('.', '*.py'))

packages =  ['supybot.plugins.' + s for s in plugins]

package_dir = { }

for plugin in plugins:
    package_dir['supybot.plugins.' + plugin] = plugin

version = '0.2'
setup(
    name='supybot-plugin-dicebot',
    version=version,
    packages=packages,
    package_dir=package_dir,
    )


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
