#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.biomassfor.technical
# AUTHOR(S):   Sandro Sacchelli, Francesco Geri
#              Converted to Python by Pietro Zambelli, reviewed by Marco Ciolli
# PURPOSE:     Calculates the technical potential taking into account morphology and operative technical limits
# COPYRIGHT:   (C) 2013 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
# %Module
# % description: Estimates the quantity of woody biomass obtained from a forest surface where extraction is possible given a particular level of mechanisation
# % keyword: raster
# % keyword: biomass
# % overwrite: yes
# %End
# %option G_OPT_R_INPUT
# % key: dtm
# % type: string
# % description: Name of Digital terrain model map
# % required : yes
# %end
# %option G_OPT_V_INPUT
# % key: forest
# % type: string
# % description: Name of vector parcel map
# % label: Name of vector parcel map
# % required : yes
# %end
# %option G_OPT_V_INPUT
# % key: boundaries
# % type: string
# % description: Name of vector boundaries map (boolean map)
# % label: Name of vector boundaries map (boolean map)
# % required : yes
# %end
# %option
# % key: forest_column_yield
# % type: string
# % description: Vector field of yield
# % required : yes
# %end
# %option
# % key: forest_column_yield_surface
# % type: string
# % description: Vector field of stand surface (ha)
# % required : yes
# %end
# %option
# % key: forest_column_management
# % type: string
# % description: Vector field of forest management (1: high forest, 2:coppice)
# % required : yes
# %end
# %option
# % key: forest_column_treatment
# % type: string
# % description: Vector field of forest treatment (1: final felling, 2:thinning)
# % required : yes
# %end
# %option G_OPT_V_INPUT
# % key: forest_roads
# % type: string
# % description: Vector map of forest roads
# % label: Vector map of forest roads
# % required : yes
# %end
# %option
# % key: output_basename
# % type: string
# % description: Basename for technical bioenergy (HF,CC and total)
# % gisprompt: new
# % key_desc : name
# % required : yes
# %end
# %option
# % key: forest_column_roughness
# % type: string
# % description: Vector field of roughness
# % required : no
# % guisection: Opt files
# %end
# %option G_OPT_V_INPUT
# % key: rivers
# % type: string
# % description: Vector map of rivers
# % label: Vector map of rivers
# % required : no
# % guisection: Opt files
# %end
# %option G_OPT_V_INPUT
# % key: lakes
# % type: string
# % description: Vector map of lakes
# % label: Vector map of lakes
# % required : no
# % guisection: Opt files
# %end
# %option
# % key: slp_min_cc
# % type: double
# % description: Percent slope lower limit with Cable Crane
# % answer: 30.
# % guisection: Cable Crane
# %end
# %option
# % key: slp_max_cc
# % type: double
# % description: Percent slope higher limit with Cable Crane
# % answer: 100.
# % required : no
# % guisection: Cable Crane
# %end
# %option
# % key: dist_max_cc
# % type: double
# % description: Maximum distance with Cable Crane
# % answer: 800.
# % required : no
# % guisection: Cable Crane
# %end
# %option
# % key: slp_max_fw
# % type: double
# % description: Percent slope higher limit with Forwarder
# % answer: 30.
# % required : no
# % guisection: Forwarder
# %end
# %option
# % key: dist_max_fw
# % type: double
# % description: Maximum distance with Forwarder
# % answer: 600.
# % required : no
# % guisection: Forwarder
# %end
# %option
# % key: slp_max_cop
# % type: double
# % description: Percent slope higher limit with other techniques for Coppices
# % answer: 30.
# % required : no
# % guisection: Other
# %end
# %option
# % key: dist_max_cop
# % type: double
# % description: Maximum distance with other techniques for Coppices
# % answer: 600.
# % required : no
# % guisection: Other
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
# %flag
# % key: r
# % description: Remove all operational maps
# %end


import numpy as np

import grass.script as grass
from grass.pygrass.raster import RasterRow
from grass.script.core import overwrite, parse_command, parser, run_command

YPIX = "yield_pix = yield_pix1*%d + yield_pix2*%d"


