#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.legal
# AUTHOR(S):   Giulia Garegnani
# PURPOSE:     Calculate the optimal position of a plant along a river
#              following legal constrains
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

#%module
#% description: Hydropower energy potential with legal constrains
#% keywords: raster
#% overwrite: yes
#%end
#%option
#% key: discharge
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of river discharge [l/s]
#% required: yes
#%end
#%option
#% key: mvf
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of river mvf discharge [l/s]
#% required: yes
#%end
#%option
#% key: river
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of vector map with interested segments of rivers
#% required: yes
#%end
#%option
#% key: elevation
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of dtm [m]
#% required: yes
#%end
#%flag
#% key: d
#% description: Debug with intermediate maps
#%end
#%flag
#% key: c
#% description: Clean vector lines
#%end
#%option
#% key: len_plant
#% type: double
#% key_desc: name
#% description: maximum length plant [m]
#% required: yes
#% answer: 100000000
#%end
#%option
#% key: len_min
#% type: double
#% key_desc: name
#% description: minimum length plant [m]
#% required: yes
#% answer: 10
#%end
#%option
#% key: distance
#% type: double
#% description: minimum distance among plants.
#% required: yes
#% answer: 0.5
#%end
#%option
#% key: area
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: areas to be excluded.
#% required: no
#%end
#%option
#% key: buff
#% type: double
#% description: buffer for areas to be excluded.
#% required: no
#%end
#%option
#% key: output_plant
#% type: string
#% key_desc: name
#% description: Name of output vector with potential segments
#% required: no
#%end
#%option
#% key: output_point
#% type: string
#% key_desc: name
#% description: Name of output vector with potential intakes and restitution
#% required: yes
#%END

# import system libraries
from __future__ import print_function
import os
import sys
import atexit

# import grass libraries
from grass.script import core as gcore
from grass.pygrass.utils import set_path
from grass.pygrass.messages import get_msgr
from grass.script import mapcalc

# r.green lib
set_path('r.green', 'libhydro', '..')
set_path('r.green', 'libgreen', os.path.join('..', '..'))
# finally import the module in the library
from libgreen.utils import cleanup


if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exitd(1)


def main(opts, flgs):   
    DEBUG = False
    TMPRAST = []
    atexit.register(cleanup, rast=TMPRAST, debug=DEBUG)
    dtm = options['elevation']
    river = options['river']  # raster
    discharge = options['discharge']  # vec
    mvf = options['mvf']  # vec
    len_plant = float(options['len_plant'])
    len_min = float(options['len_min'])
    distance = float(options['distance'])
    output_plant = options['output_plant']
    output_point = options['output_point']
    area = options['area']
    buff = options['buff']
    DEBUG = flags['d']
    c = flags['c']
    msgr = get_msgr()

    TMPRAST = []
    if not gcore.overwrite():
        for m in TMPRAST:
            if gcore.find_file(m)['name']:
                msgr.fatal(_("Temporary raster map %s exists") % (m))
                #FIXME:check if it works for vectors

    if area:
        if buff:
            gcore.run_command('v.buffer',
                              input=area,
                              output='buff_area',
                              distance=buff)
            area = 'buff_area'

        gcore.run_command('v.overlay',
                          ainput=river,
                          binput=area,
                          operator='not',
                          output='new_river')
        river = 'new_river'

    command = ('q_leg= %s - %s') % (discharge, mvf)
    mapcalc(command, overwrite=True)

    gcore.run_command('r.green.hydro.optimal',
                      flags=c,
                      discharge=discharge,
                      river=river,
                      elevation=dtm,
                      len_plant=len_plant,
                      output_plant=output_plant,
                      output_point=output_point,
                      distance=distance,
                      len_min=len_min,
                      efficiency=1)

    #TODO: add the possibility to exclude vector segments of rivers
    # by using the attribute of the river input

if __name__ == "__main__":
    atexit.register(cleanup)
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
