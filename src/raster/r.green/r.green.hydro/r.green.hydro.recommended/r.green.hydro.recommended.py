#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.recommended
# AUTHOR(S):   Giulia Garegnani
# PURPOSE:     Calculate the optimal position of a plant along a river
#              following user's recommendations
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

# %module
# % description: Calculate hydropower energy potential with user's recommendations
# % keyword: raster
# %end

##
## REQUIRED INPUTS
##
# %option G_OPT_R_ELEV
# % required: yes
# %end
# %option G_OPT_V_INPUT
# % key: river
# % label: Name of vector map with interesting segments of rivers
# % description: Vector map with the segments of the river that will be analysed
# % required: yes
# %end

##
## OPTIONAL INPUTS
##
# %option
# % key: efficiency
# % type: double
# % key_desc: double
# % description: Efficiency [0-1]
# % required: yes
# % options: 0-1
# % answer: 1
# %end
# %option
# % key: len_plant
# % type: double
# % key_desc: double
# % description: Maximum plant length [m]
# % required: yes
# % answer: 100
# %end
# %option
# % key: len_min
# % type: double
# % key_desc: double
# % description: Minimum plant length [m]
# % required: yes
# % answer: 10
# %end
# %option
# % key: distance
# % type: double
# % key_desc: double
# % description: Minimum distance among plants [m]
# % required: yes
# % answer: 0.5
# %end
# %option
# % key: p_min
# % type: double
# % key_desc: double
# % description: Minimum mean power [kW]
# % answer: 10.0
# % required: no
# %end
# %option
# % key: n
# % type: double
# % description: Number of operative hours per year [hours/year]
# % required: no
# % answer: 3392
# %end

##
## OPTIONAL INPUTS: LEGAL DISCHARGE
##
# %option G_OPT_R_INPUT
# % key: discharge_current
# % label: Current discharge [m3/s]
# % required: yes
# % guisection: Legal Discharge
# %end
# %option G_OPT_R_INPUT
# % key: mfd
# % label: Minimum Flow Discharge (MFD) [m3/s]
# % required: no
# % guisection: Legal Discharge
# %end
# %option G_OPT_R_INPUT
# % key: discharge_natural
# % label: Natural discharge [m3/s]
# % required: no
# % guisection: Legal Discharge
# %end
# %option
# % key: percentage
# % type: double
# % key_desc: double
# % description: MFD as percentage of natural discharge [%]
# % options: 0-100
# % required: no
# % guisection: Legal Discharge
# %end

##
## OPTIONAL INPUTS: AREAS TO EXCLUDE
##
# %option G_OPT_V_INPUT
# % key: area
# % label: Areas to exclude
# % description: Vector map with the areas that must be excluded (e.g. Parks)
# % required: no
# % guisection: Areas to exclude
# %end
# %option
# % key: buff
# % type: double
# % key_desc: double
# % description: Buffer for areas to exclude [m]
# % required: no
# % answer: 0
# % guisection: Areas to exclude
# %end
# %option G_OPT_V_INPUT
# % key: points_view
# % label: Vector points of viewing position to exclude
# % description: Vector with the points that are used to compute the visibility
# % required: no
# % guisection: Areas to exclude
# %end
# %option
# % key: visibility_resolution
# % type: double
# % description: Resolution of the visibility map computation
# % required: no
# % guisection: Areas to exclude
# %end
# %option
# % key: n_points
# % type: integer
# % description: Number of points for the visibility
# % required: no
# % guisection: Areas to exclude
# %end

##
## OUTPUTS
##
# %option G_OPT_V_OUTPUT
# % key: output_plant
# % description: Name of output vector with potential segments
# % required: yes
# %end
# %option G_OPT_V_OUTPUT
# % key: output_vis
# % description: Name of output vector with viewed areas
# % required: no
# % guisection: Areas to exclude
# %end

##
## FLAGS
##
# %flag
# % key: d
# % description: Debug with intermediate maps
# %end
# %flag
# % key: c
# % description: Clean vector lines
# %end

# %rules
# %exclusive: mfd, discharge_natural
# %exclusive: mfd, percentage
# %requires: discharge_natural, percentage
# %end

# import system libraries
from __future__ import print_function

import atexit
import os
import sys

from grass.pygrass.messages import get_msgr
from grass.pygrass.vector import VectorTopo
from grass.script import core as gcore

# import grass libraries
from grass.script import mapcalc
from grass.script.utils import set_path

try:
    # set python path to the shared r.green libraries
    set_path("r.green", "libhydro", "..")
    set_path("r.green", "libgreen", os.path.join("..", ".."))
    from libgreen.utils import cleanup
    from libhydro.plant import power2energy
except ImportError:
    try:
        set_path("r.green", "libhydro", os.path.join("..", "etc", "r.green"))
        set_path("r.green", "libgreen", os.path.join("..", "etc", "r.green"))
        from libgreen.utils import cleanup
        from libhydro.plant import power2energy
    except ImportError:
        gcore.warning("libgreen and libhydro not in the python path!")


if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def set_new_region(new_region):
    gcore.run_command("g.region", res=new_region)
    return


