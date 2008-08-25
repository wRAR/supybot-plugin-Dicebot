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
package_data = { }

for plugin in plugins:
    package_dir['supybot.plugins.' + plugin] = plugin
    package_data['supybot.plugins.' + plugin] = ['README.txt']

version = '0.2'
setup(
    name='supybot-plugin-dicebot',
    version=version,
    author='Andrey Rahmatullin',
    author_email='wrar@altlinux.ru',
    url='http://www.assembla.com/spaces/supybot-plugin-Dicebot',
    description='Dicebot plugin for Supybot',
    long_description='Dicebot plugin contains the commands which simulate rolling of dice.',
    packages=packages,
    package_dir=package_dir,
    package_data=package_data,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Games/Entertainment :: Board Games',
        ],
    )


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
