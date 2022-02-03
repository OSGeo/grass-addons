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
# %Module
# % description: Compute channels and penstocks
# % overwrite: yes
# %End
# %option G_OPT_R_ELEV
# %  required: yes
# %end
# %option G_OPT_V_INPUT
# %  key: plant
# %  label: Name of input vector map with segments of potential plants
# %  required: yes
# %end
# %option G_OPT_V_FIELD
# %  key: plant_layer
# %  label: Name of the vector map layer of plants
# %  required: no
# %  answer: 1
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_plant_id
# %  type: string
# %  description: Column name with the plant id
# %  required: no
# %  answer: plant_id
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_point_id
# %  type: string
# %  description: Column name with the point id
# %  required: no
# %  answer: cat
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_stream_id
# %  type: string
# %  description: Column name with the stream id
# %  required: no
# %  answer: stream_id
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_elevup
# %  type: string
# %  description: Column name with the elevation value at the intake (upstream) [m]
# %  required: no
# %  answer: elev_up
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_elevdown
# %  type: string
# %  description: Column name with the elevation value at the restitution (downstream) [m]
# %  required: no
# %  answer: elev_down
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_discharge
# %  type: string
# %  description: Column name with the discharge values [m3/s]
# %  required: no
# %  answer: discharge
# %  guisection: Input columns
# %end
# %option
# %  key: plant_column_power
# %  type: string
# %  description: Column name with the potential power [kW]
# %  required: no
# %  answer: pot_power
# %  guisection: Input columns
# %end
# %option
# %  key: ndigits
# %  type: integer
# %  description: Number of digits to use for the elevation in the contour line vector map
# %  required: no
# %  answer: 0
# %  guisection: Contour
# %end
# %option
# %  key: resolution
# %  type: double
# %  description: Resolution use for the contour line vector map, if 0.25 approximate 703.31 tp 703.25
# %  required: no
# %  guisection: Contour
# %end
# %option G_OPT_V_OUTPUT
# %  key: contour
# %  description: Name of the contour line vector map
# %  required: no
# %  guisection: Contour
# %end
# %option G_OPT_V_OUTPUT
# % key: output_point
# % label: Name of output vector map with potential intakes and restitution
# % required: no
# %end
# %option G_OPT_V_OUTPUT
# % key: output_struct
# % label: Name of output vector map with the structure of the plants
# % required: yes
# %end
##
## FLAGS
##
# %flag
# % key: d
# % description: Debug with intermediate maps
# %end
from __future__ import print_function

import atexit
import os

from grass.exceptions import ParameterError
from grass.pygrass.raster import RasterRow
from grass.script.core import overwrite, parser, warning
from grass.script.utils import set_path

try:
    # set python path to the shared r.green libraries
    set_path("r.green", "libhydro", "..")
    set_path("r.green", "libgreen", os.path.join("..", ".."))
    from libhydro.optimal import conv_segpoints
    from libhydro.plant import read_plants, write_structures
    from libgreen.checkparameter import check_required_columns, exception2error
    from libgreen.utils import cleanup
except ImportError:
    try:
        set_path("r.green", "libhydro", os.path.join("..", "etc", "r.green"))
        set_path("r.green", "libgreen", os.path.join("..", "etc", "r.green"))
        from libhydro.optimal import conv_segpoints
        from libhydro.plant import read_plants, write_structures
        from libgreen.checkparameter import check_required_columns, exception2error
        from libgreen.utils import cleanup
    except ImportError:
        warning("libgreen and libhydro not in the python path!")


def main(opts, flgs):
    TMPVECT = []
    DEBUG = True if flgs["d"] else False
    atexit.register(cleanup, vector=TMPVECT, debug=DEBUG)

    # check input maps
    plant = [
        opts["plant_column_discharge"],
        opts["plant_column_elevup"],
        opts["plant_column_elevdown"],
        opts["plant_column_point_id"],
        opts["plant_column_plant_id"],
        opts["plant_column_power"],
        opts["plant_column_stream_id"],
    ]
    ovwr = overwrite()

    try:
        plnt = check_required_columns(
            opts["plant"], int(opts["plant_layer"]), plant, "plant"
        )
    except ParameterError as exc:
        exception2error(exc)
        return

    if not opts["output_point"]:
        output_point = "tmp_output_point"
        TMPVECT.append(output_point)
    else:
        output_point = opts["output_point"]

    plnt = conv_segpoints(opts["plant"], output_point)

    el, mset = (
        opts["elevation"].split("@")
        if "@" in opts["elevation"]
        else (opts["elevation"], "")
    )

    elev = RasterRow(name=el, mapset=mset)
    elev.open("r")
    plnt.open("r")

    plants, skipped = read_plants(
        plnt,
        elev=elev,
        restitution="restitution",
        intake="intake",
        ckind_label="kind_label",
        cdischarge="discharge",
        celevation="elevation",
        cid_point="cat",
        cid_plant="plant_id",
    )

    plnt.close()

    # contour options
    resolution = float(opts["resolution"]) if opts["resolution"] else None
    write_structures(
        plants,
        opts["output_struct"],
        elev,
        ndigits=int(opts["ndigits"]),
        resolution=resolution,
        contour=opts["contour"],
        overwrite=ovwr,
    )
    elev.close()


if __name__ == "__main__":
    main(*parser())
