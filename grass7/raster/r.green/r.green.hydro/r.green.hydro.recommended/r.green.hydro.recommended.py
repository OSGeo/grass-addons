#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.reccomended
# AUTHOR(S):   Giulia Garegnani
# PURPOSE:     Calculate the optimal position of a plant along a river
#              following user reccomandations
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

#%module
#% description: Hydropower energy potential with user reccomandations
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
#% key: river
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of vector map with interested segments of rivers
#% required: yes
#%end
#%option
#% key: dtm
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
#% key: efficiency
#% type: double
#% key_desc: name
#% description: efficiency [-]]
#% required: yes
#% answer: 0.8
#%end
#%option
#% key: len_plant
#% type: double
#% key_desc: name
#% description: maximum length plant [m]
#% required: yes
#% answer: 100
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

# r.green lib
set_path('r.green', 'libhydro', '..')
set_path('r.green', 'libgreen', os.path.join('..', '..'))
# finally import the module in the library
from libgreen.utils import cleanup

DEBUG = False
TMPRAST = []

if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def main(opts, flgs):
    global DEBUG, TMPRAST
    atexit.register(cleanup, rast=TMPRAST, debug=DEBUG)
    dtm = options['dtm']
    river = options['river']  # raster
    discharge = options['discharge']  # vec
    len_plant = options['len_plant']
    len_min = options['len_min']
    distance = options['distance']
    output_plant = options['output_plant']
    output_point = options['output_point']
    area = options['area']
    buff = options['buff']
    efficiency = options['efficiency']
    DEBUG = flags['d']
    c = flags['c']
    msgr = get_msgr()

    TMPRAST = ['new_river', 'buff_area']
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

    gcore.run_command('r.green.hydro.optimal',
                      flags='c',
                      discharge=discharge,
                      river=river,
                      dtm=dtm,
                      len_plant=len_plant,
                      output_plant=output_plant,
                      output_point=output_point,
                      distance=distance,
                      len_min=len_min,
                      efficiency=efficiency)

if __name__ == "__main__":
    atexit.register(cleanup)
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
