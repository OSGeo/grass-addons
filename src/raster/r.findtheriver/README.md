COPYRIGHT
---------
(C) 2013 by the University of North Carolina at Chapel Hill

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.


AUTHOR
------
Brian Miles - brian_miles@unc.edu


DESCRIPTION
-----------
r.findtheriver finds the nearest stream pixel to a coordinate pair
using an upstream accumulating area (UAA) raster map.  This is
necessary because the coordinates for streamflow gages are often not
perfectly registered to the topography represented by a digital
elevation model (DEM) map.  This presents a problem when trying to
derive a watershed contributing area using r.water.outlet; if the
streamflow gage does not fall on the stream as represented in the
DEM, r.water.outlet can fail to derive the watershed area.
 
The basic assumption is that the UAA for "stream" pixels will be much
higher than for adjacent "non-stream" pixels.
r.findtheriver attempts to "snap" the coordinates of the
streamflow gage to the "true" stream location by first identifying
stream pixels within a search window, and then selecting the stream
pixel that is closest (cartesian distance) to the input gage
coordinates.  Stream pixels are identified by searching the UAA
raster window for pixels that exceed a threshold.  This is done by
computing the log10 of the UAA value for the pixel corresponding to
the gage coordinates and subtracting from it the log10 of each pixel
in the window; for a given pixel if this difference is greater than
the threshold, the pixel is deemed to be a stream pixel.

r.findtheriver will automatically compute the window and threshold if
they are not supplied by the user.  The window is determined based on
a THRESHOLD_DISTANCE / cell resolution of the UAA map.  The threshold
is determined by subtracting the log10 of the UAA value at the input 
gage coordinate from the log10 of the maximum UAA value of the map, 
and then rounding down to the nearest integer, in other words:
threshold = floor( log(maxUAA) - log(gageUAA) ).

The closest stream pixel is printed to standard output.  If no stream
pixels were found nothing is printed.


BUILDING
--------
OS X

First read William Kyngesburye's "Building Addon Modules for Mac OS X
GRASS.app (see ReadMe-OSX.rtf).  To install, you will generally do:

make GRASS_HOME=./ GRASS_APP=/Applications/GRASS-6.4.app
sudo make GRASS_HOME=./ GRASS_APP=/Applications/GRASS-6.4.app deploy

Assuming you have unpacked r.findtheriver into your local copy of 
modbuild/module (see ReadMe-OSX.rtf) and the current directory is 
r.findtheriver.


Linux/Unix

First read: http://grasswiki.osgeo.org/wiki/Compile_and_Install#Addons

To install, you will generally do:

sudo make MODULE_TOPDIR=/usr/lib/grass64/ INST_DIR=/usr/lib/grass64/

Note: you will have to change /usr/lib/grass64 to the location of your GRASS headers.
