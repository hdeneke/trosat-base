'''
Python module to access the Copernicus Data Store (CDS) services.

This module provides code for accessing information and data offered
by the European Copernicus programme through the Copernicus Atmosphere
Monitoring (CAMS) and Copernicus Climate Change Service (C3S) services.

These services are refered to in the following as: 
* The Atmosphere Data Store (ADS)
* The Climate Data Store (CDS)

Access is implemented via the public API endpoints. The primary
sources of information used for writing this module are the public API
docs for the API endpoints (EPs)

References:
* https://ads.atmosphere.copernicus.eu/#!/home
* https://cds.climate.copernicus.eu/#!/home
* https://ads.atmosphere.copernicus.eu/modules/custom/cds_apikeys/app/apidocs.html
* https://cds.climate.copernicus.eu/modules/custom/cds_apikeys/app/apidocs.html
'''

import jstyleson as json
import os
import requests
import string
import sys

from collections import deque
from collections.abc import Callable, Iterator, Mapping, Sequence
from operator import itemgetter, getitem

from requests.compat import urljoin, urlparse
from urllib.parse import parse_qsl
from toolz import dicttoolz
from .util import get_jspath_node


def request_has_children(req):
    ''' Test if request is a parent request '''
    return "request_children" in req


def read_requests(fn, *, expand_user=True, expand_vars=True, \
                  expand_children=True, obj_hook=dict        ):
    '''
    Read CDS request(s) from JSON-formatted file
    
    Parameters
    ----------
    fpath : str or PathLike
        the file path to the JSON file
    expand_user : bool, default=True
        perform tilde/user home directory expansion on
        target key by invoking os.path.expanduser
    expand_vars : bool, default=True
        perform environment variable expansion on target
        key by invoking os.path.expanduser
    expand_children : bool, default=False
        expand child requests
    obj_hook : Mapping, default=dict
        class/constructor for mapping type

    Returns
    -------
    reqs : list 
        list of requests
    '''

    def _read_json(fpath, *, obj_hook=dict):
        with open(fpath,"r") as f:
            js = json.load(f, object_hook=obj_hook)
            return js
    
    def _expand_path(p, user=True, vars=True):
        p = os.path.expanduser(p) if user else p
        p = os.path.expandvars(p) if vars else p
        return p

    # read JSON file
    reqs = _read_json(fn, obj_hook=obj_hook)

    # support both single request and list of requests
    # => convert reqs to list if necessary
    if isinstance(reqs, Mapping):
        reqs = [reqs]
    elif isinstance(reqs, Sequence):
        pass
    else:
        raise ValueError("read neither a Sequence nor a Mapping")

    # expand path
    if expand_user or expand_vars:
        for r in reqs:
            if "target" in r:
                r["target"] = _expand_path(
                    r["target"],
                    user=expand_user,
                    vars=expand_vars
                )

    # expand children requests
    if expand_children:
        _reqs = []
        for r in reqs:
            if request_has_children(r):
                children = r.pop("request_children")
                _reqs.extend([{**r, **ch} for ch in children])
            else:
                _reqs.append(r)
            reqs = _reqs

    # finally return
    return reqs

### misc. private objects/functions

# string.Formatter object
_fmtr = string.Formatter()

# test function if s is a string
_is_str = lambda s:  isinstance(s, str)

def _fmt_filter(s):
    ''' test if s is a format string with named fields '''
    if _is_str(s):
        return _is_str(tuple(_fmtr.parse(s))[0][1])
    else:
        return False


def _fmt_request(r, farg, fmt_keys):
    ''' for requests, map values to str.format output for keys in fmt_keys  '''
    _fmt_map = lambda i: (i[0],i[1].format(req=r, **farg)) if i[0] in fmt_keys else i
    return dicttoolz.itemmap(_fmt_map, r)


def expand_requests(base_reqs, farg_iter, *, fmt_keys=None):
    '''
    Expand list of CDS request templates by substitution of request values
    with format strings by str.format output, iterating over format arguments
    
    Parameters
    ----------
    base_reqs : sequence of mapping
        a sequence of request templates
    farg_iter : sequence of mapping
        a sequence of named key-word arguments for str.format
    fmt_keys : set of str, default=None
        the request keys who's values contain format strings
        
    Returns
    -------
    req_gen : iterator of mapping
        an iterator of requests
    '''
    for farg in farg_iter:
        for i,req in enumerate(base_reqs):
            _keys = fmt_keys or set(dicttoolz.valfilter(_fmt_filter, req).keys())
            yield _fmt_request(req.copy(), farg, _keys)


