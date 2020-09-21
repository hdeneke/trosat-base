# -*- coding: utf-8 -*-
#
# sunpos.py is free software; you can redistribute it and/or modify
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
# Authors/Copyright(2012-2020):
# -Hartwig Deneke (deneke@tropos.de)
# -Jonas Witthuhn (witthuhn@tropos.de)

'''
sunpos.py contains functions for calculation of the sun position, based on an 
algorithm from the Astronomical Alamanac. This algorithm was compared in 
Michalsky (1988a,1988b) with other approximate formulae and was found to be 
the most accurate. It is therefore recommended by the WMO Guide to 
Meteorological Instruments and Methods of Observations for practical 
application.

References
----------
.. [1] United States Naval Observatory, 1993: The Astronomical Almanac, 
       Nautical Almanac Office, Washington DC.
.. [2] Michalsky, J.J., 1988a: The astronomical almanac’s algorithm for 
       approximate solar position (1950–2050).
.. [3] Michalsky, J.J., 1988b: Errata. The astronomical almanac’s algorithm 
       for approximate solar position (1950–2050).
.. [4] World Meteorological Organization, 2014: Guide to Meteorological 
       Instruments and Methods of Observation. Geneva, Switzerland, World 
       Meteorological Organization, 1128p. (WMO-No.8, 2014).
'''

from enum import IntEnum
import datetime
import numpy as np
from numpy import sin, cos, arctan2, arcsin, arccos, deg2rad, rad2deg, pi

# contant definitions
EPOCH_JD2000_0 = np.datetime64('2000-01-01T12:00')
ONE_DAY        = np.timedelta64(1,'D')

# define units enum
class units(IntEnum):
    DEGREES = DEG = D = 1
    RADIANS = RAD = R = 2
    HOURS   = HR  = H = 3

# add units to package namespace, based on example from the 
# Python re package
globals().update(units.__members__)

# Function definitions
def sincos(x):
    '''
    Evaluate sin/cos simultaneously
    '''
    return sin(x),cos(x)


def to_units(x, from_units, to_units):
    '''
    Convert between hours, degrees and radians

    Parameters
    ----------
    x : float or ndarray of float
       The value to convert

    Returns
    -------
    x : float or ndarray of float
        x, given in the specified units
    '''

    mapfun = {
        (DEG,RAD) : np.deg2rad,          (DEG,HR)  : lambda x: x/15.0,
        (RAD,DEG) : np.rad2deg,          (RAD,HR)  : lambda x: x*12/np.pi,
        (HR,DEG)  : lambda x: x*15.0,    (HR,RAD)  : lambda x: x/12*np.pi
    }
    try: 
        from_units = from_units if not isinstance(from_units,str) else units.__members__[from_units.upper()]
        to_units = to_units if not isinstance(to_units,str) else units.__members__[to_units.upper()]
    except KeyError:
        raise TypeError("Invalid type for units argument")
    return x if from_units==to_units else mapfun[(from_units, to_units)](x)


def to_julday(time, epoch=EPOCH_JD2000_0):
    '''
    Convert various representations of time to Julian date,
    including ndarrays, lists or scalars of datetime and datetime64

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        A representation of time. If float, interpreted as Julian date.
    epoch : np.datetime64, default JD2000.0
        The epoch to use for the calculation

    Returns
    -------
    time : float or ndarray of float
        The fractional number of days since the epoch
    '''

    # function-local imports
    from collections.abc import Sequence, Iterable

    # 1. handle scalar types
    if isinstance(time, (np.floating,float)):
        # already a float, return as is
        return time
    elif isinstance(time, datetime.datetime):
        # datetime.datetime
        return (time-epoch.item()).total_seconds()/86400.0
    elif isinstance(time, np.datetime64):
        # np.datetime64
        return (time-epoch)/ONE_DAY
    # 2. convert Iterables/Sequences to ndarray
    if isinstance(time, (Iterable,Sequence)):
        time = np.array(time)
    # 3. handle ndarrays of different dtypes of ndarray
    if isinstance(time, np.ndarray):
        k = time.dtype.kind
        if k in np.typecodes['Float']:
            return time
        elif k=='O':
            return (time.astype('M8')-epoch)/ONE_DAY
        elif k=='M':
            return (time-epoch)/ONE_DAY
    raise TypeError('Type of time argument not supported')


