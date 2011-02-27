#!/usr/bin/env python

############################################################################
#
# MODULE:      r.hazard.flood.py
# AUTHOR(S):   Margherita Di Leo
# PURPOSE:     Fast procedure to detect flood prone areas on the basis of a 
#              topographic index
# COPYRIGHT:   (C) 2010 by Margherita Di Leo and the GRASS Development Team
#              dileomargherita@gmail.com
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%module
#%  description: Fast procedure to detect flood prone areas
#%  keywords: raster
#%end
#%option
#%  key: map
#%  type: string
#%  gisprompt: old, raster, cell
#%  key_desc: elevation
#%  description: Name of elevation raster map 
#%  required: yes
#%end
#%option
#%  key: flood
#%  type: string
#%  gisprompt: new, raster, cell
#%  key_desc: flood
#%  description: Name of output flood raster map 
#%  required: yes
#%end
#%option
#%  key: mti
#%  type: string
#%  gisprompt: new, raster, cell
#%  key_desc: MTI
#%  description: Name of output MTI raster map 
#%  required: yes
#%END

import grass.script as grass
import os, sys

if not os.environ.has_key("GISBASE"):
    print "You must be in GRASS GIS to run this program."
    sys.exit(1)

def main():
    r_elevation = options['map'].split('@')[0] 
    mapname = options['map'].replace("@"," ")
    mapname = mapname.split()
    mapname[0] = mapname[0].replace(".","_")
    r_flood_map = options['flood']
    r_mti = options['mti']

    # Detect cellsize of the DEM
    info_region = grass.read_command('g.region', flags = 'p', rast = '%s' % (r_elevation))
    dict_region = grass.parse_key_val(info_region, ':')
    resolution = float(dict_region['nsres'])
    print 'cellsize : ', resolution

    # Flow accumulation map MFD
    grass.run_command('r.watershed', elevation = r_elevation , accumulation = 'r_accumulation' , convergence = 5, flags = 'fa')
    print 'flow accumulation done.'

    # Slope map
    grass.run_command('r.slope.aspect', elevation = r_elevation , slope = 'r_slope' )
    print 'slope map done.'

    # n exponent 
    n = 0.016 * (resolution ** 0.46)
    print 'exponent : ', n

    # MTI threshold
    mti_th = 10.89 * n + 2.282
    print 'MTI threshold : ', mti_th
    
    # MTI map
    print 'Calculating mti raster map.. '
    grass.mapcalc("$r_mti = log((exp((($rast1+1)*$resolution) , $n)) / (tan($rast2+0.001)))", r_mti = r_mti, rast1 = 'r_accumulation', resolution = resolution, rast2 = 'r_slope', n = n)

    # Cleaning up
    print 'Cleaning up.. '
    grass.run_command('g.remove', rast = 'r_accumulation')
    grass.run_command('g.remove', rast = 'r_slope')

    # flood map
    print 'Calculating flood raster map.. '
    grass.mapcalc("r_flood = if($rast1 >  $mti_th, 1, null())", rast1 = r_mti, mti_th = mti_th)

    ## # Attempt to eliminate isolated pixels (doesn't seem to work properly)
    # Recategorizes data in a raster map by grouping cells that form physically discrete areas into unique categories (preliminar to r.area)
    print 'Running r.clump..'
    grass.run_command('r.clump', input = 'r_flood', output = 'r_clump')
    
    # Delete areas of less than a threshold of cells (corresponding to 1 square kilometer)
    # Calculating threshold
    th = 1000000 / resolution**2
    print 'Deleting areas of less than ', th, ' cells.. '
    grass.run_command('r.area', input = 'r_clump', output = 'r_flood_th', treshold = 'th')

    # New flood map
    grass.mapcalc("$r_flood_map = $rast1 / $rast1", r_flood_map = r_flood_map, rast1 = 'r_flood_th')

    # Cleaning up
    print 'Cleaning up.. '
    grass.run_command('g.remove', rast = 'r_clump')
    grass.run_command('g.remove', rast = 'r_flood_th')
    grass.run_command('g.remove', rast = 'r_flood')

    grass.run_command('g.message' , message = 'Done!')	

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())



