#!/usr/bin/env python

############################################################################
#
# MODULE:    r.centroids
#
# AUTHOR(S): Caitlin Haedrich (caitlin dot haedrich gmail com) and 
#
# PURPOSE:   Wrapper for r.volume. Creates vector map of centroids from a raster 
#            of "clumps"; r.clumps creates "clumps" of data.
#
# COPYRIGHT: (C) 2021 by Caitlin Haedrich and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

#%module
#% description: Creates vector map of centroids from raster of "clumps".
#% keyword: raster
#% keyword: centroid
#% keyword: clumps
#% keyword: vector
#% keyword: centerpoint
#%end

#%option G_OPT_R_INPUT
#% key: input
#% description: Raster of clumps, cluster of same-valued pixels
#% required: yes
#%end

#%option G_OPT_V_OUTPUT
#% key: output
#% required: yes
#%end

import grass.script as gs

def main(options, flags):
    # options and flags into variables
    ipl = options['input']
    opl = options['output']

    gs.run_command('r.volume', input=ipl, clump=ipl, centroids=opl, errors="exit")

if __name__ == "__main__":
    main(gs.parser()[0], gs.parser()[1])
