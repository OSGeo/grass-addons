#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       r.skyview
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      Implementation of Sky-View Factor visualization technique
#
# COPYRIGHT:    (C) 2013 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (version 2). Read the file COPYING that comes with GRASS
#		for details.
#
##############################################################################

#%module
#% description: Computes Sky-View Factor visualization technique
#% keywords: raster
#% keywords: visualization
#%end
#%option G_OPT_R_INPUT
#%end
#%option G_OPT_R_OUTPUT
#%end
#%option
#% key: ndir
#% description: Number of directions (8 to 32 recommended)
#% type: integer
#% required: yes
#% answer: 16
#% options: 2-64
#%end
#%option
#% key: maxdistance
#% description: The maximum distance to consider when finding the horizon height
#% type: double
#% required: no
#%end


import sys
import os
import atexit

import grass.script.core as gcore
import grass.script.raster as grast


def cleanup():
    gcore.run_command('g.mremove', rast="*{pid}*".format(pid=os.getpid()), flags='f')


def main():
    elev = options['input']
    output = options['output']
    n_dir = int(options['ndir'])
    horizon_step = 360. / n_dir

    tmp_rast_name_hor = 'tmp_horizon_' + str(os.getpid())
    ret = gcore.run_command('r.horizon', elevin=elev, direction=0, horizonstep=horizon_step,
                            horizon=tmp_rast_name_hor, flags='d')
    if ret != 0:
        gcore.fatal(_("r.horizon failed to compute horizon elevation angle maps. "
                      "Please report this problem to developers."))

    gcore.info(_("Computing sky view factor ..."))
    new_maps = gcore.mlist_grouped('rast',
                                   pattern=tmp_rast_name_hor + "*")[gcore.gisenv()['MAPSET']]
    expr = "{out} = 1 - (sin({first}) ".format(first=new_maps[0], out=output)
    for horizon in new_maps[1:]:
        expr += "+ sin({name}) ".format(name=horizon)
    expr += ") / {n}.".format(n=len(new_maps))

    grast.mapcalc(exp=expr)
    gcore.run_command('r.colors', map=output, color='grey')

    return 0


if __name__ == "__main__":
    options, flags = gcore.parser()
    atexit.register(cleanup)
    sys.exit(main())
