#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.biomassfor.recommended
# AUTHOR(S):   Francesco Geri, Sandro Sacchelli
#              Converted to Python by Francesco Geri reviewed by Marco Ciolli
# PURPOSE:     Calculates the potential bioenergy contained in a forest accortding to several constraints
# COPYRIGHT:   (C) 2013 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
# %Module
# % description: Estimates potential bioenergy according to environmental restriction
# % keyword: raster
# % keyword: biomass
# %End
# %option G_OPT_R_INPUT
# % key: hfmap
# % description: Bioenergy potential map for High Forest in MWh/m3
# %end
# %option G_OPT_R_INPUT
# % key: cmap
# % type: string
# % description: Bioenergy potential map for Coppice in MWh/m3
# % required : yes
# %end
# %option
# % key: output_basename
# % type: string
# % description: Basename for final recommended maps of bioenergy (HF,CC and total)
# % gisprompt: new
# % key_desc : name
# % required : yes
# %end
# %option G_OPT_R_INPUT
# % key: management
# % type: string
# % description: Map of forest management (1: high forest, 2:coppice)
# % required : yes
# %end
# %option G_OPT_R_INPUT
# % key: treatment
# % type: string
# % description: Map of forest treatment (1: final felling, 2:thinning)
# % required : yes
# %end
# %option G_OPT_R_INPUTS
# % key: restrictions
# % type: string
# % description: Area with absolute restrictions (protected areas, urban parks etc.)
# % required : no
# % guisection: Restrictions
# %end
# %option G_OPT_R_INPUT
# % key: hydro
# % type: string
# % description: Rivers network
# % required : no
# % guisection: Restrictions
# %end
# %option
# % key: buffer_hydro
# % type: integer
# % description: Buffer area for rivers
# % answer: 0
# % required : no
# % guisection: Restrictions
# %end
# %option G_OPT_R_INPUT
# % key: zone_less
# % type: string
# % description: Civic use
# % required : no
# % guisection: Restrictions
# %end
# %option
# % key: energy_tops_hf
# % type: double
# % description: Energy for tops and branches in high forest in MWh/m3
# % answer: 0.49
# % guisection: Energy
# %end
# %option
# % key: energy_cormometric_vol_hf
# % type: double
# % description: Energy for tops and branches for high forest in MWh/m3
# % answer: 1.97
# % guisection: Energy
# %end
# %option
# % key: energy_tops_cop
# % type: double
# % description: Energy for tops and branches for Coppices in MWh/m3
# % answer: 0.55
# % guisection: Energy
# %end

import pdb
import string

import numpy as np

from grass.pygrass.raster import RasterRow
from grass.script.core import overwrite, parser, run_command

# check_var checks the presence/absence of the input maps
check_var = 0