def ecliptic_longitude(time, units=DEG):
    '''
    Calculate the ecliptic longitude

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.
    units : units, int or str
        Units of the return value

    Returns
    -------
    l : float or ndarray of float
        The ecliptic longitude
    '''

    jd = to_julday(time)
    L = 280.460 + 0.9856474*jd
    g = np.deg2rad(357.528 + 0.9856003*jd)
    l = L + 1.915*sin(g)+0.020*sin(2.0*g)
    l = np.remainder(l, 360.0)
    return to_units(l, DEG, units) if units!=DEG else l


def obliquity_of_ecliptic(time, units=DEG):
    '''
    Calculate the obliquity of the ecliptic

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.
    units : units, int or str
        Units of the return value

    Returns
    -------
    ep : float or ndarray of float
        The obliquity of the ecliptic
    '''

    jd = to_julday(time)
    ep = 23.439 - 0.0000004*jd
    return to_units(ep, DEG, units) if units!=DEG else ep


def right_ascension(time=None, l=None, ep=None, units=RAD):
    '''
    Calculate the right ascension of the sun

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64, or None
        Representation of time. If float, interpreted as Julian date.
    l : None, or float or ndarray of float
       The ecliptic longitude, in degrees. If None, it is calculated from time
    ep : None, or float or ndarray of float
       The obliquity of the ecliptic, in degrees. If None, it is calculated from time
    units : units, int or str, default DEGREES
        Units of the return value

    Returns
    -------
    ra : float or ndarray of float
        The right ascension
    '''
    
    if time is not None:
        # calc. if time is given as argument
        jd = to_julday(time)
        l = ecliptic_longitude(jd, units=RAD)
        cos_ep = cos(obliquity_of_ecliptic(jd, units=RAD))
    else:
        if l is None or ep is None:
            raise ValueError('time is None, so l and ep needed as arguments')
        l = deg2rad(l)
        cos_ep = cos(np.deg2rad(ep))
    # ensure ecliptic longitude lies within [-np.pi,np.pi]
    l = np.remainder(l+pi, 2.0*pi)-pi
    # use arctan2 for determining RA over [-pi,pi] range, instead of 
    # manually assigning quadrants as done in sunae.f
    ra = arctan2(cos_ep*sin(l),cos(l))
    return ra if units==RAD else to_units(ra, RAD, units)


def declination(time=None, l=None, ep=None, units=RAD):
    '''
    Calculate the declination of the sun

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.
    l : None, or float or ndarray of float
       The ecliptic longitude, in degrees. If None, it is calculated from time
    ep : None, or float or ndarray of float
       The obliquity of the ecliptic, in degrees. If None, it is calculated from time
    units : units, int or str
        Units of the return value

    Returns
    -------
    l : float or ndarray of float
        The ecliptic longitude
    '''

    if time is not None:
        # calc. jd, l and ep if time is given as argument
        jd = to_julday(time)
        l = ecliptic_longitude(jd, units=RAD)
        sin_ep = sin(obliquity_of_ecliptic(jd, units=RAD))
    else:
        if l is None or ep is None:
            raise ValueError('time is None, so l and ep needed as arguments')
        l = deg2rad(l)
        sin_ep = sin(deg2rad(ep))
    dec = arcsin(sin_ep*sin(l))
    return dec if units==RAD else to_units(dec, RAD, units)

def celestial_coordinates(time=None, units=RAD):
    '''
    Calculate the celestial coordinates of the sun (declination and right ascension)

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.
    units : units, int or str
        Units of the return values

    Returns
    -------
    dec, ra : tuple of float or ndarrays of float
        The declination and right ascension
    '''
    
    jd = to_julday(time)
    l = ecliptic_longitude(jd, units=RAD)
    sin_ep,cos_ep = sincos(obliquity_of_ecliptic(jd, units=RAD))
    l = np.remainder(l+pi, 2.0*pi)-pi
    dec = arcsin(sin_ep*sin(l))
    ra = arctan2(cos_ep*sin(l),cos(l))
    return (dec,ra) if units==RAD else (to_units(dec, RAD, units),to_units(ra, RAD, units))


def mean_sidereal_time(time=None, lon=None, units=HR):
    '''
    Calculate either Greenwich or local sidereal time

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.
    lon : float or array of float, default None
        The longitude in degrees, for calculation of LMST. If None, GMST is returned
    units : units, int or str
        Units of the return value

    Returns
    -------
    gmst or lmst: float or ndarray of float
        Greenwich or local sidereal time
    '''

    # get Julian date
    jd = to_julday(time)
    # get fractional hour
    # calc. based on CIMO Guide 2014, Ch.7, p.267
    hh = np.remainder(jd-0.5,1.0)*24.0
    gmst = 6.697375 + 0.0657098242*jd + hh
    # calcualate local sidereal time if lon is given
    mst = gmst+lon/15.0 if lon else gmst
    # limit to [0-24[ range
    mst = np.remainder(mst,24.0)
    # return desired units
    return mst if units==HR else to_units(mst, HR, units)

