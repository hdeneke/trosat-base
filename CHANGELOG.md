# Changelog of trosat-base Python Package

## Version 0.9.b2
* Added example notebooks in ipynb directory for sunpos, cfconv sub-packages
* cfconv: added support for "encode" object in CF-JSON e.g. for compression
* cfconv: use custom class CfDict for storing CF-JSON.
* pathutil: small fixes to PathMatcher/PathMatch
* numpy_ext: new addition for basic numerical functions, added bitops

## Version 0.9.b1
Initial release, including the following features/subpackages:
* trosat.sunpos: Functions for calculation of the sun position
* trosat.cfconv: Functions for creating CF-compliant netCDF files from CF-JSON
* trosat.pathutil: Functions for formatting and matching paths
