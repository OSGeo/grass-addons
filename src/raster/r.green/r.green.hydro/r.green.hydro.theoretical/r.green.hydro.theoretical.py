#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.potential
# AUTHOR(S):   Giulia Garegnani, Pietro Zambelli
# PURPOSE:     Calculate the theoretical hydropower energy potential for each basin and segments of river
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

# %module
# % description: Calculate the hydropower energy potential for each basin starting from discharge and elevation data. If existing plants are available it computes the potential installed power in the available part of the rivers.
# % keyword: raster
# % keyword: hydropower
# % keyword: renewable energy
# %end
# %option G_OPT_R_ELEV
# % required: yes
# %end
# %option G_OPT_R_INPUT
# % key: discharge
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of input river discharge raster map [m3/s]
# % required: yes
# %end
# %option G_OPT_V_INPUT
# % key: rivers
# % type: string
# % gisprompt: old,vector,vector
# % key_desc: name
# % description: Name of river network input vector map
# % required: no
# %end
# %option G_OPT_V_INPUT
# % key: lakes
# % type: string
# % gisprompt: old,vector,vector
# % key_desc: name
# % description: Name of lakes input vector map
# % required: no
# %end
# %option
# % key: threshold
# % type: string
# % description: Minimum size of exterior watershed basin
# % required: yes
# % answer: 0
# % guisection: Basin Potential
# %end
# %option G_OPT_R_INPUT
# % key: basins
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of basin map obtained by r.watershed
# % required: no
# % guisection: Basin Potential
# %end
# %option G_OPT_R_INPUT
# % key: stream
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of stream map obtained by r.watershed
# % required: no
# % guisection: Basin Potential
# %end
# TODO: add flags
# %flag
# % key: d
# % description: Debug with intermediate maps
# %end
# %option G_OPT_V_OUTPUT
# % key: output
# % type: string
# % key_desc: name
# % description: Name of output vector map with basin potential [MWh]
# % required: yes
# % guisection: Basin Potential
# %END

from __future__ import print_function

import atexit

# import system libraries
import os
import sys

from grass.pygrass.messages import get_msgr
from grass.script import core as gcore
from grass.script.utils import set_path

try:
    # set python path to the shared r.green libraries
    set_path("r.green", "libhydro", "..")
    set_path("r.green", "libgreen", os.path.join("..", ".."))
    from libgreen.utils import cleanup
    from libhydro.basin import dtm_corr
    from libhydro.plant import power2energy
    from libhydro import basin
    from libgreen.utils import check_overlay_rr

    # from libgreen.utils import check_overlay_rv
    from libgreen.utils import raster2numpy
    from libgreen.utils import remove_pixel_from_raster
except ImportError:
    try:
        set_path("r.green", "libhydro", os.path.join("..", "etc", "r.green"))
        set_path("r.green", "libgreen", os.path.join("..", "etc", "r.green"))
        from libgreen.utils import cleanup
        from libhydro.basin import dtm_corr
        from libhydro.plant import power2energy
        from libhydro import basin
        from libgreen.utils import check_overlay_rr

        # from libgreen.utils import check_overlay_rv
        from libgreen.utils import raster2numpy
        from libgreen.utils import remove_pixel_from_raster
    except ImportError:
        gcore.warning("libgreen and libhydro not in the python path!")


if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def main(options, flags):
    #############################################################
    # inizialitation
    #############################################################
    pid = os.getpid()
    DEBUG = flags["d"]
    atexit.register(cleanup, pattern=("tmprgreen_%i*" % pid), debug=DEBUG)
    # TOD_add the possibilities to have q_points
    # required
    discharge = options["discharge"]
    dtm = options["elevation"]
    # basin potential
    basins = options["basins"]
    stream = options["stream"]  # raster
    rivers = options["rivers"]  # vec
    lakes = options["lakes"]  # vec
    E = options["output"]
    threshold = options["threshold"]

    # existing plants
    #    segments = options['segments']
    #    output_segm = options['output_segm']
    #    output_point = options['output_point']
    #    hydro = options['hydro']
    #    hydro_layer = options['hydro_layer']
    #    hydro_kind_intake = options['hydro_kind_intake']
    #    hydro_kind_turbine = options['hydro_kind_turbine']
    #    other = options['other']
    #    other_kind_intake = options['other_kind_intake']
    #    other_kind_turbine = options['other_kind_turbine']

    # optional

    msgr = get_msgr()
    # info = gcore.parse_command('g.region', flags='m')
    # print info
    #############################################################
    # check temporary raster

    if rivers:
        # cp the vector in the current mapset in order to clean it
        tmp_river = "tmprgreen_%i_river" % pid
        to_copy = "%s,%s" % (rivers, tmp_river)
        gcore.run_command("g.copy", vector=to_copy)
        rivers = tmp_river
        gcore.run_command("v.build", map=rivers)
        tmp_dtm_corr = "tmprgreen_%i_dtm_corr" % pid
        dtm_corr(dtm, rivers, tmp_dtm_corr, lakes)
        basins, stream = basin.check_compute_basin_stream(
            basins, stream, tmp_dtm_corr, threshold
        )
    else:
        basins, stream = basin.check_compute_basin_stream(
            basins, stream, dtm, threshold
        )

    perc_overlay = check_overlay_rr(discharge, stream)
    # pdb.set_trace()
    try:
        p = float(perc_overlay)
        if p < 90:
            warn = (
                "Discharge map doesn't overlay all the stream map."
                "It covers only the %s %% of rivers"
            ) % (perc_overlay)
            msgr.warning(warn)
    except ValueError:
        msgr.error("Could not convert data to a float")
    except:
        msgr.error("Unexpected error")

    msgr.message("\\Init basins\n")
    # pdb.set_trace()
    #############################################################
    # core
    #############################################################
    basins_tot, inputs = basin.init_basins(basins)

    msgr.message("\nBuild the basin network\n")
    #############################################################
    # build_network(stream, dtm, basins_tot) build relationship among basins
    # Identify the closure point with the r.neigbours module
    # if the difference betwwen the stream and the neighbours
    # is negative it means a new subsanin starts
    #############################################################
    basin.build_network(stream, dtm, basins_tot)
    stream_n = raster2numpy(stream)
    discharge_n = raster2numpy(discharge)
    basin.fill_basins(inputs, basins_tot, basins, dtm, discharge_n, stream_n)

    ###################################################################
    # check if lakes and delate stream in lakes optional
    ###################################################################

    if lakes:
        remove_pixel_from_raster(lakes, stream)

    ####################################################################
    # write results
    ####################################################################
    # if not rivers or debug I write the result in the new vector stream
    msgr.message("\nWrite results\n")

    basin.write_results2newvec(stream, E, basins_tot, inputs)
    power2energy(E, "Etot_kW", 8760)


if __name__ == "__main__":
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