def equation_of_time(time, units=HR):
    gmst = mean_sidereal_time(time, units=HR)
    ra = right_ascension(time, units=HR)
    eot = gmst-ra
    eot = np.remainder(eot+12.0,24.0)-12.0
    return eot if units==HR else to_units(eot, HR, units)

def apparent_time(time, lon=None, units=HR):
    '''
    Calculate either Greenwich or local apparent time

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.
    lon : float or array of float, default None
        The longitude in degrees, for calculation of LMST. If None, GMST is returned
    units : units, int or str
        Units of the return value

    Returns
    -------
    gat or lat: float or ndarray of float
        Greenwich or local apparent time
    '''
    eot = equation_of_time(time, units=HR)
    return None


def hour_angle(time=None, lon=None, mst=None, ra=None, units=HR):
    '''
    Calculate the Greenwich or local hour angle

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.
    lon : float or array of float, default None
        The longitude in degrees, for calculation of the local hour angle. If None, 
        the Greenwich hour angle is returned
    mst : None, or float or ndarray of float
        The mean sideral time. If None, it is calculated internally.
    ra : None, or float or ndarray of float
        The right ascension. If None, it is calculated internally.
    units : units, int or str
        Units of the return value

    Returns
    -------
    ha: float or ndarray of float
        The Greenwich or local hour angle
    '''

    if time is not None:
        mst = mean_sidereal_time(time, lon, units=HR)
        ra = right_ascension(time, units=HR)
    else:
        ra = to_units(ra, RAD, HR)
    # ensure that ha lies in range [-12,12]
    ha = np.remainder((mst-ra)+12.0, 24.0)-12.0
    # Return ha with chosen units
    return ha if units==HR else to_units(ha, HR, DEG)


def sun_angles(time, lat, lon, units=DEG):
    '''
    Calculate the sun angles

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.
    lat : float or array of float, default None
        The latitude in degrees for the calculation
    lon : float or array of float, default None
        The latitude in degrees for the calculation
    units : units, int or str
        Units of the return value

    Returns
    -------
    szen,sazi: tuple of floats or ndarrays of float
        The solar zenith and azimuth angle
    '''
  
    # Calculate Greenwich mean sidereal time
    gmst = mean_sidereal_time(time, units=RAD)

    # Calculate declination/right ascension
    dec,ra = celestial_coordinates(time, units=RAD)

    # Calc. sin/cos of lat/lon/dec
    sin_lat, cos_lat = sincos(deg2rad(lat))
    sin_lon, cos_lon = sincos(deg2rad(lon))
    sin_dec, cos_dec = sincos(dec)

    # Calc. Greenwich hour angle
    gha = gmst-ra

    # Calc. sin/cos of local hour angle
    # NB: split time/space dims in evaluation of trig. functions, to 
    # enable efficient broadcasting
    (sin_gha,cos_gha) = sincos(gha)
    sin_ha = sin_gha*cos_lon + cos_gha*sin_lon
    cos_ha = cos_gha*cos_lon - sin_gha*sin_lon

    # Calculate cosine of solar zenith angle
    mu0 = sin_dec*sin_lat + cos_dec*cos_lat*cos_ha
    zen = arccos(mu0)

    # Calculate solar azimuth angle
    sin_azi = -cos_dec*sin_ha                  # skip divide by cos_el 
    cos_azi = (sin_dec-mu0*sin_lat)/cos_lat
    azi = arctan2(sin_azi,cos_azi)

    # constrain azi range to  [0-2*pi]
    azi = np.remainder(azi,2.0*pi)
    # return values in requested units
    return (zen,azi) if units==RAD else (to_units(zen,RAD,units),to_units(azi,RAD,units))


def earth_sun_distance(time):
    '''
    Calculate the earth sun distance

    Parameters
    ----------
    time : list, ndarray, or scalar of type float, datetime or datetime64 
        Representation of time. If float, interpreted as Julian date.

    Returns
    -------
    esd: float or ndarray of float
        The earth-sun distance, in Astronomical units
    '''
    jd = to_julday(time)
    g = np.deg2rad(357.528 + 0.9856003*jd)
    return 1.00014-0.01671*cos(g)+0.00014*cos(2.0*g)



