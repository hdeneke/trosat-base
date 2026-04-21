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
# Author/Copyright(2012-2026):
# * Hartwig Deneke (deneke@tropos.de)
#
# Contributors
# * Sebastian Bley
# * Fabian Senf
# * Frank Werner
# * Jonas Witthuhn

import json
from jsonpath_ng.ext import parse as _jp_parse_nocache
from functools import lru_cache
from operator import attrgetter
import hashlib

# cached parser for json-path expressions
_parse_jspath = lru_cache(_jp_parse_nocache)


def dict2uuid(d):
    '''
    Generate a uuid for a dict-like object

    Code based on:
    https://gist.github.com/azylinski/b61116f74c609cf3b7a4b28d7da65c96
    
    Parameters
    ----------
    d : dict-like
       the dictionary
    
    Returns
    -------
    uuid : str
       string corresponding to the UUID for the dictionary
    '''
    from uuid import NAMESPACE_DNS, uuid3
    # convert req to JSON
    jstr = json.dumps(d, sort_keys=True)
    # return uuid3 string
    return str(uuid3(NAMESPACE_DNS, jstr))


def get_jspath_node(d, jspth, *, type=None):
    '''
    get nodes from a nested dictionary using JSONPath expressions

    Parameters
    ----------
    d : dict-like
       the nested dictionary
    jspth : str
       a JSONPath string
    type : callable, optional
       a callable applied to the node

    Returns
    -------
    Any
        The node obtained from the nested dict or None
    '''

    jexpr = _parse_jspath(jspth)
    mtch = jexpr.find(d)
    if len(mtch)==0: return None
    mval = mtch[0].value
    return type(mval) if type else mval


def get_jspath_iter(d, jspth, *, type=None):
    expr = _parse_jspath(jspth)
    yield from map(attrgetter('value'), expr.find(d))


def md5sum(fn, chunk_size=8192):
    '''
    Calculate the MD5 checksum of a file

    Parameters
    ----------
    fn : str or path-like
    chunk_size : int, optional
         the size of the chunks to read (in bytes)

    Returns
    -------
      md5 digest: str
    '''

    cks = hashlib.md5()
    with open(fn, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            cks.update(chunk)
    return cks.hexdigest()




