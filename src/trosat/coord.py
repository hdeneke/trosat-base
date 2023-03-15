import numpy as np
import pyproj


_ecef     = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84') 
_lla      = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
_ecef2lla = pyproj.Transformer.from_proj(_ecef, _lla)
_lla2ecef = pyproj.Transformer.from_proj(_lla, _ecef)

def ecef2lla(x,y,z):
    '''
    Transform a 3D vector from ECEF to lon/lat/alt coordinates
    '''
    return _ecef2lla.transform(x,y,z)

def lla2ecef(lon,lat,alt):
    '''
    Transform a 3D vector from lon/lat/alt to ECEF coordinates
    '''
    return _lla2ecef.transform(lon,lat,alt)

def view2enu(zen,azi,dist=None):
    sin_zen = np.sin(np.deg2rad(zen))    
    e = sin_zen*np.sin(np.deg2rad(azi))
    n = sin_zen*np.cos(np.deg2rad(azi))
    u = np.cos(np.deg2rad(zen))
    if dist:
        e *= dist
        n *= dist
        u *= dist
    return e,n,u

def enu2view(e,n,u, unit=False):
    azi = np.rad2deg(np.arctan2(e,n))
    zen = np.rad2deg(np.arccos(u)) if unit else np.rad2deg(np.arccos(u/np.sqrt(e**2+n**2+u**2)))
    return zen, azi

def lat2re(lat):
    # WGS84 constants
    r_eq = 6378137.0
    f = 1.0/298.257223563
    r_pol = r_eq*(1.0-f)
    return r_eq*(1.0-f)/np.sqrt(1.0-(f*(2.0-f))*np.cos(np.deg2rad(lat)))

def rot_ecef2enu(lon, lat):
    '''
    Get rotation matrix for converting ECEF to ENU coordinates
    '''
    # get transformation matrix from ECEF to ENU coordinates
    # see https://en.wikipedia.org/wiki/Geographic_coordinate_conversion#From_ECEF_to_ENU
    sin_lam = np.sin(np.deg2rad(lon))
    cos_lam = np.cos(np.deg2rad(lon))
    sin_phi = np.sin(np.deg2rad(lat))
    cos_phi = np.cos(np.deg2rad(lat))
    
    _scalar = np.isscalar(lon) and np.isscalar(lat)
    assert(np.isscalar(lon)==np.isscalar(lat))
    zero = 0.0 if _scalar else np.zeros_like(lat)
    R = np.stack([
        [ -sin_lam,          cos_lam,         zero    ],
        [ -sin_phi*cos_lam, -sin_phi*sin_lam, cos_phi ],
        [  cos_phi*cos_lam,  cos_phi*sin_lam, sin_phi ]
    ])
    
    # if lon/lat are multi-dimensional arrays, we have now added 2 new
    # dimensions left of the original dimensions. Move these two dimensions
    # to the right, so ndarray.dot, matrix multiply and @ operator work
    if not _scalar:
        R = np.transpose(R, np.roll(np.arange(len(R.shape)), -2) )
    return R

def rot_enu2ecef(lon, lat):
    '''
    Get rotation matrix for converting ENU to ECEF coordinates
    '''
    # inverse/transpose of ecef2enu rotation matrix, thus
    # use that instead of re-writing everything... 
    R = rot_ecef2enu(lon,lat)
    return np.swapaxes(R,-2,-1)
