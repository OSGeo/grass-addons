#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.discharge
# AUTHOR(S):   Giulia Garegnani
# PURPOSE:     ?
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

# %module
# % description: Calculate average natural discharge and minimum flow following regional law an
# % keyword: raster
# % keyword: hydropower
# % keyword: renewable energy
# % overwrite: yes
# %end
# %option G_OPT_R_INPUT
# % key: q_spec
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of the specific discharge [l/s/km2]
# % required: no
# %end
# %option G_OPT_R_OUTPUT
# % key: q_river
# % type: string
# % key_desc: name
# % description: Name of raster map with the discharge along river [m3/s]
# % required: yes
# %end
# %option G_OPT_R_INPUT
# % key: k_b
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of raster map with kb parameter
# % required: no
# % guisection: Regione Veneto
# %end
# %option G_OPT_R_INPUT
# % key: k_n
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of raster map with kn parameter
# % required: no
# % guisection: Regione Veneto
# %end
# %option
# % key: rain
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of the specific with rain [mm]
# % required: no
# %end
# %option
# % key: k_matrix
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of k area map with k parameter
# % required: no
# % guisection: Regione Piemonte
# %end
# %option
# % key: m_matrix
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of M area map with M parameter
# % required: no
# % guisection: Regione Piemonte
# %end
# %option
# % key: a_matrix
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of A area map with A parameter
# % required: no
# % guisection: Regione Piemonte
# %end

# %option G_OPT_R_OUTPUT
# % key: mfd
# % type: string
# % key_desc: name
# % description: Name of raster map with minimum flow along the river [m3/s]
# % required: no
# %end
# %option G_OPT_R_OUTPUT
# % key: a_river
# % type: string
# % key_desc: name
# % description: Name of raster map with area of the basin along the river [m2]
# % required: no
# %end
# %flag
# % key: d
# % description: Debug with intermediate maps
# %end
# %flag
# % key: f
# % description: compute the discharge in the river with q_spec=flow map
# %end
# %flag
# % key: p
# % description: compute the discharge in the river with q_spec computed as see manual
# %end
# %option G_OPT_R_ELEV
# %  required: yes
# %end
# %option G_OPT_V_INPUT
# % key: river
# % label: Name of river network
# % required: no
# %end
# %option G_OPT_V_INPUT
# % key: lakes
# % label: Name of lakes network
# % required: no
# %end
# %option G_OPT_V_OUTPUT
# % key: streams
# % type: string
# % key_desc: name
# % description: Name of the new stream network
# % required: yes
# %end
# %option
# % key: corr_fact
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of corrective factors area map for environmental flow
# TODO: list of maps
# % required: no
# %end
# %option
# % key: env_area
# % type: string
# % gisprompt: old,cell,raster
# % key_desc: name
# % description: Name of area with environmental restriction
# % required: no
# %end
# %option
# % key: threshold
# % type: double
# % description: Minimum size of exterior watershed basin
# % required: yes
# % answer: 100000
# %END

import atexit

# import system libraries
import os
import sys

from grass.pygrass.messages import get_msgr
from grass.script import core as gcore

# import grass libraries
from grass.script import mapcalc
from grass.script.utils import set_path

# import pdb


try:
    # set python path to the shared r.green libraries
    set_path("r.green", "libhydro", "..")
    set_path("r.green", "libgreen", os.path.join("..", ".."))
    from libgreen.utils import cleanup
    from libhydro.basin import dtm_corr
except ImportError:
    try:
        set_path("r.green", "libhydro", os.path.join("..", "etc", "r.green"))
        set_path("r.green", "libgreen", os.path.join("..", "etc", "r.green"))
        from libgreen.utils import cleanup
        from libhydro.basin import dtm_corr
    except ImportError:
        gcore.warning("libgreen and libhydro not in the python path!")


if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def compute_a(threshold, dtm, stream, a_river, acc):
    """Compute the area of the basin for each pixel of stream
    the accumulation map and the new streams
    """
    pid = os.getpid()
    info = gcore.parse_command("g.region", flags="pgm")
    area_px = float(info["nsres"]) * float(info["ewres"])
    tmp_stream = "tmprgreen_%i_stream" % pid
    tmp_tmp_stream = "tmprgreen_%i_tmpstream" % pid
    gcore.run_command(
        "r.watershed",
        elevation=dtm,
        threshold=threshold,
        accumulation=acc,
        stream=tmp_stream,
        memory=3000,
    )
    gcore.run_command("r.thin", input=tmp_stream, output=tmp_tmp_stream)
    gcore.run_command(
        "r.to.vect",
        flags="v",
        overwrite=True,
        input=tmp_tmp_stream,
        output=stream,
        type="line",
    )

    command = "%s = abs(%s)/1000000.0 * %f" % (a_river, acc, area_px)
    mapcalc(command, overwrite=True)


