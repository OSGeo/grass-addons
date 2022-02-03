#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.biomassfor.legal
# AUTHOR(S):   Sandro Sacchelli, Francesco Geri
#              Converted to Python by Pietro Zambelli and Francesco Geri, reviewed by Marco Ciolli
# PURPOSE:     Calculates the potential Ecological Bioenergy contained in a forest
# COPYRIGHT:   (C) 2013 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
# %Module
# % description: Estimates potential bioenergy depending on forest increment, forest management and forest treatment
# % keyword: raster
# % keyword: biomass
# % overwrite: yes
# %End
# %option G_OPT_V_INPUT
# % key: forest
# % type: string
# % description: Name of vector parcel map
# % label: Name of vector parcel map
# % guisection: Base
# %end
# %option G_OPT_V_INPUT
# % key: boundaries
# % type: string
# % description: Name of vector boundaries map (boolean map)
# % label: Name of vector boundaries map (boolean map)
# % guisection: Base
# %end
# %option
# % key: energy_tops_hf
# % type: double
# % description: Energy for tops and branches in high forest in MWh/m3
# % answer: 0.49
# % guisection: Energy
# %end
# %option
# % key: forest_column_yield
# % type: string
# % answer: yield
# % description: Vector field of yield
# % guisection: Base
# %end
# %option
# % key: forest_column_yield_surface
# % type: string
# % answer: yield_surface
# % description: Vector field of stand surface (ha)
# % guisection: Base
# %end
# %option
# % key: forest_column_management
# % type: string
# % answer: management
# % description: Vector field of forest management (1: high forest, 2:coppice)
# % guisection: Base
# %end
# %option
# % key: forest_column_treatment
# % answer: treatment
# % type: string
# % description: Vector field of forest treatment (1: final felling, 2:thinning)
# % guisection: Base
# %end
# %option
# % key: output_basename
# % answer: biomassfor
# % type: string
# % gisprompt: new
# % description: Basename for potential bioenergy (HF,CC and total)
# % key_desc : name
# % guisection: Base
# %end
# %option
# % key: energy_cormometric_vol_hf
# % type: double
# % description: Energy for the whole tree in high forest (tops, branches and stem) in MWh/m3
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

import numpy as np

from grass.pygrass.raster import RasterRow
from grass.script.core import overwrite, parser, run_command


def main(opts, flgs):
    ow = overwrite()

    output = opts["output_basename"]

    forest = opts["forest"]
    boundaries = opts["boundaries"]
    yield_ = opts["forest_column_yield"]
    management = opts["forest_column_management"]
    treatment = opts["forest_column_treatment"]
    yield_surface = opts["forest_column_yield_surface"]

    l_bioenergyHF = output + "_l_bioenergyHF"
    l_bioenergyC = output + "_l_bioenergyC"
    l_bioenergy = output + "_l_bioenergy"

    ######## start import and convert ########

    run_command("g.region", vect=boundaries)
    run_command(
        "v.to.rast",
        input=forest,
        output="yield",
        use="attr",
        attrcolumn=yield_,
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="yield_surface",
        use="attr",
        attrcolumn=yield_surface,
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="treatment",
        use="attr",
        attrcolumn=treatment,
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="management",
        use="attr",
        attrcolumn=management,
        overwrite=True,
    )

    run_command("r.null", map="yield", null=0)
    run_command("r.null", map="yield_surface", null=0)
    run_command("r.null", map="treatment", null=0)
    run_command("r.null", map="management", null=0)

    ######## end import and convert ########

    ######## temp patch to link map and fields ######

    management = "management"
    treatment = "treatment"
    yield_surface = "yield_surface"
    yield_ = "yield"

    ######## end temp patch to link map and fields ######

    # import pdb; pdb.set_trace()
    # treatment=1 final felling, treatment=2 thinning
    ECOHF = (
        l_bioenergyHF
        + " = if("
        + management
        + "==1 && "
        + treatment
        + "==1 || "
        + management
        + " == 1 && "
        + treatment
        + "==99999, yield_pix1*%f, if("
        + management
        + "==1 && "
        + treatment
        + "==2, yield_pix1*%f + yield_pix1*%f))"
    )

    # ECOHF = 'ecological_bioenergyHF = if(management==1 && treatment==1 || management == 1 && treatment==99999,yield_pix1*'+opts['energy_tops_hf']+', if(management==1 && treatment==2, yield_pix1*'+opts['energy_tops_hf']+' + yield_pix1*'+opts['energy_cormometric_vol_hf']+'))'

    ECOCC = (
        l_bioenergyC
        + " = if("
        + management
        + "==2, yield_pix1*"
        + opts["energy_tops_cop"]
        + ")"
    )

    ECOT = l_bioenergy + " = (" + l_bioenergyHF + " + " + l_bioenergyC + ")"

    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression="yield_pix1 = ("
        + yield_
        + "/"
        + yield_surface
        + ")*((ewres()*nsres())/10000)",
    )

    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression=ECOHF
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

    run_command("r.mapcalc", overwrite=ow, expression=ECOCC)

    run_command("r.mapcalc", overwrite=ow, expression=ECOT)

    with RasterRow(l_bioenergy) as pT:
        T = np.array(pT)

    print(
        "Resulted maps: "
        + output
        + "_l_bioenergyHF, "
        + output
        + "_l_bioenergyC, "
        + output
        + "_l_bioenergy"
    )
    print("Total bioenergy stimated (Mwh): %.2f" % np.nansum(T))


if __name__ == "__main__":
    main(*parser())
