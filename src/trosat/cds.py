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

from collections.abc import Mapping, Sequence
from requests.compat import urljoin
from functools import reduce
from toolz import dicttoolz
from operator import itemgetter, getitem


def get_nested(d, keys, *, sep="."):
    '''
    get item from nested dictionary
    
    Parameters
    ----------
    keys : tuple of str or str
       the sequence of keys to get
    sep : str
       split keys usi
    
    Returns
    -------
    retval : j
        returns the value of the nested dict
    '''
    keys = keys.split(sep) if isinstance(keys, str) else keys
    return reduce(lambda d,k: d.get(k, None) if d else None, keys, d)


def req2uuid(req):
    '''
    Generate a uuid from a request

    Code based on:
    https://gist.github.com/azylinski/b61116f74c609cf3b7a4b28d7da65c96
    
    Parameters
    ----------
    req : Mapping
       the request
    
    Returns
    -------
    uuid : str
       a string corresponding to a UUID for the object
    '''
    from uuid import NAMESPACE_DNS, uuid3
    # convert req to JSON
    jreq= json.dumps(req, sort_keys=True)
    # return uuid3 string
    return str(uuid3(NAMESPACE_DNS, jreq))


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


class session(requests.Session):
    '''
    Session class for sending HTTP requests to the Copernicus Data
    Store (CDS) API endpoints.
    
    Parameters
    ----------
    url : str
       The URL of the API endpoint
    key : str, default=None
       Authentication key

    Attributes
    ----------
    ep_url : str
       The URL of the API endpoint
    auth : tuple
        Authentication tokens

    Note
    ----
    This class inherits from request.Session and sends all requests to 
    an URL relative to the session.ep_url, inspired by:
    https://github.com/psf/requests/issues/2554#issuecomment-109341010
    '''


    def __init__(self, url, *, key=None):
        '''
        Parameters
        ----------
        url : str
            The base URL of the Copernicus Datastore 
        '''
        # set base url as attribute
        self.ep_url = url
        # call parent __init__
        super().__init__()
        # add authentication keys
        if key:
            self.auth = tuple(key.split(":",2))
        return


    def request(self, method, ep, *args, raise_for_status=True, **kwargs):
        '''
        Builds, prepares and sends HTTP requests

        Arguments
        ---------
        method : {"get", "post","put","delete"}
            HTTP method
        ep : str
            the API endpoint, relative to ep_url
        args: list
            positional arguments for calling parent class
        kwargs: Mapping
            keyword arguments for calling parent class

        Returns
        -------
        resp : requests.Response
            the response to the HTTP request
        '''

        url = urljoin(self.ep_url, ep)
        resp = super().request(method, url, *args, **kwargs)
        if raise_for_status:
            resp.raise_for_status()
        return resp


    def list_requests(self, *, state=None, as_dict=False, http_resp=False):
        ''' 
        Get list of submitted CDS requests
        
        Parameters
        ----------
        state : None or str
            if set, only return requests with this state
        as_dict : bool
            return results as dict with request ID as keys
        http_resp : bool
            return http response of request as first tuple member 
        
        Returns
        -------
            list or dict of requests, or tuple with HTTP response
        '''
        
        # get task list
        resp = self.get('tasks')

        # parse json-formatted request list
        retval = json.loads(resp.text)

        # filter by state if state argument is given
        if state:
            retval = [r for r in retval if r["state"]==state]

        # return as dictionary if as_dict is True
        if as_dict:
            f = itemgetter("request_id")
            retval = {f(r):r for r in retval}
        
        # return HTTP response in tuple if http_resp is True
        if http_resp:
            retval = (resp, retval)

        return retval


    def delete_request(self, rid):
        '''
        Delete a request.

        Parameters
        ----------
        rid : str
            The request ID.

        Raises
        ------
        TBD
        '''
        resp = self.delete( f'tasks/{rid}' )
        return


    def submit_request(self, req, resource=None, /, *, userid=False,
                       return_uuid=False, json_encode=True):
        '''
        Submit a request

        Parameters
        ----------
        req  : str or dict
            the request
        resource : str
            the resource/dataset name
        userid : bool, default=False
            specify userid on submission if set
        return_uuid : bool, default=False
            return uuid of request
        json_encode : bool, default=True
            boolean flag for encod

        Raises
        ------
        TBD
        '''
        
        req  = json.dumps(req) if json_encode else req
        #if userid:
        if resource is None:
            # infer resource name 
            if not json_encode:
                raise ValueError("submit: resource not given and json str")
            resource = req["dataset"].split(":")[-1]
        resp = self.post(f'resources/{resouce}', req)
        return resp if return_uuid else None


    def request_info(self, rid):
        '''
        Get request info.

        Parameters
        ----------
        rid : str
            The request ID.

        Returns
        -------
        info : dict
            The decoded json response of the "tasks/{rid}" endpoint.
        '''
        resp = self.get( f'tasks/{rid}' )
        return json.loads(resp.text)


    def request_provenance(self, rid):
        '''
        Get request provenance.

        Parameters
        ----------
        rid : str
            The request ID.

        Returns
        -------
        info : dict
            The decoded json response of the "tasks/{id}/provenance" endpoint.
        '''
        resp = self.get(f'tasks/{rid}/provenance')
        return json.loads(resp.text)


    def download_request(self, rid, ofile=None, *, chunk_size=8192):
        '''
        Download a completed request from the CDS.

        Parameters
        ----------
        rid : str
            The request ID.
        ofile: str, pathlike or filelike, default=None
            The target file to save the request to.

        Returns
        -------
        None
        '''
        
        # get request info
        param = self.request_info(rid)

        # get download URL and content length
        dl_url = param["location"]

        # open destination file for writing
        if ofile is None:
            ofile = get_nested(
                self.request_provenance(rid), 
                "original_request.specific_json.target",
            )
            if ofile is None: raise ValueError("neither ofile set nor target in request")

        # open file obj for writing
        fobj = ofile if hasattr(ofile, "write") else open(ofile, "wb")

        #  download URL 
        self.download_url(dl_url, fobj, chunk_size=chunk_size)

        # cleanup
        if hasattr(fobj, "close"):
            fobj.close()
        return


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
