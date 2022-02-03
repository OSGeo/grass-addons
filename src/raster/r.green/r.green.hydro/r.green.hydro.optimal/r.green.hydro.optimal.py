#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.optimal
# AUTHOR(S):   Giulia Garegnani
# PURPOSE:     Calculate the optimal position of a plant along a river
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
# %module
# % description: Detect the position of the potential hydropower plants that can produce the highest possible power
# % keyword: raster
# % overwrite: yes
# %end
# %option G_OPT_R_ELEV
# %  required: yes
# %end
# %option G_OPT_R_INPUT
# % key: discharge
# % label: Name of river discharge [m^3/s]
# % required: yes
# %end
# %option G_OPT_V_INPUT
# % key: river
# % label: Name of vector map with interested segments of rivers
# % required: yes
# %end
# %flag
# % key: d
# % description: Debug with intermediate maps
# %end
# %flag
# % key: c
# % description: Clean vector lines
# %end
# %option
# % key: len_plant
# % type: double
# % description: Maximum length of the plant [m]
# % required: yes
# % answer: 10000
# %end
# %option
# % key: len_min
# % type: double
# % description: Minimum length of the plant [m]
# % required: yes
# % answer: 10
# %end
# %option
# % key: distance
# % type: double
# % description: Minimum distance among plants [m]
# % required: yes
# % answer: 0.5
# %end
# %option
# % key: p_max
# % type: double
# % description: Maximum mean power [kW]
# % required: no
# %end
# %option
# % key: p_min
# % type: double
# % description: Minimum mean power [kW]
# % answer: 10.0
# % required: yes
# %end
# %option G_OPT_V_OUTPUT
# % key: output_plant
# % label: Name of output vector map with potential power for each river segment [kW]
# % required: yes
# %end
# %option G_OPT_V_OUTPUT
# % key: output_point
# % label: Name of output vector map with potential power intakes and restitution [kW]
# % required: no
# %end
# %option
# % key: efficiency
# % type: double
# % description: Efficiency [-]
# % required: yes
# % answer: 1
# %END

from __future__ import print_function

# import system libraries
import atexit
import os
import sys

# from grass.script import mapcalc
from grass.pygrass.messages import get_msgr
from grass.script import core as gcore

# from grass.pygrass.raster.buffer import Buffer
from grass.script.utils import set_path

try:
    # set python path to the shared r.green libraries
    set_path("r.green", "libhydro", "..")
    set_path("r.green", "libgreen", os.path.join("..", ".."))
    from libgreen.utils import cleanup
    from libgreen.utils import dissolve_lines
    from libhydro.optimal import find_segments
    from libhydro.optimal import write_plants
    from libhydro.optimal import write_points
except ImportError:
    try:
        set_path("r.green", "libhydro", os.path.join("..", "etc", "r.green"))
        set_path("r.green", "libgreen", os.path.join("..", "etc", "r.green"))
        from libgreen.utils import cleanup
        from libgreen.utils import dissolve_lines
        from libhydro.optimal import find_segments
        from libhydro.optimal import write_plants
        from libhydro.optimal import write_points
    except ImportError:
        gcore.warning("libgreen and libhydro not in the python path!")


##################################################
# optimization problem
# the coordinate along the river is s
# the delta (distance betwwen intake and restitution) is delta
# the discharge is q
# the equation is f=[h(s,0)-h(s,delta)]*q
# x = [s,delta]
# s e delta are integer (the index of the vector)
#


if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def main(options, flags):
    TMPRAST, TMPVECT, DEBUG = [], [], False
    atexit.register(cleanup, raster=TMPRAST, vector=TMPVECT, debug=DEBUG)
    elevation = options["elevation"]
    river = options["river"]  # raster
    discharge = options["discharge"]  # vec
    len_plant = float(options["len_plant"])
    len_min = float(options["len_min"])
    distance = float(options["distance"])
    efficiency = float(options["efficiency"])
    output_plant = options["output_plant"]
    output_point = options["output_point"]
    if options["p_max"]:
        p_max = float(options["p_max"])
    else:
        p_max = None
    p_min = float(options["p_min"])
    DEBUG = flags["d"]
    c = flags["c"]
    msgr = get_msgr()
    # import ipdb; ipdb.set_trace()

    if c:
        msgr.message("\Clean rivers\n")
        TMPVECT = [("tmprgreen_%i_cleanb" % os.getpid())]
        pid = os.getpid()
        dissolve_lines(river, "tmprgreen_%i_cleanb" % os.getpid())
        river = "tmprgreen_%i_cleanb" % pid
        # number of cell of the river
    # range for the solution
    msgr.message("\Loop on the category of segments\n")

    range_plant = (len_min, len_plant)
    plants = find_segments(river, discharge, elevation, range_plant, distance, p_max)

    # add l_min
    if output_point:
        write_points(plants, output_point, efficiency, p_min)
    write_plants(plants, output_plant, efficiency, p_min)


if __name__ == "__main__":
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