def main(opts, flgs):
    ow = overwrite()

    output = opts["output_prefix"]
    management = opts["management"]
    treatment = opts["treatment"]

    # ouput variables
    rec_bioenergyHF = output + "_rec_bioenergyHF"
    rec_bioenergyC = output + "_rec_bioenergyC"
    rec_bioenergy = output + "_rec_bioenergy"

    # input variables
    pot_HF = opts["hfmap"]
    pot_C = opts["cmap"]

    rivers = opts["hydro"]

    buffer_hydro = int(opts["buffer_hydro"])

    zone_less = opts["zone_less"]

    check_var = 0

    # pdb.set_trace()

    # check if the raster of rivers is present with a buffer inserted
    if buffer_hydro > 0 and rivers == "":
        print(
            "if the river buffer is greater than zero, the raster map of rivers is required"
        )
        return

    # recovery of the series of raster constraint maps
    restr_map = opts["restrictions"].split(",")

    # start the query string
    expr_map = "constraint="

    # check if at least 1 constraint map is inserted
    if opts["restrictions"] != "":
        check_var = 1
        count_map = 0

        # cycle with composition of the query string with all the constraint maps
        for mapr_ in restr_map:
            mapr1 = string.split(mapr_, "@")
            mapr = mapr1[0]

            if count_map == 0:
                expr_map += "(" + mapr
                convert_bool = mapr + "=" + mapr + ">0"
                run_command("r.mapcalc", overwrite=1, expression=convert_bool)
                run_command("r.null", map=mapr, null=0)
            else:
                expr_map += "||" + mapr
                convert_bool = mapr + "=" + mapr + ">0"
                run_command("r.mapcalc", overwrite=1, expression=convert_bool)
                run_command("r.null", map=mapr, null=0)
            count_map += 1
        expr_map += ")"

    # if the river buffer is inserted add calculate the buffer and
    # add the buffer to the constraint map
    if buffer_hydro > 0:
        run_command("r.null", map=rivers, null=0)
        run_command(
            "r.buffer",
            overwrite=ow,
            input=rivers,
            output="rivers_buffer",
            distances=buffer_hydro,
            flags="z",
        )
        run_command("r.null", map="rivers_buffer", null=0)
        if check_var == 1:
            expr_map += "|| (rivers || rivers_buffer)"
        else:
            expr_map += "rivers || rivers_buffer"
        check_var = 1

    if zone_less != "":
        check_var = 1

    if check_var == 0:
        print("Error: At least one constraint map must be inserted")
        return
    else:
        # if at least one contraint is inserted process the potential map
        run_command(
            "r.mapcalc", overwrite=ow, expression=rec_bioenergyHF + "=" + pot_HF
        )
        run_command("r.mapcalc", overwrite=ow, expression=rec_bioenergyC + "=" + pot_C)

        run_command("r.mapcalc", overwrite=ow, expression=expr_map)
        run_command("r.mapcalc", overwrite=ow, expression="constraint=constraint<1")
        run_command("r.null", map="constraint", null=0)

        constr_HF = rec_bioenergyHF + "=" + rec_bioenergyHF + "*constraint"
        constr_C = rec_bioenergyC + "=" + rec_bioenergyC + "*constraint"

        run_command("r.mapcalc", overwrite=ow, expression=constr_HF)
        run_command("r.mapcalc", overwrite=ow, expression=constr_C)

    if zone_less != "":
        run_command(
            "r.mapcalc",
            overwrite=ow,
            expression="wood_pix=(" + zone_less + "/((ewres()*nsres())*10000))",
        )
        WHF = (
            "wood_energyHF= if("
            + management
            + "==1 && "
            + treatment
            + "==1 || "
            + management
            + " == 1 && "
            + treatment
            + "==99999, wood_pix*%f, if("
            + management
            + "==1 && "
            + treatment
            + "==2, wood_pix*%f + wood_pix*%f))"
        )
        WCC = (
            "wood_energyC = if("
            + management
            + "==2, wood_pix*"
            + opts["energy_tops_cop"]
            + ")"
        )
        run_command(
            "r.mapcalc",
            overwrite=ow,
            expression=WHF
            % tuple(
                map(
                    float,
                    (
                        opts["energy_tops_hf"],
                        opts["energy_tops_hf"],
                        opts["energy_cormometric_vol_hf"],
                    ),
                )
            ),
        )
        run_command("r.mapcalc", overwrite=ow, expression=WCC)

        run_command("r.null", map="wood_energyHF", null=0)
        run_command("r.null", map="wood_energyC", null=0)

        limit_HF = rec_bioenergyHF + "=" + rec_bioenergyHF + "-wood_energyHF"
        limit_C = rec_bioenergyC + "=" + rec_bioenergyC + "-wood_energyC"

        run_command("r.mapcalc", overwrite=ow, expression=limit_HF)
        run_command("r.mapcalc", overwrite=ow, expression=limit_C)

    RECOT = rec_bioenergy + " = (" + rec_bioenergyHF + " + " + rec_bioenergyC + ")"

    run_command("r.mapcalc", overwrite=ow, expression=RECOT)

    with RasterRow(rec_bioenergy) as pT:
        T = np.array(pT)

    print(
        "Resulted maps: "
        + output
        + "_rec_bioenergyHF, "
        + output
        + "_rec_bioenergyC, "
        + output
        + "_rec_bioenergy"
    )
    print("Total bioenergy stimated (Mwh): %.2f" % np.nansum(T))

    # print "Resulted maps: "+output+"_rec_bioenergyHF, "+output+"_rec_bioenergyC, "+output+"_rec_bioenergy"


if __name__ == "__main__":
    main(*parser())
