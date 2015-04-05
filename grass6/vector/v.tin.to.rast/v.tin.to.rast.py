#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:     v.tin.to.rast
#
# AUTHOR(S):  Antonio Alliegro Civil Engineer
#             Salerno, Italy
#             antonioall(at)libero.it
#
#             Alexander Muriy
#             (Institute of Environmental Geoscience, Moscow, Russia)    
#             amuriy(at)gmail.com   
#
# PURPOSE:    Converts (rasterize) a TIN map into a raster map
#
# COPYRIGHT:  (C) 2011-2015 Antonio Alliegro, 2015 Alexander Muriy,
#             and the GRASS Development Team
#
#             This program is free software under the GNU General
#             Public License (>=v2). Read the file COPYING that
#             comes with GRASS for details.
#
############################################################################

#%module
#% description: Converts (rasterize) a TIN map into a raster map
#% keywords: TIN, vector, raster, conversion
#%end
#%option
#% key: input
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: tin
#% description: Name of input TIN map
#% required: yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% key_desc: raster
#% description: Name of output raster map
#% required: yes
#%end
#****************************************************************                        

import sys
import os
import atexit

try:
    import grass.script as grass
except:
    try:
        from grass.script import core as grass
    except:
        if not os.environ.has_key("GISBASE"):
            print "You must be in GRASS GIS to run this program."
            sys.exit(1)

grass_version = grass.version().get('version')[0:3]
if grass_version != '6.4':
    grass.fatal(_("Sorry, this script works in GRASS 6.4.* only"))
else:
    from grass.lib.gis    import *
    from grass.lib.vector import *


def cleanup():
    nuldev = file(os.devnull, 'w')
    if tmp:
        grass.run_command('g.remove', rast = '%s' % tmp,
                          quiet = True, stderr = nuldev)
        
def main():
    
    global nuldev, tmp
    nuldev = file(os.devnull, 'w')
    tmp = "v_tin_to_rast_%d" % os.getpid()

        
    input = options['input']
    output = options['output']
    
    # initialize GRASS library
    G_gisinit('')

    # check if vector map exists
    mapset = G_find_vector2(input, "")
    if not mapset:
        grass.fatal("Vector map <%s> not found" % input)

    # define map structure 
    map_info = pointer(Map_info())
    
    # set vector topology to level 2 
    Vect_set_open_level(2)

    # opens the vector map
    Vect_open_old(map_info, input, mapset)

    Vect_maptype_info(map_info, input, mapset)
    
    # check if vector map is 3D
    if Vect_is_3d(map_info):
        grass.message("Vector map <%s> is 3D" % input)
    else:
        grass.fatal("Vector map <%s> is not 3D" % input)

    # allocation of the output buffer using the values of the current region
    window = pointer(Cell_head())
    G_get_window(window)
    nrows = window.contents.rows
    ncols = window.contents.cols
    xref = window.contents.west
    yref = window.contents.south
    xres = window.contents.ew_res
    yres = window.contents.ns_res

    outrast = []
    for i in range(nrows):
        outrast[i:] = [G_allocate_d_raster_buf()]
        
    # create new raster
    outfd = G_open_raster_new(output, DCELL_TYPE)
    if outfd < 0:
        grass.fatal("Impossible to create a raster <%s>" % output)

    # insert null values in cells
    grass.message(_("Step 1/4: Inserting null values in cells..."))
    for i in range(nrows):
        G_set_d_null_value(outrast[i], ncols)
        G_percent(i, nrows, 2)

    #####  main work #####
    grass.message(_("Step 2/4: TIN preprocessing..."))
    z = c_double()
    G_percent(0, nrows, 2)
    Vect_tin_get_z(map_info, xref, yref, byref(z), None, None)

    grass.message(_("Step 3/4: Converting TIN to raster..."))
    for i in range(nrows):
        for j in range(ncols):
            x = xref + j * xres
            y = yref + i * yres
            Vect_tin_get_z(map_info, x, y, byref(z), None, None)
            outrast[i][j] = z
        G_percent(i, nrows, 2)

    grass.message(_("Step 4/4: Writing raster map..."))
    for i in range(nrows - 1, -1, -1):
        if G_put_d_raster_row(outfd, outrast[i]) < 0:
            grass.fatal(_("Error writing raster <%s>" % output))
        G_percent(nrows - i, nrows, 2)

    # clear buffer
    for i in range(nrows):
        G_free(outrast[i])

    # close raster
    G_close_cell(outfd)

    # close vector
    Vect_close(map_info)
    
    # cut output raster to TIN vertical range
    vtop = grass.read_command('v.info', flags = 'g',
                              map = input).rsplit()[4].split('=')[1]
    vbottom = grass.read_command('v.info', flags = 'g',
                                 map = input).rsplit()[5].split('=')[1]

    tmp = "v_tin_to_rast_%d" % os.getpid()
    grass.mapcalc("$tmp = if($vbottom < $output && $output < $vtop, $output, null())",
                  tmp = tmp, output = output, vbottom = vbottom, vtop = vtop,
                  quiet = True, stderr = nuldev)

    grass.parse_command('g.rename', rast = (tmp, output),
                      quiet = True, stderr = nuldev)

    # write cmd history:
    grass.run_command('r.support', map = output,
                      title = "%s" % output, history="", 
                      description = "generated by v.tin.to.rast")
    grass.raster_history(output)

    grass.message(_("Done."))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
                        
