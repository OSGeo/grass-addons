#!/usr/bin/env python3
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:    r.centroids
#
# AUTHOR(S): Caitlin Haedrich (wrapper for r.volume, caitlin dot haedrich gmail com)

#
# PURPOSE:   Creates vector map of centroids from a raster of "clumps"; r.clumps
#            creates "clumps" of data.
#
# COPYRIGHT: (C) 1997-2016 by the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

#%module
#% description: Creates vector map of centroids from raster of "clumps"
#% keyword: raster
#% keyword: centroid
#% keyword: clumps
#% keyword: vector
#% keyword: centerpoint
#%end

#%option G_OPT_R_INPUT
#% key: input
#% description: raster of clumps, cluster of same-valued pixels
#% required: yes
#%end

#%option G_OPT_V_OUTPUT
#% key: output
#% description: name of output vector
#% required: yes
#%end


import sys
import grass.script as gs


def raster_exists(name):
    """Check if the raster map exists, call GRASS fatal otherwise"""
    ffile = gs.find_file(name, element='raster')
    if not ffile['fullname']:
        gs.fatal(_("Raster map <%s> not found") % name)

def main(options, flags):
    # options and flags into variables
    ipl = options['input']
    raster_exists(ipl)
    opl = options['output'] #'testingCentroids'

    gs.run_command('r.volume', input=ipl, clump=ipl, centroids=opl)

if __name__ == "__main__":
    options, flags = gs.parser()
    main(options, flags)
    exit(0)