def remove_map(opts, flgs):

    run_command("g.remove", type="raster", flags="f", name="cable_crane_extraction")
    run_command("g.remove", type="raster", flags="f", name="forwarder_extraction")
    run_command("g.remove", type="raster", flags="f", name="other_extraction")
    run_command("g.remove", type="raster", flags="f", name="technical_surface")
    run_command("g.remove", type="raster", flags="f", name="frict_surf_extr")
    run_command("g.remove", type="raster", flags="f", name="extr_dist")
    run_command("g.remove", type="raster", flags="f", name="yield_pix")
    run_command("g.remove", type="raster", flags="f", name="yield_pix1")
    run_command("g.remove", type="raster", flags="f", name="yield_pix2")
    run_command("g.remove", type="raster", flags="f", name="pix_cross")
    run_command("g.remove", type="raster", flags="f", name="slope_deg")
    run_command("g.remove", type="raster", flags="f", name="slope")


def main(opts, flgs):
    ow = overwrite()

    output = opts["output_basename"]

    forest = opts["forest"]
    boundaries = opts["boundaries"]
    yield_ = opts["forest_column_yield"]
    management = opts["forest_column_management"]
    treatment = opts["forest_column_treatment"]
    yield_surface = opts["forest_column_yield_surface"]
    roughness = opts["forest_column_roughness"]
    forest_roads = opts["forest_roads"]

    rivers = opts["rivers"]
    lakes = opts["lakes"]

    vector_forest = opts["forest"]

    tech_bioenergyHF = output + "_tech_bioenergyHF"
    tech_bioenergyC = output + "_tech_bioenergyC"
    tech_bioenergy = output + "_tech_bioenergy"

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

    run_command(
        "v.to.rast",
        input=forest_roads,
        output="forest_roads",
        use="val",
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
    forest_roads = "forest_roads"

    ######## end temp patch to link map and fields ######

    if roughness == "":
        run_command("r.mapcalc", overwrite=ow, expression="roughness=0")
        roughness = "roughness"
    else:
        run_command(
            "v.to.rast",
            input=forest,
            output="roughness",
            use="attr",
            attrcolumn=roughness,
            overwrite=True,
        )
        run_command("r.null", map="roughness", null=0)

    CCEXTR = (
        "cable_crane_extraction = if("
        + yield_
        + ">0 && slope>"
        + opts["slp_min_cc"]
        + " && slope<="
        + opts["slp_max_cc"]
        + " && extr_dist<"
        + opts["dist_max_cc"]
        + ", 1)"
    )

    FWEXTR = (
        "forwarder_extraction = if("
        + yield_
        + ">0 && slope<="
        + opts["slp_max_fw"]
        + " && "
        + management
        + "==1 && ("
        + roughness
        + "==0 || "
        + roughness
        + "==1 || "
        + roughness
        + "==99999) && extr_dist<"
        + opts["dist_max_fw"]
        + ", 1)"
    )

    OEXTR = (
        "other_extraction = if("
        + yield_
        + ">0 && slope<="
        + opts["slp_max_cop"]
        + " && "
        + management
        + "==2 && ("
        + roughness
        + "==0 || "
        + roughness
        + "==1 || "
        + roughness
        + "==99999) && extr_dist<"
        + opts["dist_max_cop"]
        + ", 1)"
    )

    EHF = (
        tech_bioenergyHF
        + " = technical_surface*(if("
        + management
        + "==1 && "
        + treatment
        + "==1 || "
        + management
        + "==1 && "
        + treatment
        + "==99999, yield_pix*"
        + opts["energy_tops_hf"]
        + ", if("
        + management
        + "==1 && "
        + treatment
        + "==2, yield_pix *"
        + opts["energy_tops_hf"]
        + " + yield_pix * "
        + opts["energy_cormometric_vol_hf"]
        + ")))"
    )

    ECC = (
        tech_bioenergyC
        + " = technical_surface*(if("
        + management
        + " == 2, yield_pix*"
        + opts["energy_tops_cop"]
        + "))"
    )

    ET = tech_bioenergy + " = (" + tech_bioenergyC + " + " + tech_bioenergyHF + ")"

    run_command(
        "r.param.scale",
        overwrite=ow,
        input=opts["dtm"],
        output="morphometric_features",
        size=3,
        method="feature",
    )
    run_command(
        "r.slope.aspect", overwrite=ow, elevation=opts["dtm"], slope="slope_deg"
    )
    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression="pix_cross = ((ewres()+nsres())/2)/ cos(slope_deg)",
    )
    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression="yield_pix1 = ("
        + yield_
        + "/"
        + yield_surface
        + ")*((ewres()*nsres())/10000)",
    )
    run_command("r.null", map="yield_pix1", null=0)
    run_command("r.null", map="morphometric_features", null=0)

    exprmap = "frict_surf_extr = pix_cross + if(yield_pix1<=0, 99999) + if(morphometric_features==6, 99999)"

    if rivers != "":
        run_command(
            "v.to.rast", input=rivers, output="rivers", use="val", overwrite=True
        )
        run_command("r.null", map="rivers", null=0)
        rivers = "rivers"
        exprmap += "+ if(" + rivers + ">=1, 99999)"

    if lakes != "":
        run_command("v.to.rast", input=lakes, output="lakes", use="val", overwrite=True)
        run_command("r.null", map="lakes", null=0)
        lakes = "lakes"
        exprmap += "+ if(" + lakes + ">=1, 99999)"

    # morphometric_features==6 -> peaks
    # run_command("r.mapcalc", overwrite=ow,expression='frict_surf_extr = if(morphometric_features==6, 99999) + if(rivers>=1 || lakes>=1, 99999) + if(yield_pix1<=0, 99999) + pix_cross')
    run_command("r.mapcalc", overwrite=ow, expression=exprmap)

    run_command(
        "r.cost",
        overwrite=ow,
        input="frict_surf_extr",
        output="extr_dist",
        stop_points=vector_forest,
        start_rast=forest_roads,
        max_cost=1500,
    )

    run_command(
        "r.slope.aspect",
        overwrite=ow,
        elevation=opts["dtm"],
        slope="slope",
        format="percent",
    )
    run_command("r.mapcalc", overwrite=ow, expression=CCEXTR)
    run_command("r.mapcalc", overwrite=ow, expression=FWEXTR)
    run_command("r.mapcalc", overwrite=ow, expression=OEXTR)
    run_command("r.null", map="cable_crane_extraction", null=0)
    run_command("r.null", map="forwarder_extraction", null=0)
    run_command("r.null", map="other_extraction", null=0)
    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression="technical_surface = cable_crane_extraction + forwarder_extraction + other_extraction",
    )
    # run_command("r.statistics", overwrite=ow,
    #             base="compartment", cover="technical_surface", method="sum",
    #             output="techn_pix_comp")
    # run_command("r.mapcalc", overwrite=ow,
    #             expression='yield_pix2 = yield/(technical_surface*@techn_pix_comp)')
    # run_command("r.null", map="yield_pix2", null=0)
    # run_command("r.mapcalc", overwrite=ow,
    #             expression=YPIX % (1 if flgs['u'] else 0, 0 if flgs['u'] else 1,))

    run_command("r.mapcalc", overwrite=ow, expression="yield_pix=yield_pix1")

    run_command("r.mapcalc", overwrite=ow, expression=EHF)
    run_command("r.mapcalc", overwrite=ow, expression=ECC)
    run_command("r.mapcalc", overwrite=ow, expression=ET)

    with RasterRow(tech_bioenergy) as pT:
        T = np.array(pT)

    print(
        "Resulted maps: "
        + output
        + "_tech_bioenergyHF, "
        + output
        + "_tech_bioenergyC, "
        + output
        + "_tech_bioenergy"
    )
    print("Total bioenergy stimated (Mwh): %.2f" % np.nansum(T))

    if flgs["r"]:
        remove_map(opts, flgs)


if __name__ == "__main__":
    main(*parser())