class ApiSession(requests.Session):
    '''
    Session class for sending HTTP requests to a Copernicus Data Store (CDS)
    API endpoint.
    
    Parameters
    ----------
    url : str
       The URL of the API endpoint
    key : str, default=None
       Authentication key

    Attributes
    ----------
    url : str
       The URL of the API endpoint
    auth : tuple
        Authentication tokens

    Note
    ----
    This class inherits from request.Session and sends all requests to 
    an URL relative to session.base_url, which is particularly useful
    for talking to a WebAPI.

    Code inspired by:
    https://github.com/psf/requests/issues/2554#issuecomment-109341010
    '''


    def __init__(self, base_url, *, headers=None, key=None):
        '''
        Parameters
        ----------
        url : str
            The base URL of the Copernicus Datastore 
        '''
        # set base url as attribute
        self.base_url = base_url
        # call parent __init__
        super().__init__()
        # add authentication keys
        if key:
            self.auth = tuple(key.split(":",2))
        if headers:
            self.headers.update(headers)
        return


    def request(self, method, ep_url, *args, raise_for_status=True, **kwargs):
        '''
        Builds, prepares and sends the HTTP requests

        Arguments
        ---------
        method : {"get", "post","put","delete"}
            HTTP method
        ep_url : str
            the URL of the service endpoint, relative to self.base_url
        args: list
            positional arguments for calling the parent class
        raise_for_status: bool, default=True
            raise 
        kwargs: Mapping
            keyword arguments for calling the parent class

        Returns
        -------
        resp : requests.Response
            the response of the HTTP request
        '''

        url = urljoin(self.base_url, ep_url)
        resp = super().request(method, url, *args, **kwargs)
        if raise_for_status: resp.raise_for_status()
        return resp


class EpDict(Mapping):
    '''
    Dict-like object representing a REST API endpoint
    '''
    def __init__(self, api, endpoint):
        self.api = api
        self.session = api.session
        self.endpoint = endpoint
        return

    def __getitem__(self, key):
        try:
            return self.session.get(
                self.endpoint.format(key=key)
            ).json()
        except HTTPError as e:
            raise KeyError(f"no job id {key}" ) from e

    def __len__(self):
        return self.api.__len__()

    def __iter__(self):
        return self.api.__iter__()


class _JobsIter(Iterator):

    def __init__(self, session, limit=10, **kwargs):
        self.session = session
        self._jobs = deque()
        self._qdict = {**kwargs, "limit":limit}
        self._next  = True
        return

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self._jobs.popleft()
        except IndexError:
            # should we try to get more jobs from endpoint?
            if self._next:
                # get next jobs page
                jj = self.session.get('jobs', params=self._qdict).json()
                # get URL/query dict for next page
                href_next = get_jspath_node(jj, '$.links[?rel=="next"].href')
                if href_next:
                    self._qdict = self.get_query_dict(href_next)
                else:
                    self._next = False
                jlist = jj["jobs"]
                if len(jj["jobs"])>0:
                    self._jobs.extend(jj["jobs"])
                    return self._jobs.popleft()
            raise StopIteration

    @staticmethod
    def get_query_dict(url):
        qstr = urlparse(url).query
        return dict(parse_qsl(qstr)) if qstr else None

class JobsApi(Mapping):

    def __init__(self, session):
        self.session = session
        self.status  = EpDict(self, 'jobs/{key}')
        self.results = EpDict(self, 'jobs/{key}/results')
        self.receipt = EpDict(self, 'jobs/{key}/receipt')
        return

    def __len__(self):
        jj = self.session.get('jobs', params={"limit":1}).json()
        return get_jspath_node(jj, "$.metadata.totalCount", type=int)

    def __getitem__(self, key):
        return self.status[key]

    def __delitem__(self, key):
        return self.delete(key)

    def __iter__(self):
        return (j["jobID"] for j in  _JobsIter(self.session, limit=10))

    def __call__(self, limit=10, **qparams):
        return _JobsIter(self.session, limit=limit, **qparams)
        
    def submit(self, req):
        '''
        submit a data request job

        Parameters
        ----------
        req : dict-like
            the request in dictionary format

        Returns
        -------
        response
        '''
        # get dataset
        dataset = req["dataset"]
        resp = self.session.post(
            f"processes/{dataset}/execution",
            json={
                "inputs": req
            }
        )
        return resp.json()

    def delete(self, key):
        '''
        delete a data request job

        Parameters
        ----------
        jid : int
            the ID of the data request job

        Returns
        -------
        response
        '''
        return self.session.delete(f'jobs/{key}').json()


def download_url(self, url, ostream, *, http_resp=False, chunk_size=8192):
    '''
    Download URL of completed request to a file object 
        
    Parameters
    ----------
    url : str
        the URL of the download
    ostream : file object
        the output file object for the download
    '''

    resp = super().get(url, stream=True)
    resp.raise_for_status()
    for chunk in resp.iter_content(chunk_size=chunk_size):
        ostream.write(chunk)
    return resp if http_resp else None
