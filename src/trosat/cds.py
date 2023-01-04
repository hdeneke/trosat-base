import os
import sys
import json

import requests
from requests.compat import urljoin

class session(requests.Session):
    '''
    https://github.com/psf/requests/issues/2554#issuecomment-109341010
    '''
 
    def __init__(self, url, *, key=None):
        # set base url as attribute
        self.base_url = url
        # call parent __init__
        super().__init__()
        # add authentication keys
        if key:
            self.auth = tuple(key.split(":",2))
        return

    def request(self, method, ep, *args, **kwargs):
        '''
        
        '''
        url = urljoin(self.base_url, ep)
        resp = super().request(method, url, *args, **kwargs)
        resp.raise_for_status()
        return resp

    def list_requests(self):
        ''' 
        Get a list of CDS requests.

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
        resp = self.delete(f'tasks/{rid}')
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



    
