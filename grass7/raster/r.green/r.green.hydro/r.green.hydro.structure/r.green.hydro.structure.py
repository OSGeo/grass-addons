#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.structure
# AUTHOR(S):
# PURPOSE:
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
#%Module
#% description: Compute channels and penstocks
#% overwrite: yes
#%End
#%option G_OPT_R_ELEV
#%  required: yes
#%end
#%option G_OPT_V_MAP
#%  key: plant
#%  description: Name of the vector map points with the plants
#%  required: yes
#%end
#%option G_OPT_V_INPUT
#%  key: plant_layer
#%  description: Name of the vector map layer of plants
#%  required: no
#%  answer: 1
#%end
#%option
#%  key: plant_column_plant_id
#%  type: string
#%  description: Column name with the plant id
#%  required: no
#%  answer: plant_id
#%  guisection: Input columns
#%end
#%option
#%  key: plant_column_point_id
#%  type: string
#%  description: Column name with the point id
#%  required: no
#%  answer: cat
#%  guisection: Input columns
#%end
#%option
#%  key: plant_column_elevation
#%  type: string
#%  description: Column name with the elevation values [m]
#%  required: no
#%  answer: elevation
#%  guisection: Input columns
#%end
#%option
#%  key: plant_column_discharge
#%  type: string
#%  description: Column name with the discharge values [m3/s]
#%  required: no
#%  answer: discharge
#%  guisection: Input columns
#%end
#%option
#%  key: plant_column_kind
#%  type: string
#%  description: Column name (string) with the kind type of the points
#%  required: no
#%  answer: kind_label
#%  guisection: Input columns
#%end

#%option
#%  key: plant_column_kind_intake
#%  type: string
#%  description: Value contained in the column: hydro_kind that indicates the plant is an intake.
#%  required: no
#%  answer: intake
#%  guisection: Input columns
#%end
#%option
#%  key: plant_column_kind_turbine
#%  type: string
#%  description: Value contained in the column: hydro_kind that indicates the plant is a restitution.
#%  required: no
#%  answer: restitution
#%  guisection: Input columns
#%end
#%option G_OPT_V_OUTPUT
#% key: output
#% required: yes
#%end
from __future__ import print_function

import os
import atexit

from grass.exceptions import ParameterError
from grass.script.core import parser, run_command, overwrite
from grass.pygrass.utils import set_path
from grass.pygrass.raster import RasterRow
from grass.pygrass.vector import VectorTopo

# set python path to the shared r.green libraries
set_path('r.green', 'libhydro', '..')
set_path('r.green', 'libgreen', os.path.join('..', '..'))

from libgreen.utils import cleanup
from libgreen.checkparameter import check_required_columns, exception2error
from libhydro.plant import read_plants, write_structures


def main(opts, flgs):
    #TMPVECT = []
    #DEBUG = True if flgs['d'] else False
    #atexit.register(cleanup, vect=TMPVECT, debug=DEBUG)
    # check input maps
    plant = [opts['plant_column_kind'], opts['plant_column_discharge'],
             opts['plant_column_point_id'], opts['plant_column_plant_id']]
    ovwr = overwrite()
    #import pdb; pdb.set_trace()
    try:
        plnt = check_required_columns(opts['plant'], int(opts['plant_layer']),
                                      plant, 'plant')
    except ParameterError as exc:
        exception2error(exc)
        return

    el, mset = (opts['elevation'].split('@') if '@' in opts['elevation']
                else (opts['elevation'], ''))

    elev = RasterRow(name=el, mapset=mset)
    elev.open('r')
    plnt.open('r')
    #import pdb; pdb.set_trace()
    plants, skipped = read_plants(plnt, elev=elev,
                                  restitution=opts['plant_column_kind_turbine'],
                                  intake=opts['plant_column_kind_intake'],
                                  ckind_label=opts['plant_column_kind'],
                                  cdischarge=opts['plant_column_discharge'],
                                  celevation=opts['plant_column_elevation'],
                                  cid_point=opts['plant_column_point_id'],
                                  cid_plant=opts['plant_column_plant_id'])
    plnt.close()
    #import ipdb; ipdb.set_trace()

    write_structures(plants, opts['output'], elev, overwrite=ovwr)
    elev.close()


if __name__ == "__main__":
    main(*parser())
