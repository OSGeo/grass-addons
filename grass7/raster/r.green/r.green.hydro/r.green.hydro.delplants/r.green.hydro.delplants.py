#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.del_plants
# AUTHOR(S):   Pietro Zambelli & Giulia Garegnani
# PURPOSE:     Delete segmets where there is an existing plant
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
#%Module
#% description: Delete segmets where there is an existing plant
#% overwrite: yes
#%End
#%option G_OPT_V_INPUT
#%  key: hydro
#%  description: Name of the vector map point of hydro plants.
#%  required: yes
#%end
#%option G_OPT_V_FIELD
#%  key: hydro_layer
#%  description: Name of the vector map layer of the hydro plant, with the following attributes: kind (water intake/turbine), discharge [l/s], working hours [hours], altitute[m], id point, id plant
#%  required: no
#%  answer: 1
#%end
#%option G_OPT_V_INPUT
#%  key: river
#%  description: Name of the vector map with the streams.
#%  required: yes
#%end
#%option G_OPT_V_OUTPUT
#%  description: Name of the vector map with the stream segments without plants.
#%  required: yes
#%end
#%option G_OPT_V_OUTPUT
#%  key: plants
#%  description: Name of the vector map with the stream segments already with plants.
#%  required: no
#%end
#%option
#%  key: hydro_kind_intake
#%  type: string
#%  description: Value contained in the column: hydro_kind that indicate the plant is an intake.
#%  required: no
#%  answer: intake
#%end
#%option
#%  key: hydro_kind_turbine
#%  type: string
#%  description: Value contained in the column: hydro_kind that indicate the plant is an intake.
#%  required: no
#%  answer: turbine
#%end
#%option G_OPT_R_ELEV
#%  required: yes
#%end
#%option G_OPT_V_MAP
#%  key: other
#%  description: Name of the vector map point of other plants such as irrigation, acqueducts, etc.
#%  required: no
#%end
#%option G_OPT_V_INPUT
#%  key: other_layer
#%  description: Name of the vector map layer of other plants, with the following attributes: kind (water intake/turbine), discharge [m3/year], id point, id plant
#%  required: no
#%  answer: 1
#%end
#%option
#%  key: other_kind_intake
#%  type: string
#%  description: Value contained in the column: other_kind that indicate the plant is an intake.
#%  required: no
#%  answer: intake
#%end
#%option
#%  key: other_kind_turbine
#%  type: string
#%  description: Value contained in the column: other_kind that indicate the plant is an intake.
#%  required: no
#%  answer: turbine
#%end
#%option
#%  key: efficiency
#%  type: double
#%  description: Plant efficiency.
#%  required: no
#%  answer: 0.8
#%end
#%flag
#% key: d
#% description: Debug with intermediate maps
#%end
from __future__ import print_function

# import stadard libraries
import os
import atexit

# import GRASS libraries
from grass.exceptions import ParameterError
from grass.script.core import parser, overwrite
from grass.pygrass.vector import VectorTopo
from grass.pygrass.raster import RasterRow
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.messages import get_msgr
from grass.pygrass.utils import set_path

set_path('r.green', 'libhydro', '..')
set_path('r.green', 'libgreen', os.path.join('..', '..'))

# finally import the module in the library
from libgreen.utils import cleanup
from libgreen.checkparameter import (check_required_columns,
                                     exception2error)
from libhydro.plant import read_plants, write_plants


def main(opts, flgs):
    TMPVECT = []
    DEBUG = True if flgs['d'] else False
    atexit.register(cleanup, vect=TMPVECT, debug=DEBUG)
    # check input maps
    rhydro = ['kind', 'discharge', 'id_point', 'id_plant']
    rother = ['kind', 'discharge', 'id_point', 'id_plant']
    ovwr = overwrite()

    try:
        hydro = check_required_columns(opts['hydro'], int(opts['hydro_layer']),
                                       rhydro, 'hydro')
        if opts['other']:
            other = check_required_columns(opts['other'], opts['other_layer'],
                                           rother, 'other')
        else:
            other = None
        #minflow = check_float_or_raster(opts['minflow'])
    except ParameterError as exc:
        exception2error(exc)
    # TODO: do we really nead the efficiency of the plant here?
    #efficiency = float(opts['efficiency'])

    # start working
    hydro.open('r')
    el, mset = (opts['elevation'].split('@') if '@' in opts['elevation']
                else (opts['elevation'], ''))
    elev = RasterRow(name=el, mapset=mset)
    elev.open('r')
    plants, skipped = read_plants(hydro, elev=elev,
                                  restitution=opts['hydro_kind_turbine'],
                                  intake=opts['hydro_kind_intake'])
    hydro.close()
    rvname, rvmset = (opts['river'].split('@') if '@' in opts['river']
                      else (opts['river'], ''))

    vplants = opts['plants'] if opts['plants'] else 'tmpplants'
    #FIXME: I try with tmpplants in my mapset and it doesn'work
    if opts['plants'] == '':
        TMPVECT.append(vplants)
    with VectorTopo(rvname, rvmset, mode='r') as river:
        write_plants(plants, vplants, river, elev, overwrite=ovwr)

    if skipped:
        for skip in skipped:
            print("Plant: %r, Point: %r, kind: %r" % skip)
    elev.close()

    # compute a buffer around the plants
    buff = vplants + 'buff'
    v.buffer(input=vplants, type='line', output=buff, distance=0.1,
             overwrite=ovwr)
    TMPVECT.append(buff)
    # return all the river segments that are not already with plants
    v.overlay(flags='t', ainput=opts['river'], atype='line', binput=buff,
              operator='not', output=opts['output'], overwrite=ovwr)


if __name__ == "__main__":
    main(*parser())
