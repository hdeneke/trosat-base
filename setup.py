#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of the TROPOS Satellite Library (TROSAT) developed 
# within the satellite work group at TROPOS.
#
# TROSAT is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors/Contributors/Copyright(2012-2020):
# - Hartwig Deneke (deneke@tropos.de)
# - Sebastian Bley
# - Fabian Senf
# - Frank Werner
# - Jonas Witthuhn

import glob
import pathlib
from setuptools import setup

setup(
    name         = 'trosat-base',
    version      = '0.9b1',
    author       = 'Hartwig Deneke', 
    author_email = 'deneke@tropos.de',
    scripts      = glob.glob('bin/*.py'),
    packages     = [ 'trosat' ],
    package_dir  = { '': 'src' },
    url          = 'https://github.com/hdeneke/trosat-base',
    python_requires  = '<3.10',
    install_requires = ["numpy",
                        "netCDF4",
                        "attrdict",
                        "jstyleson",
                       ]
)
