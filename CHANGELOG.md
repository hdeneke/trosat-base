# Changelog

## Git Head (to become Version 0.9.6)
* trosat.coord: new module for geographic coordinate calculations
* trosat.cds: misc. updates and improvements

## Version 0.9.5
* use versioneer for managing version numbers
* change version scheme, tag version in git
* add strip-json tool to strip comments from non-standard JSON files
* trosat.cds: experimental code for accessing Copernicus data store

## Version 0.9.b4
* strip notebook output from git repo
* trosat.cfconv: switch from attrdict to addict module
* trosat.cfconv: correctly fix close issue

## Version 0.9.b3
* trosat.cfconv: fix close issue caused by inheritance
* trosat.numpy.ext.bitops:  bugfix

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
