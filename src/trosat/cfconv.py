import numpy as np
import pandas as pd

import netCDF4 as nc

from addict import Dict as aDict
from . import numpy_ext as npx

lat_units = "degree_north"
lon_units = "degree_east"

# Try to load jstylson, falling back to json
try:
    import jstyleson as json
except:
    import json


def val2type(val, ts):
    '''
    Convert scalar value to numpy type based on ts

    Parameters
    ----------
    val : numeric
        The value
    ts : string
        A string denoting type
    '''
    return np.dtype(ts).type(val)


class CfDict(aDict):
    '''
    Class for storing CF-data in dictionary,
    based on AttrMap
    (just adding a few convenience functions)
    '''
    def setDim(self, name, n):
        self.dimensions[name] = n
        return

    def setCoord(self, name, x):
        self.dimensions[name] = x.shape[0]
        self.variables[name].data = x
        return

    def setData(self, name, x):
        self.variables[name].data = x
        return

def read_cfjson(fname):
    '''
    Read a CF-JSON like JSON file, see https://cf-json.org for info. 
    
    Parameters
    ----------
    fname : str
        The filename to read
    
    Returns
    -------
    cfdict : dict-like
        The CF conventions metadata, stored in a dictionary
    '''
    with open(fname,'r') as f:   
        cf = json.load(f, object_pairs_hook=CfDict)
        for vnam in cf.variables.keys():
            v = cf.variables[vnam]
            if 'type' in v:
                if '_FillValue' in v.attributes:
                    val = val2type(v.attributes['_FillValue'], v.type)
                    v.attributes['_FillValue'] = val
                if 'flag_masks' in v.attributes:
                    mlist = [val2type(m,v.type) for m in v.attributes['flag_masks']]
                    v.attributes['flag_masks'] = mlist
    return cf


class File(nc.Dataset):

    def __init__(self, *args, **kwargs):
        '''
        Constructor for netcdf File
        '''
        # pop encoding argument from kwargs
        enc = kwargs.pop('encoding', None)
        # call nc.Dataset constructor
        super().__init__(*args, **kwargs)
        # set default encoding for variables if specified
        if enc:
            self.__dict__['encoding'] = enc
        return


    def __del__(self):
        '''
        Fix inheritance issue, see:
        https://github.com/Unidata/netcdf4-python/issues/788
        '''
        if self.isopen():
            self.close()
        return

    def createDims(self, dims):
        '''
        create dimensions

        Parameters
        ----------
        dims : dict
            A dict containing dimension names/size as key/value pairs
        '''
        for d,n in dims.items():
            self.createDimension(d,n)
        return

    def setGlobalAtts(self, attdict):
        '''
        Set global attributes

        Parameters
        ----------
        attdict : dict
            A dict containing attributes as key/value pairs
        '''
        self.setncatts(attdict)
        return

    def createVars(self, vars_):
        '''
        Create variable described by vars dictionary
        '''
        for vnam,var in vars_.items():
            atts = var.attributes
            _fvalue = atts.pop('_FillValue', None)
            # get properties for variable creation
            if hasattr(self, 'encoding'):
                kwargs = dict(self.encoding)
            else:
                kwargs = {}
            if hasattr(var, 'encoding'):
                kwargs.update(var.encoding)
            # create variable
            self.createVariable(vnam, var.type, var.shape, fill_value=_fvalue, **kwargs)
            # add attributes to variable
            self[vnam].setncatts(atts)
            # set data if specified
            if 'data' in var:
                self[vnam][:] = var.data
        return


def create_file( fname, cfdict=None, dims=None, atts=None, vars_=None, **kwargs):
        '''
        Create a CF-compliant netcdf file, either based on CF-JSON dictionary, or
        dicts for specifying dimensions, global attributes and variables.

        Parameters
        ----------
        fname : str
            The filename
        cfdict : dict or None
            A dict following CF-JSON conventions.
        dims : dict or None
            A dict containing dimension names/size as key/value pairs. Used if cfdict is None.
        atts : dict or None
            A dict containing global attributes as key/value pairs. Used if cfdict is None.
        vars_ : dict or None
            A dict describing variables to create. Used if cfdict is None.
        kwargs : dict
            A dict with keyword arguments to be passed into cf.File.__init__

        Returns
        -------
        file : cfconv.File, a subclass of NetCDF4.Dataset
             The created NetCDF file object
        '''

        # create file
        if cfdict:
            if 'encoding' in cfdict:
                kwargs['encoding'] = cfdict.encoding
        f = File(fname, "w", **kwargs)
        # set global attributes
        atts = cfdict.attributes if cfdict else atts
        if atts: f.setGlobalAtts(atts)
        # create dims
        dims = cfdict.dimensions if cfdict else dims
        if dims: f.createDims(dims)
        # create variables
        vars_ = cfdict.variables if cfdict else vars_
        if vars_: f.createVars(vars_)
        return f

def get_coverage(ds, *, timevar="time", skipna=True):
    '''
    get ACCD coverage attributes for xr.Dataset
    
    Parameters
    ----------
    ds : xr.Dataset
        the dataset to use as basis
    timevar : str, default="time"
        the name of the time variable, or None, if time coverage should be skipped
    return_json : bool, optional
        return results as a json string
    kwargs
        further keyword arguments passed to json.dumps
    
    Returns
    -------
    coverage : dict
        dict with ACDD coverage attributes
    '''

    # calc. geospatial coverage
    lat_min, lat_max = npx.minmax(ds["lat"], skipna=skipna)
    lon_min, lon_max = npx.minmax(ds["lon"], skipna=skipna)
    cov = {
        "geospatial_lat_min": lat_min,
        "geospatial_lat_max": lat_max,
        "geospatial_lat_units": lat_units,
        "geospatial_lon_min": lon_min,
        "geospatial_lon_max": lon_max,
        "geospatial_lon_units": lon_units,
    }
    
    #
    if timevar is not None:
        tarr = ds[timevar]
        tstart = pd.to_datetime(tarr.values.min())
        tend   = pd.to_datetime(tarr.values.max())
        tres   = pd.to_timedelta(np.diff(tarr.values).mean())
        cov.update({
            "time_coverage_start": tstart.isoformat(),
            "time_coverage_end": tend.isoformat(),
            "time_coverage_duration": (tend-tstart).isoformat(),
            "time_coverage_resolution": tres.isoformat()
        })
    return cov    



    

    
