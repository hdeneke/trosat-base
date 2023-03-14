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

import os
import sys
import json

import requests
from requests.compat import urljoin

class session(requests.Session):

'''
    Session class for sending HTTP requests to the Copernicus Data
    Store (CDS) API endpoints.
    
    Parameters
    ----------
    url : str
       The base URL of the API endpoint
    key : str, default=None
       Authentication key

    Attributes
    ----------
    base_url : str
       The base URL of the API endpoint
    auth : tuple
        Authentication tokens

    Note
    ----
    This class inherits from request.Session and sends all requests to 
    an URL relative to the session.base_url, inspired by:
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
        self.base_url = url
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
            the API endpoint, relative to base_url
        args: list
            positional arguments for calling parent class
        kwargs: Mapping
            keyword arguments for calling parent class

        Returns
        -------
        resp : requests.Response
            the response to the HTTP request
        '''

        url = urljoin(self.base_url, ep)
        resp = super().request(method, url, *args, **kwargs)
        if raise_for_status:
            resp.raise_for_status()
        return resp


    def list_requests(self):
        ''' 
        Get a list of CDS requests

        Parameters
        ----------
        as_dict : Bool
            Return results as dict, with request IDs as keys
        
        Returns
        -------
           A list or dict of user's requests
        '''
        resp = self.get('tasks')
        return json.loads(resp.text)


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


    def submit_request(self, name, req, json_encode=True):
        '''
        Submit a request

        Parameters
        ----------
        name : str
            the dataset name
        req  : str or dict
            the request
        json_encode : bool, default=True
            boolean flag for encod

        Raises
        ------
        TBD
        '''
        req = json.dumps(req) if json_encode else req
        resp = self.post(f'resources/{name}', req)
        return


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


    def request_details(self, rid):
        '''
        Get request details.

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
            req_details = self.request_details(rid)
            req_json = req_details["original_request"]["specific_json"]
            ofile = req_json.get("target", None)
            if ofile is None: raise ValueError("neither ofile set nor target in request")

        f = ofile if hasattr(ofile, "write") else open(ofile, "wb")

        # get download using stream mode in chunks
        resp = super().get(dl_url, stream=True)
        resp.raise_for_status()
        
        for chunk in resp.iter_content(chunk_size=chunk_size):
            f.write( chunk )

        # cleanup
        if hasattr(f, "close"):
            f.close()
        return


    