def compute_q(threshold, q_spec, q_river, dtm):
    """Compute the discharge along the river given the specific discharge"""
    pid = os.getpid()
    info = gcore.parse_command("g.region", flags="pgm")
    area_px = float(info["nsres"]) * float(info["ewres"])
    q_cum = "tmprgreen_%i_q_cum" % pid
    gcore.run_command(
        "r.watershed",
        elevation=dtm,
        flow=q_spec,
        threshold=threshold,
        accumulation=q_cum,
        memory=3000,
    )
    command = "%s=abs(%s/1000.0* %f/1000000.0)" % (q_river, q_cum, area_px)
    mapcalc(command)


def regione_veneto(q_spec, a_river, k_b, k_n, min_flow):
    # minimum flow m3/s
    command = "%s=(%s+%s)*177.0*exp(%s,0.85)*%s*exp(10.0,-6)" % (
        min_flow,
        k_b,
        k_n,
        a_river,
        q_spec,
    )
    mapcalc(command, overwrite=True)


def main(options, flags):
    pid = os.getpid()
    pat = "tmprgreen_%i_*" % pid
    DEBUG = False
    atexit.register(cleanup, pattern=pat, debug=DEBUG)
    rain = options["rain"]
    q_spec = options["q_spec"]
    a_river = options["a_river"]
    q_river = options["q_river"]
    dtm = options["elevation"]
    river = options["river"]
    lakes = options["lakes"]
    threshold = options["threshold"]
    DEBUG = flags["d"]
    rf = flags["f"]  # ra flow map
    rp = flags["p"]  # rain map, piedmont formula
    k_mat = options["k_matrix"]  # raster
    m_mat = options["m_matrix"]  # raster
    a_mat = options["a_matrix"]
    new_stream = options["streams"]
    env_area = options["env_area"]
    corr_fact = options["corr_fact"]

    if not a_river:
        a_river = "tmprgreen_%i_a_river" % pid
    msgr = get_msgr()

    msgr.warning("set region to elevation raster")
    gcore.run_command("g.region", raster=dtm)

    # compute temporary DTM
    if river:
        tmp_dtm_corr = "tmprgreen_%i_dtm_corr" % pid
        dtm_corr(dtm, river, tmp_dtm_corr, lakes)
        dtm_old = dtm
        dtm = tmp_dtm_corr
    # compute the area for each cell
    tmp_acc = "tmprgreen_%i_acc" % pid
    compute_a(threshold, dtm, new_stream, a_river, tmp_acc)
    # compute q_river
    if rf:
        compute_q(threshold, q_spec, q_river, dtm)
        q_spec = "tmpgreen_%i_q_spec" % pid
        command = "%s=if(%s,%s/%s)" % (q_spec, a_river, q_river, a_river)
        mapcalc(command, overwrite=True)
    elif rp:
        if not (q_spec):
            # compute the mean elevation of the basin
            h_cum = "tmprgreen_%i_h_cum" % pid
            h_mean = "tmprgreen_%i_h_mean" % pid
            gcore.run_command(
                "r.watershed",
                elevation=dtm,
                flow=dtm_old,
                threshold=threshold,
                accumulation=h_cum,
                memory=3000,
            )
            command = "%s = %s/%s" % (h_mean, h_cum, tmp_acc)
            mapcalc(command)
            # TODO: compute the mean rain
            command = "q_spec =0.0086*%s+0.03416*%s-24.5694" % (rain, h_mean)
            q_spec = "q_spec"
            mapcalc(command)
            command = "%s = %s * %s/1000.0" % (q_river, q_spec, a_river)
            mapcalc(command)
    # compute MVF with Regione Veneto Formula
    min_flow = options["mfd"]
    if options["k_b"]:
        msgr.warning("Regione Veneto plan")
        k_b = options["k_b"]  # raster
        k_n = options["k_n"]  # raster
        regione_veneto(a_river, q_spec, k_b, k_n, min_flow)
    elif k_mat:
        msgr.warning("Piedmont Plan")
        command = "%s=%s*%s*%s*%s*%s/1000.0" % (
            min_flow,
            k_mat,
            a_river,
            q_spec,
            m_mat,
            a_mat,
        )
        mapcalc(command, overwrite=True)
    else:
        msgr.warning("No formula for the MVF")
    if corr_fact:
        # if corr_fact coumpute the environemtal flow else the minimum flow"
        command = "%s=if(not(%s), %s, %s*%s)" % (
            env_area,
            min_flow,
            corr_fact * min_flow,
        )


if __name__ == "__main__":
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
