#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      biomasfor.import
# AUTHOR(S):   Sandro Sacchelli
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
# % description: Assess the technical biomass availability
# % keyword: raster
# % keyword: biomass
# %End
# %option G_OPT_R_INPUT
# % key: dtm
# % type: string
# % description: Name of Digital terrain model map
# % required : yes
# %end
# %option
# % key: slp_min_cc
# % type: double
# % description: Percent slope lower limit with Cable Crane
# % answer: 30.
# % required : no
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
# % description: Energy for tops and branches in high forest in MWh/m³
# % answer: 0.49
# % required : no
# % guisection: Energy
# %end
# %option
# % key: energy_cormometric_vol_hf
# % type: double
# % description: Energy for tops and branches for high forest in MWh/m³
# % answer: 1.97
# % required : no
# % guisection: Energy
# %end
# %option
# % key: energy_tops_cop
# % type: double
# % description: Energy for tops and branches for Coppices in MWh/m³
# % answer: 0.55
# % required : no
# % guisection: Energy
# %end
# %flag
# % key: u
# % description: technical bioenergy can be considered to be spread uniformly over the entire surface or to be concentrated in accessible areas.
# %end
from grass.script.core import overwrite, parser, run_command

# CCEXTR = 'cable_crane_extraction = if(yield>0 && slope>%f && slope<=%f && extr_dist<%f, 1)'
# FWEXTR = 'forwarder_extraction = if(yield>0 && slope<=%f && management==1 && (roughness==0 || roughness==1 || roughness==99999) && extr_dist<%f, 1)'
# OEXTR = 'other_extraction = if(yield>0 && slope<=%f && management==2 && (roughness==0 || roughness==1 || roughness==99999) && extr_dist<%f, 1)'
YPIX = "yield_pix = yield_pix1*%d + yield_pix2*%d"
# EHF = 'technical_bioenergyHF = technical_surface*(if(management==1 && treatment==1 || management==1 && treatment==99999, yield_pix*%f, if(management==1 && treatment==2, yield_pix * %f + yield_pix * %f)))'
# ECC = 'technical_bioenergyC = technical_surface*(if(management == 2, yield_pix*%f))'


def main(opts, flgs):
    ow = overwrite()

    CCEXTR = (
        "cable_crane_extraction = if(yield>0 && slope>"
        + opts["slp_min_cc"]
        + " && slope<="
        + opts["slp_max_cc"]
        + " && extr_dist<"
        + opts["dist_max_cc"]
        + ", 1)"
    )

    FWEXTR = (
        "forwarder_extraction = if(yield>0 && slope<="
        + opts["slp_max_fw"]
        + " && management==1 && (roughness==0 || roughness==1 || roughness==99999) && extr_dist<"
        + opts["dist_max_fw"]
        + ", 1)"
    )

    OEXTR = (
        "other_extraction = if(yield>0 && slope<="
        + opts["slp_max_cop"]
        + " && management==2 && (roughness==0 || roughness==1 || roughness==99999) && extr_dist<"
        + opts["dist_max_cop"]
        + ", 1)"
    )

    EHF = (
        "technical_bioenergyHF = technical_surface*(if(management==1 && treatment==1 || management==1 && treatment==99999, yield_pix*"
        + opts["energy_tops_hf"]
        + ", if(management==1 && treatment==2, yield_pix *"
        + opts["energy_tops_hf"]
        + " + yield_pix * "
        + opts["energy_cormometric_vol_hf"]
        + ")))"
    )

    ECC = (
        "technical_bioenergyC = technical_surface*(if(management == 2, yield_pix*"
        + opts["energy_tops_cop"]
        + "))"
    )

    run_command(
        "r.param.scale",
        overwrite=ow,
        input=opts["dtm"],
        output="morphometric_features",
        size=3,
        param="feature",
    )
    run_command(
        "r.slope.aspect", overwrite=ow, elevation=opts["dtm"], slope="slope_deg"
    )
    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression="pix_cross = ((ewres()+nsres())/2)/ cos(slope_deg)",
    )
    run_command("r.null", map="yield_pix1", null=0)
    run_command("r.null", map="lakes", null=0)
    run_command("r.null", map="rivers", null=0)
    run_command("r.null", map="morphometric_features", null=0)
    # morphometric_features==6 -> peaks
    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression="frict_surf_extr = if(morphometric_features==6, 99999) + if(rivers>=1 || lakes>=1, 99999) + if(yield_pix1<=0, 99999) + pix_cross",
    )
    run_command(
        "r.cost",
        overwrite=ow,
        input="frict_surf_extr",
        output="extr_dist",
        stop_points="forest",
        start_rast="forest_roads",
        max_cost=1500,
    )
    run_command(
        "r.slope.aspect",
        flags="a",
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
    run_command(
        "r.statistics",
        overwrite=ow,
        base="compartment",
        cover="technical_surface",
        method="sum",
        output="techn_pix_comp",
    )
    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression="yield_pix2 = yield/(technical_surface*@techn_pix_comp)",
    )
    run_command("r.null", map="yield_pix2", null=0)
    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression=YPIX
        % (
            1 if flgs["u"] else 0,
            0 if flgs["u"] else 1,
        ),
    )
    run_command("r.mapcalc", overwrite=ow, expression=EHF)
    run_command("r.mapcalc", overwrite=ow, expression=ECC)
    run_command(
        "r.mapcalc",
        overwrite=ow,
        expression="technical_bioenergy =  (technical_bioenergyHF +  technical_bioenergyC)",
    )


if __name__ == "__main__":
    main(*parser())