def set_old_region(info):
    gcore.run_command(
        "g.region",
        rows=info["rows"],
        e=info["e"],
        cols=info["cols"],
        n=info["n"],
        s=info["s"],
        w=info["w"],
        ewres=info["ewres"],
        nsres=info["nsres"],
    )
    return


def main(opts, flgs):
    TMPRAST, TMPVECT, DEBUG = [], [], flgs["d"]
    atexit.register(cleanup, raster=TMPRAST, vector=TMPVECT, debug=DEBUG)
    OVW = gcore.overwrite()

    dtm = options["elevation"]
    river = options["river"]  # raster
    discharge_current = options["discharge_current"]  # vec
    discharge_natural = options["discharge_natural"]  # vec
    mfd = options["mfd"]
    len_plant = options["len_plant"]
    len_min = options["len_min"]
    distance = options["distance"]
    output_plant = options["output_plant"]
    area = options["area"]
    buff = options["buff"]
    efficiency = options["efficiency"]
    DEBUG = flags["d"]
    points_view = options["points_view"]
    new_region = options["visibility_resolution"]
    final_vis = options["output_vis"]
    n_points = options["n_points"]
    p_min = options["p_min"]
    percentage = options["percentage"]
    msgr = get_msgr()

    # set the region
    info = gcore.parse_command("g.region", flags="m")
    if (info["nsres"] == 0) or (info["ewres"] == 0):
        msgr.warning("set region to elevation raster")
        gcore.run_command("g.region", raster=dtm)

    pid = os.getpid()

    if area:
        if float(buff):
            area_tmp = "tmp_buff_area_%05d" % pid
            gcore.run_command(
                "v.buffer", input=area, output=area_tmp, distance=buff, overwrite=OVW
            )
            area = area_tmp
            TMPVECT.append(area)
        oriver = "tmp_river_%05d" % pid
        gcore.run_command(
            "v.overlay",
            flags="t",
            ainput=river,
            binput=area,
            operator="not",
            output=oriver,
            overwrite=OVW,
        )
        river = oriver
        TMPVECT.append(oriver)

    if points_view:
        info_old = gcore.parse_command("g.region", flags="pg")
        set_new_region(new_region)
        pl, mset = points_view.split("@") if "@" in points_view else (points_view, "")
        vec = VectorTopo(pl, mapset=mset, mode="r")
        vec.open("r")
        string = "0"
        for i, point in enumerate(vec):
            out = "tmp_visual_%05d_%03d" % (pid, i)
            gcore.run_command(
                "r.viewshed",
                input=dtm,
                output=out,
                coordinates=point.coords(),
                overwrite=OVW,
                memory=1000,
                flags="b",
                max_distance=4000,
            )
            TMPRAST.append(out)
            # we use 4 km sice it the human limit
            string = string + ("+%s" % out)
        # import pdb; pdb.set_trace()

        tmp_final_vis = "tmp_final_vis_%05d" % pid
        formula = "%s = %s" % (tmp_final_vis, string)
        TMPRAST.append(tmp_final_vis)
        mapcalc(formula, overwrite=OVW)
        # change to old region
        set_old_region(info_old)
        TMPVECT.append(tmp_final_vis)
        gcore.run_command(
            "r.to.vect",
            flags="v",
            overwrite=OVW,
            input=tmp_final_vis,
            output=tmp_final_vis,
            type="area",
        )
        if int(n_points) > 0:
            where = "cat<%s" % (n_points)
        else:
            where = "cat=0"
        gcore.run_command(
            "v.db.droprow",
            input=tmp_final_vis,
            where=where,
            output=final_vis,
            overwrite=OVW,
        )
        tmp_river = "tmp_river2_%05d" % pid
        gcore.run_command(
            "v.overlay",
            flags="t",
            ainput=river,
            binput=final_vis,
            operator="not",
            output=tmp_river,
            overwrite=OVW,
        )
        river = tmp_river
        TMPVECT.append(tmp_river)

        # import pdb; pdb.set_trace()

    tmp_disch = "tmp_discharge_%05d" % pid
    if mfd:
        formula = "%s=%s-%s" % (tmp_disch, discharge_current, mfd)
        mapcalc(formula, overwrite=OVW)
        TMPRAST.append(tmp_disch)
        discharge_current = tmp_disch

    elif discharge_natural:
        formula = "%s=%s-%s*%s/100.0" % (
            tmp_disch,
            discharge_current,
            discharge_natural,
            percentage,
        )
        mapcalc(formula, overwrite=OVW)
        formula = "%s=if(%s>0, %s, 0)" % (tmp_disch, tmp_disch, tmp_disch)
        mapcalc(formula, overwrite=True)
        TMPRAST.append(tmp_disch)
        discharge_current = tmp_disch

    gcore.run_command(
        "r.green.hydro.optimal",
        flags="c",
        discharge=discharge_current,
        river=river,
        elevation=dtm,
        len_plant=len_plant,
        output_plant=output_plant,
        distance=distance,
        len_min=len_min,
        efficiency=efficiency,
        p_min=p_min,
    )
    power2energy(output_plant, "pot_power", float(options["n"]))
    print("r.green.hydro.recommended completed!")


if __name__ == "__main__":
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
