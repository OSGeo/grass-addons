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
# COPYRIGHT:    (C) 2013-2014 by the GRASS Development Team
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
#% options: 2-360
#%end
#%option
#% key: maxdistance
#% description: The maximum distance to consider when finding the horizon height
#% type: double
#% required: no
#%end
#%option
#%  key: basename
#%  type: string
#%  multiple: no
#%  description: Set the basename for the intermediate maps
#%end


import sys
import os
import atexit

import grass.script.core as gcore
import grass.script.raster as grast
from grass.pygrass.messages import get_msgr


TMP_NAME = 'tmp_horizon_' + str(os.getpid())
CLEANUP = True


def cleanup():
    if CLEANUP:
        gcore.run_command('g.remove', flags = 'f', type = 'rast', pattern =TMP_NAME + "*")


def main():
    elev = options['input']
    output = options['output']
    n_dir = int(options['ndir'])
    global TMP_NAME, CLEANUP
    if options['basename']:
        TMP_NAME = options['basename']
        CLEANUP = False
    horizon_step = 360. / n_dir
    msgr = get_msgr()

    # checks if there are already some maps
    old_maps = _get_horizon_maps()
    if old_maps:
        if not gcore.overwrite():
            CLEANUP = False
            msgr.fatal(_("You have to first check overwrite flag or remove the following maps:\n"
                         "{names}").format(names=','.join(old_maps)))
        else:
            msgr.warning(_("The following maps will be overwritten: {names}").format(names=','.join(old_maps)))

    ret = gcore.run_command('r.horizon', elevin=elev, direction=0, horizonstep=horizon_step,
                            horizon=TMP_NAME, flags='d')
    if ret != 0:
        msgr.fatal(_("r.horizon failed to compute horizon elevation angle maps. "
                     "Please report this problem to developers."))

    msgr.message(_("Computing sky view factor ..."))
    new_maps = _get_horizon_maps()
    expr = "{out} = 1 - (sin({first}) ".format(first=new_maps[0], out=output)
    for horizon in new_maps[1:]:
        expr += "+ sin({name}) ".format(name=horizon)
    expr += ") / {n}.".format(n=len(new_maps))

    grast.mapcalc(exp=expr)
    gcore.run_command('r.colors', map=output, color='grey')

    return 0


def _get_horizon_maps():
    return gcore.mlist_grouped('rast',
                               pattern=TMP_NAME + "*")[gcore.gisenv()['MAPSET']]


if __name__ == "__main__":
    options, flags = gcore.parser()
    atexit.register(cleanup)
    sys.exit(main())
