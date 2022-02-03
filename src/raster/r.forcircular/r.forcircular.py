#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      r.forcircular
# AUTHOR(S):   Francesco Geri, Sandro Sacchelli
# PURPOSE:     Evaluation of circular bioeconomy level of forest ecosystems
# COPYRIGHT:   (C) 2022 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
# %Module
# % description: Evaluation of circular bioconomy level of forest ecosystems
# % keyword: bioeconomy
# % keyword: forest
# %End
# %option G_OPT_V_INPUT
# % key: forest
# % type: string
# % description: Name of input parcel parcel map
# % label: Name of input parcel parcel map
# % required : yes
# % guisection: Base
# %end
# %option G_OPT_V_INPUT
# % key: boundaries
# % type: string
# % description: Name of input boundaries vector boolean map
# % label: Name of input boundaries vector boolean map
# % required : yes
# % guisection: Base
# %end
# %option G_OPT_R_ELEV
# % key: dtm
# % type: string
# % description: Name of input elevation raster map
# % required : yes
# % guisection: Base
# %end
# %option G_OPT_V_INPUT
# % key: tracks
# % type: string
# % description: Name of input forest roads vector map
# % label: Name of input forest roads vector map
# % guisection: Base
# % required : yes
# %end
# %option G_OPT_V_INPUT
# % key: rivers
# % type: string
# % description: Name of input rivers vector map
# % label: Name of input rivers vector map
# % required : no
# % guisection: Base
# %end
# %option G_OPT_V_INPUT
# % key: lakes
# % type: string
# % description: Name of input lakes vector map
# % label: Name of input lakes vector map
# % required : no
# % guisection: Base
# %end
# %option G_OPT_V_INPUT
# % key: protected_areas
# % type: string
# % description: Name of input protected areas vector map
# % label: Name of input protected areas vector map
# % required : no
# % guisection: Base
# %end
# %option
# % key: slp_min_cc
# % type: double
# % description: Percent slope lower limit for aerial extraction
# % answer: 30.
# % required : yes
# % guisection: Variables
# %end
# %option
# % key: slp_max_cc
# % type: double
# % description: Percent slope higher limit for aerial extraction
# % answer: 100.
# % required : yes
# % guisection:Variables
# %end
# %option
# % key: dist_max_cc
# % type: double
# % description: Maximum distance for aerial extraction
# % answer: 1000.
# % required : yes
# % guisection: Variables
# %end
# %option
# % key: slp_max_fw
# % type: double
# % description: Percent slope higher limit with Forwarder
# % answer: 30.
# % required : no
# % guisection: Variables
# %end
# %option
# % key: dist_max_fw
# % type: double
# % description: Maximum distance with Forwarder
# % answer: 900.
# % required : yes
# % guisection: Variables
# %end
# %option
# % key: slp_max_cop
# % type: double
# % description: Percent slope higher limit with other techniques for Coppices
# % answer: 30.
# % required : yes
# % guisection: Variables
# %end
# %option
# % key: dist_max_cop
# % type: double
# % description: Maximum distance with other techniques for Coppices
# % answer: 800.
# % required : yes
# % guisection: Variables
# %end
# %option
# % key: hf_slope
# % type: string
# % description: Machineries for high forest in steep terrain
# % options: cable crane - high power,cable crane - medium/low power,skidder
# % required: yes
# % guisection: Variables
# %end
# %option
# % key: c_slope
# % type: string
# % description: Machineries for coppice in steep terrain
# % options: cable crane - high power,cable crane - medium/low power,tractor
# % required: yes
# % guisection: Variables
# %end
# %option
# % key: hf_noslope
# % type: string
# % description: Vehicle for high forest in not steep terrain
# % options: forwarder,skidder,tractor
# % required: yes
# % guisection: Variables
# %end
# %option
# % key: c_noslope
# % type: string
# % description: Vehicle for coppice in not steep terrain
# % options: forwarder,skidder,tractor
# % required: yes
# % guisection: Variables
# %end
# %option
# % key: resolution
# % type: value
# % description: Working resolution
# % answer: 10
# % required : no
# %end
# %option
# % key: cost_chainsaw
# % type: double
# % description: Felling and/or felling-processing cost with chainsaw EUR/h
# % answer: 13.17
# % guisection: Costs
# %end
# %option
# % key: cost_processor
# % type: double
# % description: Processing cost with processor EUR/h
# % answer: 83.52
# % guisection: Costs
# %end
# %option
# % key: cost_harvester
# % type: double
# % description: Felling and processing cost with harvester EUR/h
# % answer: 96.33
# % guisection: Costs
# %end
# %option
# % key: cost_cablehf
# % type: double
# % description: Extraction cost with high power cable crane EUR/h
# % answer: 111.64
# % guisection: Costs
# %end
# %option
# % key: cost_cablec
# % type: double
# % description: Extraction cost with medium power cable crane EUR/h
# % answer: 104.31
# % guisection: Costs
# %end
# %option
# % key: cost_forwarder
# % type: double
# % description: Extraction cost with forwarder EUR/h
# % answer: 70.70
# % guisection: Costs
# %end
# %option
# % key: cost_skidder
# % type: double
# % description: Extraction cost with skidder EUR/h
# % answer: 64.36
# % guisection: Costs
# %end
# %option
# % key: cost_tractor
# % type: double
# % description: Extraction cost with tractor EUR/h
# % answer: 45
# % guisection: Costs
# %end
# %option
# % key: cost_chipping
# % type: double
# % description: Chipping cost EUR/h
# % answer: 160.87
# % guisection: Costs
# %end
# %option
# % key: interest
# % type: double
# % description: Interest rate EUR/h
# % answer: 0.03
# % guisection: Costs
# %end
# %option
# % key: mc_paper
# % type: double
# % description: Percentage of roundwood re-use in paper
# % answer : 0.02
# % guisection: Indicators
# %end
# %option
# % key: mc_furniture
# % type: double
# % description: Percentage of roundwood re-use in furniture
# % answer : 0.4
# % guisection: Indicators
# %end
# %option
# % key: mc_building
# % type: double
# % description: Percentage of roundwood re-use in building
# % answer : 0.5
# % guisection: Indicators
# %end
# %option
# % key: mc_woodpackaging
# % type: double
# % description: Percentage of roundwood re-use in packaging
# % answer : 0.03
# % guisection: Indicators
# %end
# %option
# % key: mc_other
# % type: double
# % description: Percentage of roundwood re-use in other use
# % answer : 0.05
# % guisection: Indicators
# %end
# %option
# % key: ind1
# % type: string
# % gisprompt: new
# % description: Name for indicator n.1 map
# % key_desc : name
# % required: yes
# % guisection: Indicators
# %end
# %option
# % key: ind2
# % type: string
# % gisprompt: new
# % description: Name for indicator n.2 map
# % key_desc : name
# % required: yes
# % guisection: Indicators
# %end
# %option
# % key: ind3
# % type: string
# % gisprompt: new
# % description: Name for indicator n.3 map
# % key_desc : name
# % required: yes
# % guisection: Indicators
# %end
# %option
# % key: ind4
# % type: string
# % gisprompt: new
# % description: Name for indicator n.4 map
# % key_desc : name
# % required: yes
# % guisection: Indicators
# %end
# %option
# % key: ind5
# % type: string
# % gisprompt: new
# % description: Name for indicator n.5 map
# % key_desc : name
# % required: yes
# % guisection: Indicators
# %end
# %option
# % key: ind6
# % type: string
# % gisprompt: new
# % description: Name for indicator n.6 map
# % key_desc : name
# % required: yes
# % guisection: Indicators
# %end
# %option
# % key: ind7
# % type: string
# % gisprompt: new
# % description: Name for indicator n.7 map
# % key_desc : name
# % required: yes
# % guisection: Indicators
# %end
# %option
# % key: w_1
# % type: double
# % description: Weight for indicator n.1
# % answer : 0.15
# % guisection: Indicators
# %end
# %option
# % key: w_2
# % type: double
# % description: Weight for indicator n.2
# % answer : 0.12
# % guisection: Indicators
# %end
# %option
# % key: w_3
# % type: double
# % description: Weight for indicator n.3
# % answer : 0.12
# % guisection: Indicators
# %end
# %option
# % key: w_4
# % type: double
# % description: Weight for indicator n.4
# % answer : 0.13
# % guisection: Indicators
# %end
# %option
# % key: w_5
# % type: double
# % description: Weight for indicator n.5
# % answer : 0.14
# % guisection: Indicators
# %end
# %option
# % key: w_6
# % type: double
# % description: Weight for indicator n.6
# % answer : 0.17
# % guisection: Indicators
# %end
# %option
# % key: w_7
# % type: double
# % description: Weight for indicator n.7
# % answer : 0.16
# % guisection: Indicators
# %end
# %flag
# % key: r
# % description: Remove all operational maps
# %end


from grass.script.core import run_command, parser, overwrite
from grass.pygrass.raster import RasterRow
from grass.pygrass.modules import Module
from grass.pygrass.modules.shortcuts import raster as r
import numpy as np
from subprocess import PIPE
from grass.script import parse_key_val
import pdb


def remove_map(opts, flgs, dic1, dic2, dic_ind2):
    run_command("g.remove", type="raster", flags="f", name="incr_ha")
    run_command("g.remove", type="raster", flags="f", name="management")
    run_command("g.remove", type="raster", flags="f", name="treatment")
    run_command("g.remove", type="raster", flags="f", name="tree_diam")
    run_command("g.remove", type="raster", flags="f", name="pric_bioe")
    run_command("g.remove", type="raster", flags="f", name="tree_vol")
    run_command("g.remove", type="raster", flags="f", name="soil_prod")
    run_command("g.remove", type="raster", flags="f", name="roughness")
    run_command("g.remove", type="raster", flags="f", name="rotation")
    run_command("g.remove", type="raster", flags="f", name="cut")
    run_command("g.remove", type="raster", flags="f", name="PCI")
    run_command("g.remove", type="raster", flags="f", name="tracks")
    run_command("g.remove", type="raster", flags="f", name="boundaries")
    run_command("g.remove", type="raster", flags="f", name="increment")
    run_command(
        "g.remove", type="raster", flags="f", name="morphometric_features"
    )
    run_command("g.remove", type="raster", flags="f", name="pix_cross")
    run_command("g.remove", type="raster", flags="f", name="frict_surf_extr")
    run_command("g.remove", type="raster", flags="f", name="extr_dist")
    run_command("g.remove", type="raster", flags="f", name="aerial_extraction")
    run_command(
        "g.remove", type="raster", flags="f", name="HFground_extraction"
    )
    run_command(
        "g.remove", type="raster", flags="f", name="Cground_extraction"
    )
    run_command("g.remove", type="raster", flags="f", name="volume")
    run_command("g.remove", type="raster", flags="f", name="tracks")
    run_command("g.remove", type="raster", flags="f", name="boundaries")
    for key, val in dic1.items():
        run_command(
            "g.remove", type="raster", flags="f", name="tmpc_%s" % (key)
        )

    run_command("g.remove", type="raster", flags="f", name="chipp_cost")
    run_command("g.remove", type="raster", flags="f", name="direction_cost")
    run_command("g.remove", type="raster", flags="f", name="interests")
    run_command("g.remove", type="raster", flags="f", name="costs_reclass")
    run_command("g.remove", type="raster", flags="f", name="stump_value_ha")
    run_command("g.remove", type="raster", flags="f", name="a_stump_value_ha")
    run_command("g.remove", type="raster", flags="f", name="clumped_area")
    run_command("g.remove", type="raster", flags="f", name="revenues9")
    run_command(
        "g.remove", type="raster", flags="f", name="administrative_cost9"
    )
    run_command("g.remove", type="raster", flags="f", name="costs9")
    run_command("g.remove", type="raster", flags="f", name="costs_reclass9")
    run_command("g.remove", type="raster", flags="f", name="stumpage_value9")
    run_command("g.remove", type="raster", flags="f", name="a_stumpage_value9")
    run_command("g.remove", type="raster", flags="f", name="economic_surface9")
    run_command(
        "g.remove", type="raster", flags="f", name="administrative_cost"
    )
    run_command("g.remove", type="raster", flags="f", name="clumped_area")
    run_command("g.remove", type="raster", flags="f", name="clumped_area9")
    run_command("g.remove", type="raster", flags="f", name="costs9")
    run_command("g.remove", type="raster", flags="f", name="costs_reclass9")
    run_command("g.remove", type="raster", flags="f", name="economic_surface9")
    run_command("g.remove", type="raster", flags="f", name="perc_res")
    run_command("g.remove", type="raster", flags="f", name="slope_deg")
    run_command("g.remove", type="raster", flags="f", name="stumpage_value9")
    run_command("g.remove", type="raster", flags="f", name="interests9")
    run_command("g.remove", type="raster", flags="f", pattern="extr_*")
    run_command("g.remove", type="raster", flags="f", pattern="mc_*")
    run_command("g.remove", type="raster", flags="f", pattern="chipp_*")
    run_command("g.remove", type="raster", flags="f", pattern="fell_*")
    run_command("g.remove", type="raster", flags="f", pattern="perc_*")
    run_command("g.remove", type="raster", flags="f", pattern="pric_*")

    for key, val in dic2.items():
        run_command("g.remove", type="raster", flags="f", name=key)

    for key, val in dic_ind2.items():
        run_command("g.remove", type="raster", flags="f", name="em_%s" % (key))


def indicator2(opts, flgs):
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression=opts["ind2"]
        + "= clumped_area*(emission / volume)/rotation",
    )


def indicator4(opts, flgs):

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="mc_paper = roundwood*" + opts["mc_paper"],
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="mc_furniture = roundwood*" + opts["mc_furniture"],
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="mc_building = roundwood*" + opts["mc_building"],
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="mc_woodpackaging = roundwood*" + opts["mc_woodpackaging"],
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="mc_other = roundwood*" + opts["mc_other"],
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression=opts["ind4"]
        + " = mc_paper*2*(1+0.8+0.8^2+0.8^3+0.8^4+0.8^5) + mc_furniture*20*"
        + "(1+0.1) + mc_building*25*(1+0.9) + mc_woodpackaging*3 + mc_other*"
        + "3 + timber*20 + firewood*1 + bioenergy/PCI*0.5",
    )


def indicator5(opts, flgs):

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="revenues9 = technical_surface*(volume*(perc_roun9*"
        + "pric_roun + perc_timb9*pric_timb + perc_fire9*pric_fire + "
        + "perc_res9*PCI*pric_bioe))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="administrative_cost9 = revenues9*0.07",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="interests9 = (prod_costs +  administrative_cost9)*"
        + opts["interest"]
        + "/4",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="costs9 = if(management==2,(prod_costs + "
        + "direction_cost + administrative_cost9 + interests9)"
        + "*0.825, prod_costs + direction_cost + "
        + "administrative_cost9 + interests9)",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="costs_reclass9 = if(costs9<0,99999,costs9)",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="stumpage_value9 = if(revenues9 - "
        + "costs_reclass9<=0,0, revenues9 - costs_reclass9)",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="a_stumpage_value9 = stumpage_value9*("
        + opts["interest"]
        + "/(((1+"
        + opts["interest"]
        + ")^rotation) -1))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="economic_surface9 = if(stumpage_value9>0,1,0)",
    )

    run_command(
        "r.reclass.area",
        overwrite=True,
        input="economic_surface9",
        output="clumped_area9",
        value=0.5,
        mode="greater",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression=opts["ind5"]
        + " = clumped_area9*(a_stumpage_value9 / a_stumpage_value)",
    )


def main(opts, flgs):
    ow = overwrite()

    c_hf_slope = {
        "cable crane - high power": 1,
        "cable crane - medium/low power": 0.7,
        "skidder": 0.5,
    }

    c_c_slope = {
        "cable crane - high power": 1.2,
        "cable crane - medium/low power": 1,
        "tractor": 0.7,
    }

    c_hf_noslope = {
        "forwarder": 1,
        "skidder": 0.8,
        "tractor": 0.65
        # ,"other": 0.5
    }

    c_c_noslope = {
        "forwarder": 1.2,
        "skidder": 1,
        "tractor": 0.85
        # ,"other": 0.7
    }

    forest = opts["forest"]
    dtm = opts["dtm"]
    boundaries = opts["boundaries"]

    rivers = opts["rivers"]
    lakes = opts["lakes"]

    tracks = opts["tracks"]

    protected_areas = opts["protected_areas"]

    resolution = opts["resolution"]

    # start import and convert

    if resolution == "":
        resolution = 10

    run_command("g.region", vect=boundaries, res=resolution)

    run_command(
        "v.to.rast",
        input=forest,
        output="incr_ha",
        use="attr",
        attrcolumn="incr_ha",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="management",
        use="attr",
        attrcolumn="management",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="treatment",
        use="attr",
        attrcolumn="treatment",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="perc_roun",
        use="attr",
        attrcolumn="perc_roun",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="perc_timb",
        use="attr",
        attrcolumn="perc_timb",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="perc_fire",
        use="attr",
        attrcolumn="perc_fire",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="perc_res",
        use="attr",
        attrcolumn="perc_res",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="perc_roun9",
        use="attr",
        attrcolumn="perc_roun9",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="perc_timb9",
        use="attr",
        attrcolumn="perc_timb9",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="perc_fire9",
        use="attr",
        attrcolumn="perc_fire9",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="perc_res9",
        use="attr",
        attrcolumn="perc_res9",
        overwrite=True,
    )

    run_command(
        "v.to.rast",
        input=forest,
        output="pric_roun",
        use="attr",
        attrcolumn="pric_roun",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="pric_timb",
        use="attr",
        attrcolumn="pric_timb",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="pric_fire",
        use="attr",
        attrcolumn="pric_fire",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="pric_bioe",
        use="attr",
        attrcolumn="pric_bioe",
        overwrite=True,
    )

    run_command(
        "v.to.rast",
        input=forest,
        output="tree_diam",
        use="attr",
        attrcolumn="tree_diam",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="tree_vol",
        use="attr",
        attrcolumn="tree_vol",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="soil_prod",
        use="attr",
        attrcolumn="soil_prod",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="roughness",
        use="attr",
        attrcolumn="roughness",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="rotation",
        use="attr",
        attrcolumn="rotation",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="cut",
        use="attr",
        attrcolumn="cut",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=forest,
        output="PCI",
        use="attr",
        attrcolumn="PCI",
        overwrite=True,
    )

    run_command(
        "v.to.rast", input=tracks, output="tracks", use="val", overwrite=True
    )

    run_command(
        "v.to.rast",
        input=boundaries,
        output="boundaries",
        use="val",
        overwrite=True,
    )

    # end import and convert

    # start technical

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="increment = incr_ha*((ewres()*nsres())/10000)",
    )
    run_command("r.null", map="increment", null=0)

    run_command(
        "r.param.scale",
        overwrite=True,
        input=dtm,
        output="morphometric_features",
        size=3,
        method="feature",
    )
    run_command("r.null", map="morphometric_features", null=0)

    run_command(
        "r.slope.aspect", overwrite=True, elevation=dtm, slope="slope_deg"
    )
    run_command(
        "r.mapcalc",
        overwrite=True,
        expression="pix_cross = ((ewres()+nsres())/2)/ cos(slope_deg)",
    )

    exprmap = "frict_surf_extr = pix_cross + if(increment<=0, 99999)"
    exprmap += " + if(morphometric_features==6, 99999)"

    if rivers != "":
        run_command(
            "v.to.rast",
            input=rivers,
            output="rivers",
            use="val",
            overwrite=True,
        )
        run_command("r.null", map="rivers", null=0)
        rivers = "rivers"
        exprmap += "+ if(" + rivers + ">=1, 99999)"

    if lakes != "":
        run_command(
            "v.to.rast", input=lakes, output="lakes", use="val", overwrite=True
        )
        run_command("r.null", map="lakes", null=0)
        lakes = "lakes"
        exprmap += "+ if(" + lakes + ">=1, 99999)"

    run_command("r.mapcalc", overwrite=True, expression=exprmap)

    run_command(
        "r.cost",
        overwrite=True,
        input="frict_surf_extr",
        output="extr_dist",
        stop_points=forest,
        start_rast=tracks,
        max_cost=3000,
    )

    run_command(
        "r.slope.aspect",
        overwrite=True,
        elevation=dtm,
        slope="slope",
        format="percent",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="aerial_extraction = if(incr_ha>0 && slope>"
        + opts["slp_min_cc"]
        + " && slope<="
        + opts["slp_max_cc"]
        + " && extr_dist<"
        + opts["dist_max_cc"]
        + ",1)",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="HFground_extraction = if(incr_ha>0 && slope<="
        + opts["slp_max_fw"]
        + " && management==1 && (roughness==0 || roughness==1 || "
        + "roughness== 99999) && extr_dist<"
        + opts["dist_max_fw"]
        + ",1)",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="Cground_extraction = if(incr_ha>0 && slope<="
        + opts["slp_max_cop"]
        + " && management==2 && (roughness==0 || roughness==1 || "
        + "roughness== 99999) && extr_dist<"
        + opts["dist_max_cop"]
        + ",1)",
    )

    run_command("r.null", map="aerial_extraction", null=0)
    run_command("r.null", map="HFground_extraction", null=0)
    run_command("r.null", map="Cground_extraction", null=0)

    run_command(
        "r.mapcalc",
        overwrite=True,
        expression="technical_surface = aerial_extraction + "
        + "HFground_extraction + Cground_extraction",
    )

    # end technical

    # start economic

    if protected_areas != "":
        run_command(
            "v.to.rast",
            input=protected_areas,
            output="protected_areas",
            use="val",
            overwrite=True,
        )
        run_command("r.null", map="protected_areas", null=0)
        run_command(
            "r.mapcalc",
            overwrite=1,
            expression="volume = increment*rotation*(if"
            + "(protected_areas==1,0.5,1))*cut",
        )
    else:
        run_command(
            "r.mapcalc",
            overwrite=1,
            expression="volume = increment*rotation*cut",
        )

    run_command("r.null", map="volume", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="revenues = technical_surface*(volume*(perc_roun*"
        + "pric_roun + perc_timb*pric_timb + perc_fire*pric_fire + "
        + "perc_res*PCI*pric_bioe))",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_productHFtr1 = if(management ==1 && treatment"
        + " ==1 && tree_diam <99999,(aerial_extraction*(42-(2.6*tree_diam))"
        + "/(-20))*1.65*(1-(slope/100)), if(management ==1 && treatment ==1"
        + " && tree_diam == 99999,(aerial_extraction*"
        + "(42-(2.6*35))/(-20))*1.65*(1-(slope/100))))",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_productHFtr2 = if(management ==1 && treatment ==2"
        + " && tree_diam <99999,(aerial_extraction*(42-(2.6*tree_diam))/"
        + "(-20))*1.65*(1-(slope/100)), if(management ==1 && treatment ==2"
        + " && tree_diam == 99999,(aerial_extraction*(42-(2.6*35))/"
        + "(-20))*1.65*(1-(slope/100))))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_proc_productC = if(management ==2 && soil_prod <99999"
        + ",((0.3-(1.1*soil_prod))/(-4))*(1-(slope/100)), if(management ==2 &&"
        + " soil_prod == 99999,((0.3-(1.1*3))/(-4))*(1-(slope/100))))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="proc_productHFtr1 = if(management == 1 && treatment == 1 "
        + "&& tree_diam==99999, aerial_extraction*0.363*35^1.116, "
        + "if(management == 1 && treatment == 1 && tree_diam<99999, "
        + "aerial_extraction *0.363*tree_diam^1.116))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_proc_productHFtr1 = if(management == 1 && treatment"
        + " == 1 && tree_vol<9.999, HFground_extraction*60/(1.5*(2.71^(0.1480"
        + "-0.3894*2+0.0002*(slope^2)-0.2674*2.5))+(1.0667+(0.3094/tree_vol)"
        + "-0.1846*1)), if(management == 1 && treatment == 1 && "
        + "tree_vol==9.999 , HFground_extraction*60/(1.5*(2.71^(0.1480-"
        + "0.3894*2+0.0002*(slope^2)-0.2674*2.5))+(1.0667+(0.3094/0.7)"
        + "-0.1846*1))))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_proc_productHFtr2 = if(management == 1 && "
        + "treatment == 2 && tree_vol<9.999, "
        + "HFground_extraction*60/(1.5*(2.71^(0.1480-"
        + "0.3894*2+0.0002*(slope^2)-0.2674*2.5))+(1.0667+"
        + "(0.3094/tree_vol)-0.1846*1))*0.8,if(management"
        + " == 1 && treatment == 2 && "
        + "tree_vol==9.999, HFground_extraction*60/(1.5*"
        + "(2.71^(0.1480-0.3894*2+0.0002*(slope^2)-0.2674*2.5))"
        + "+(1.0667+(0.3094/0.7)-0.1846*1))*0.8))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="chipp_prodHF = if(management ==1 && treatment == 1"
        + ", volume/34, if(management ==1 && treatment == 2, volume/20.1))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="chipp_prodC = if(management ==2, volume/45.9)",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="chipp_prod = chipp_prodHF + chipp_prodC",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="extr_product_cableHF = if(management ==1, "
        + "aerial_extraction*56*((if(extr_dist==0,10, extr_dist))^-1.1685)*"
        + "((if(extr_dist==0,10,extr_dist))/8*0.75))*"
        + str(c_hf_slope[opts["hf_slope"]]),
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="extr_product_cableC = if(management ==2, aerial_extraction"
        + "*149.33*((if(extr_dist==0,10, extr_dist))^-1.3438)*"
        + "((if(extr_dist==0,10, extr_dist))/8*0.75))*"
        + str(c_c_slope[opts["c_slope"]]),
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="extr_product_HFground = HFground_extraction*16.14*"
        + "((if(extr_dist==0,10, extr_dist))^-0.8126)*"
        + "((if(extr_dist==0,10, extr_dist))/8*0.6)*"
        + str(c_hf_noslope[opts["hf_noslope"]]),
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="extr_product_Cground = Cground_extraction*36.293"
        + "*((if(extr_dist==0,10, extr_dist))^-1.1791)*"
        + "((if(extr_dist==0,10, extr_dist))/8*0.6)*"
        + str(c_c_noslope[opts["c_noslope"]]),
    )

    # start costs calculation

    dic1 = {
        "fell_productHFtr1": opts["cost_chainsaw"],
        "fell_productHFtr2": opts["cost_chainsaw"],
        "fell_proc_productC": opts["cost_chainsaw"],
        "proc_productHFtr1": opts["cost_processor"],
        "fell_proc_productHFtr1": opts["cost_harvester"],
        "fell_proc_productHFtr2": opts["cost_harvester"],
        "extr_product_cableHF": opts["cost_cablehf"],
        "extr_product_cableC": opts["cost_cablec"],
        "extr_product_HFground": opts["cost_forwarder"],
        "extr_product_Cground": opts["cost_skidder"],
    }

    interest = opts["interest"]

    if opts["hf_slope"] == "cable crane - high power":
        vcost_cable_hf = opts["cost_cablehf"]
    elif opts["hf_slope"] == "cable crane - medium/low power":
        vcost_cable_hf = opts["cost_cablec"]
    elif opts["hf_slope"] == "skidder":
        vcost_cable_hf = opts["cost_skidder"]

    if opts["c_slope"] == "cable crane - high power":
        vcost_cable_c = opts["cost_cablehf"]
    elif opts["c_slope"] == "cable crane - medium/low power":
        vcost_cable_c = opts["cost_cablec"]
    elif opts["c_slope"] == "tractor":
        vcost_cable_c = opts["cost_tractor"]

    if opts["hf_noslope"] == "forwarder":
        vcost_forw = opts["cost_forwarder"]
    elif opts["hf_noslope"] == "skidder":
        vcost_forw = opts["cost_skidder"]
    elif opts["hf_noslope"] == "tractor":
        vcost_forw = opts["cost_tractor"]

    if opts["c_noslope"] == "forwarder":
        vcost_Cground = opts["cost_forwarder"]
    elif opts["c_noslope"] == "skidder":
        vcost_Cground = opts["cost_skidder"]
    elif opts["c_noslope"] == "tractor":
        vcost_Cground = opts["cost_tractor"]

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_costHFtr1 = "
        + opts["cost_chainsaw"]
        + "/fell_productHFtr1*volume",
    )
    run_command("r.null", map="fell_costHFtr1", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_costHFtr2 = "
        + opts["cost_chainsaw"]
        + "/fell_productHFtr2*volume",
    )
    run_command("r.null", map="fell_costHFtr2", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_proc_costC = "
        + opts["cost_chainsaw"]
        + "/fell_proc_productC*volume",
    )
    run_command("r.null", map="fell_proc_costC", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="proc_costHFtr1 = "
        + opts["cost_processor"]
        + "/proc_productHFtr1*volume",
    )
    run_command("r.null", map="proc_costHFtr1", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_proc_costHFtr1 = "
        + opts["cost_harvester"]
        + "/fell_proc_productHFtr1*volume",
    )
    run_command("r.null", map="fell_proc_costHFtr1", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="fell_proc_costHFtr2 = "
        + opts["cost_harvester"]
        + "/fell_proc_productHFtr2*volume",
    )
    run_command("r.null", map="fell_proc_costHFtr2", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="extr_cost_cableHF = "
        + vcost_cable_hf
        + "/extr_product_cableHF*volume",
    )
    run_command("r.null", map="extr_cost_cableHF", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="extr_cost_cableC = "
        + vcost_cable_c
        + "/extr_product_cableC*volume",
    )
    run_command("r.null", map="extr_cost_cableC", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="extr_cost_forw = "
        + vcost_forw
        + "/extr_product_HFground*volume",
    )
    run_command("r.null", map="extr_cost_forw", null=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="extr_cost_Cground = "
        + vcost_Cground
        + "/extr_product_Cground*volume",
    )
    run_command("r.null", map="extr_cost_Cground", null=0)

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="chipp_cost = " + opts["cost_chipping"] + "*chipp_prod",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="prod_costs = fell_costHFtr1 +  fell_costHFtr2+ "
        + "fell_proc_costC + proc_costHFtr1 + fell_proc_costHFtr1 + "
        + "fell_proc_costHFtr2 + chipp_cost + extr_cost_cableHF + "
        + "extr_cost_cableC + extr_cost_forw + extr_cost_Cground",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="direction_cost =  prod_costs *0.05",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="administrative_cost = revenues*0.07",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="interests = (prod_costs +  administrative_cost)*"
        + interest
        + "/4",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="costs = if(management==2,(prod_costs + direction_cost"
        + " + administrative_cost + interests)*0.825, prod_costs + "
        + "direction_cost + administrative_cost + interests)",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="costs_reclass = if(costs<0,99999,costs)",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="stumpage_value = if(revenues - costs_reclass<=0,0"
        + ", revenues - costs_reclass)",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="a_stumpage_value = stumpage_value*("
        + interest
        + "/(((1+"
        + interest
        + ")^rotation) -1))",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="stump_value_ha = if(stumpage_value/(nsres()*"
        + "ewres()/10000)<=0,0, stumpage_value/(nsres()*ewres()/10000))",
    )
    run_command("r.null", map="stump_value_ha", setnull=0)
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="a_stump_value_ha = if(a_stumpage_value/(nsres()*"
        + "ewres()/10000)<=0,0, a_stumpage_value/(nsres()*ewres()/10000))",
    )
    run_command("r.null", map="a_stump_value_ha", setnull=0)

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="economic_surface = if(stumpage_value>0,1,0)",
    )

    run_command(
        "r.reclass.area",
        overwrite=True,
        input="economic_surface",
        output="clumped_area",
        value=0.5,
        mode="greater",
    )

    # end costs calculation

    # start zonal calculation

    expr2 = "{out} = {clumped}*({volume}*{perc})/{rotation}"

    dic2 = {
        "roundwood": "perc_roun",
        "timber": "perc_timb",
        "firewood": "perc_fire",
    }

    for key, val in dic2.items():
        r.mapcalc(
            expr2.format(
                out=key,
                clumped="clumped_area",
                volume="volume",
                perc=val,
                rotation="rotation",
            ),
            overwrite=True,
        )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="bioenergy = clumped_area*(volume*perc_res*PCI) / rotation",
    )

    dic_ind2 = {
        "fell_productHFtr1": 4.725,
        "fell_productHFtr2": 4.725,
        "fell_proc_productC": 2.363,
        "proc_productHFtr1": 37.729,
        "fell_proc_productHFtr1": 36.899,
        "fell_proc_productHFtr2": 36.899,
        "extr_product_cableHF": 20.730,
        "extr_product_cableC": 12.956,
        "extr_product_HFground": 25.394,
        "extr_product_Cground": 15.548,
    }

    command = "sum_em1 = "
    expr = "{out} = {volume}/({productivity}*{coeff})"
    for key, val in dic_ind2.items():
        r.mapcalc(
            expr.format(
                out="em_%s" % (key),
                volume="volume",
                productivity=key,
                coeff=val,
            ),
            overwrite=True,
        )
        run_command("r.null", map=("em_%s" % (key)), null=0)

        command += "em_%s+" % (key)

    command = command[:-1]

    run_command("r.mapcalc", overwrite=1, expression=command)
    run_command(
        "r.mapcalc", overwrite=1, expression="chipp_em = chipp_prod*130.599"
    )
    run_command("r.null", map="chipp_em", null=0)
    run_command(
        "r.mapcalc", overwrite=1, expression="sum_em = sum_em1+chipp_em"
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="emission = clumped_area*sum_em/1000",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="avoided_emission = clumped_area * ((bioenergy*"
        + "rotation*320/1000) - emission)",
    )


    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="a_stumpage_value",
        method="sum",
        output="rep_sum_a_stumpage_value",
    )
    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="stump_value_ha",
        method="average",
        output="rep_ave_stumpage_value",
    )
    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="a_stump_value_ha",
        method="average",
        output="rep_ave_a_stumpage_value",
    )
    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="avoided_emission",
        method="average",
        output="rep_avoided_emission",
    )
    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="roundwood",
        method="sum",
        output="rep_roundwood",
    )
    c_rep_roundwood = Module(
        "r.univar", flags="g", map="roundwood", stdout_=PIPE
    )
    rep_roundwood = parse_key_val(c_rep_roundwood.outputs.stdout)

    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="timber",
        method="sum",
        output="rep_timber",
    )
    c_rep_timber = Module("r.univar", flags="g", map="timber", stdout_=PIPE)
    rep_timber = parse_key_val(c_rep_timber.outputs.stdout)

    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="firewood",
        method="sum",
        output="rep_firewood",
    )
    c_rep_firewood = Module(
        "r.univar", flags="g", map="firewood", stdout_=PIPE
    )
    rep_firewood = parse_key_val(c_rep_firewood.outputs.stdout)

    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="bioenergy",
        method="sum",
        output="rep_bioenergy",
    )
    c_rep_bioenergy = Module(
        "r.univar", flags="g", map="bioenergy", stdout_=PIPE
    )
    rep_bioenergy = parse_key_val(c_rep_bioenergy.outputs.stdout)

    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="a_stumpage_value",
        method="sum",
        output="rep_sum_a_stumpage_value",
    )
    c_rep_a_stumpage_value = Module(
        "r.univar", flags="g", map="a_stumpage_value", stdout_=PIPE
    )
    rep_a_stumpage_value = parse_key_val(c_rep_a_stumpage_value.outputs.stdout)

    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="stump_value_ha",
        method="average",
        output="rep_stump_value_ha",
    )
    c_rep_stump_value_ha = Module(
        "r.univar", flags="g", map="stump_value_ha", stdout_=PIPE
    )
    rep_stump_value_ha = parse_key_val(c_rep_stump_value_ha.outputs.stdout)

    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="a_stump_value_ha",
        method="average",
        output="rep_a_stump_value_ha",
    )
    c_rep_a_stump_value_ha = Module(
        "r.univar", flags="g", map="a_stump_value_ha", stdout_=PIPE
    )
    rep_a_stump_value_ha = parse_key_val(c_rep_a_stump_value_ha.outputs.stdout)

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="annual_avoided_emission = avoided_emission / rotation",
    )
    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="annual_avoided_emission",
        method="sum",
        output="rep_annual_avoided_emission",
    )
    c_rep_annual_avoided_emission = Module(
        "r.univar", flags="g", map="annual_avoided_emission", stdout_=PIPE
    )
    rep_annual_avoided_emission = parse_key_val(
        c_rep_annual_avoided_emission.outputs.stdout
    )

    # start indicators

    if opts["ind1"] != "":
        run_command(
            "r.mapcalc",
            overwrite=1,
            expression=opts["ind1"]
            + "= clumped_area*a_stumpage_value/(volume/rotation)",
        )
        run_command(
            "r.stats.zonal",
            overwrite=1,
            base="clumped_area",
            cover=opts["ind1"],
            method="average",
            output="rep_" + opts["ind1"],
        )
        c_rep_ind1 = Module(
            "r.univar", flags="g", map="rep_" + opts["ind1"], stdout_=PIPE
        )
        rep_ind1 = parse_key_val(c_rep_ind1.outputs.stdout)
        run_command("r.null", map=opts["ind1"], setnull=0)

    if opts["ind2"] != "":
        indicator2(opts, flgs)
        run_command(
            "r.stats.zonal",
            overwrite=True,
            base="clumped_area",
            cover=opts["ind2"],
            method="average",
            output="rep_" + opts["ind2"],
        )
        c_rep_ind2 = Module(
            "r.univar", flags="g", map="rep_" + opts["ind2"], stdout_=PIPE
        )
        rep_ind2 = parse_key_val(c_rep_ind2.outputs.stdout)
        run_command("r.null", map=opts["ind2"], setnull=0)

    if opts["ind3"] != "":
        run_command(
            "r.mapcalc",
            overwrite=1,
            expression=opts["ind3"]
            + " = clumped_area*(((ewres()*nsres())/10000)/rotation)",
        )
        run_command(
            "r.stats.zonal",
            overwrite=True,
            base="clumped_area",
            cover=opts["ind3"],
            method="sum",
            output="rep_" + opts["ind3"],
        )
        c_rep_ind3 = Module(
            "r.univar", flags="g", map="rep_" + opts["ind3"], stdout_=PIPE
        )
        rep_ind3 = parse_key_val(c_rep_ind3.outputs.stdout)
        run_command("r.null", map=opts["ind3"], setnull=0)

    if opts["ind4"] != "":
        indicator4(opts, flgs)
        run_command(
            "r.stats.zonal",
            overwrite=True,
            base="clumped_area",
            cover=opts["ind4"],
            method="sum",
            output="rep_" + opts["ind4"],
        )
        c_rep_ind4 = Module(
            "r.univar", flags="g", map="rep_" + opts["ind4"], stdout_=PIPE
        )
        rep_ind4 = parse_key_val(c_rep_ind4.outputs.stdout)
        run_command("r.null", map=opts["ind4"], setnull=0)

    if opts["ind5"] != "":
        indicator5(opts, flgs)
        run_command(
            "r.stats.zonal",
            overwrite=True,
            base="clumped_area",
            cover=opts["ind5"],
            method="average",
            output="rep_" + opts["ind5"],
        )
        c_rep_ind5 = Module(
            "r.univar", flags="g", map="rep_" + opts["ind5"], stdout_=PIPE
        )
        rep_ind5 = parse_key_val(c_rep_ind5.outputs.stdout)
        run_command("r.null", map=opts["ind5"], setnull=0)

    if opts["ind6"] != "":
        run_command(
            "r.mapcalc",
            overwrite=1,
            expression=opts["ind6"] + " = clumped_area*perc_res",
        )
        run_command(
            "r.stats.zonal",
            overwrite=True,
            base="clumped_area",
            cover=opts["ind6"],
            method="average",
            output="rep_" + opts["ind6"],
        )
        c_rep_ind6 = Module(
            "r.univar", flags="g", map="rep_" + opts["ind6"], stdout_=PIPE
        )
        rep_ind6 = parse_key_val(c_rep_ind6.outputs.stdout)
        run_command("r.null", map=opts["ind6"], setnull=0)

    if opts["ind7"] != "":
        run_command(
            "r.mapcalc",
            overwrite=1,
            expression=opts["ind7"]
            + " = clumped_area*(avoided_emission*1000000)/(bioenergy"
            + "*rotation*1000)",
        )
        run_command(
            "r.stats.zonal",
            overwrite=True,
            base="clumped_area",
            cover=opts["ind7"],
            method="average",
            output="rep_" + opts["ind7"],
        )
        c_rep_ind7 = Module(
            "r.univar", flags="g", map="rep_" + opts["ind7"], stdout_=PIPE
        )
        rep_ind7 = parse_key_val(c_rep_ind7.outputs.stdout)
        run_command("r.null", map=opts["ind7"], setnull=0)

    # end indicators

    # start MCE

    calc_ind = [
        opts["ind1"],
        opts["ind2"],
        opts["ind3"],
        opts["ind4"],
        opts["ind5"],
        opts["ind6"],
        opts["ind7"],
    ]

    with RasterRow(calc_ind[0]) as pT:
        T = np.array(pT)
    max_ind1 = np.nanmax(T)
    min_ind1 = np.nanmin(T)

    with RasterRow(calc_ind[1]) as pT1:
        T1 = np.array(pT1)
    max_ind2 = np.nanmax(T1)
    min_ind2 = np.nanmin(T1)

    with RasterRow(calc_ind[2]) as pT2:
        T2 = np.array(pT2)
    max_ind3 = np.nanmax(T2)
    min_ind3 = np.nanmin(T2)

    with RasterRow(calc_ind[3]) as pT3:
        T3 = np.array(pT3)
    max_ind4 = np.nanmax(T3)
    min_ind4 = np.nanmin(T3)

    with RasterRow(calc_ind[4]) as pT4:
        T4 = np.array(pT4)
    max_ind5 = np.nanmax(T4)
    min_ind5 = np.nanmin(T4)

    with RasterRow(calc_ind[5]) as pT5:
        T5 = np.array(pT5)
    max_ind6 = np.nanmax(T5)
    min_ind6 = np.nanmin(T5)

    with RasterRow(calc_ind[6]) as pT6:
        T6 = np.array(pT6)
    max_ind7 = np.nanmax(T6)
    min_ind7 = np.nanmin(T6)

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="d_ind1 = ("
        + str(max_ind1)
        + "-"
        + calc_ind[0]
        + ")/("
        + str(max_ind1)
        + "-"
        + str(min_ind1)
        + ")",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="dist_ind1=if(d_ind1>1,1,if(d_ind1<0,0,d_ind1))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="d_ind2 = ("
        + str(min_ind2)
        + "-"
        + calc_ind[1]
        + ")/("
        + str(min_ind2)
        + "-"
        + str(max_ind2)
        + ")",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="dist_ind2=if(d_ind2>1,1,if(d_ind2<0,0,d_ind2))",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="d_ind3 = ("
        + str(max_ind3)
        + "-"
        + calc_ind[2]
        + ")/("
        + str(max_ind3)
        + "-"
        + str(min_ind3)
        + ")",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="dist_ind3=if(d_ind3>1,1,if(d_ind3<0,0,d_ind3))",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="d_ind4 = ("
        + str(max_ind4)
        + "-"
        + calc_ind[3]
        + ")/("
        + str(max_ind4)
        + "-"
        + str(min_ind4)
        + ")",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="dist_ind4=if(d_ind4>1,1,if(d_ind4<0,0,d_ind4))",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="d_ind5 = ("
        + str(max_ind5)
        + "-"
        + calc_ind[4]
        + ")/("
        + str(max_ind5)
        + "-"
        + str(min_ind5)
        + ")",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="dist_ind5=if(d_ind5>1,1,if(d_ind5<0,0,d_ind5))",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="d_ind6 = ("
        + str(max_ind6)
        + "-"
        + calc_ind[5]
        + ")/("
        + str(max_ind6)
        + "-"
        + str(min_ind6)
        + ")",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="dist_ind6=if(d_ind6>1,1,if(d_ind6<0,0,d_ind6))",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="d_ind7 = ("
        + str(max_ind7)
        + "-"
        + calc_ind[6]
        + ")/("
        + str(max_ind7)
        + "-"
        + str(min_ind7)
        + ")",
    )
    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="dist_ind7=if(d_ind7>1,1,if(d_ind7<0,0,d_ind7))",
    )

    run_command(
        "r.mapcalc",
        overwrite=1,
        expression="dip = (dist_ind1 * (1-"
        + str(opts["w_1"])
        + ")+dist_ind2 * (1-"
        + str(opts["w_2"])
        + ")+ dist_ind3 * (1-"
        + str(opts["w_3"])
        + ")+ dist_ind4 * (1-"
        + str(opts["w_4"])
        + ")+dist_ind5 * (1-"
        + str(opts["w_5"])
        + ")+ dist_ind6 * (1-"
        + str(opts["w_6"])
        + ")+ dist_ind7 * (1-"
        + str(opts["w_7"])
        + "))",
    )

    run_command(
        "r.stats.zonal",
        overwrite=True,
        base="clumped_area",
        cover="dip",
        method="average",
        output="rep_dip",
    )
    c_rep_dip = Module("r.univar", flags="g", map="rep_dip", stdout_=PIPE)
    rep_dip = parse_key_val(c_rep_dip.outputs.stdout)

    # end MCE

    run_command(
        "r.stats",
        overwrite=True,
        input="rep_roundwood,rep_timber,rep_firewood,rep_bioenergy,"
        + "rep_sum_a_stumpage_value,rep_ave_stumpage_value,"
        + "rep_ave_a_stumpage_value,rep_annual_avoided_emission",
    )
    run_command(
        "r.stats",
        overwrite=True,
        input="rep_"
        + opts["ind1"]
        + ",rep_"
        + opts["ind2"]
        + ",rep_"
        + opts["ind3"]
        + ",rep_"
        + opts["ind4"]
        + ",rep_"
        + opts["ind5"]
        + ",rep_"
        + opts["ind6"]
        + ",rep_"
        + opts["ind7"]
        + ",rep_dip",
    )

    print("\n#############################\n")
    print("End of process\nName of output maps:\n")
    print(
        "rep_roundwood -> roundwood (m3/y): {0:.4f}".format(
            float(rep_roundwood["sum"])
        )
    )
    print(
        "rep_timber -> timber pole (m3/y): {0:.4f}".format(
            float(rep_timber["sum"])
        )
    )
    print(
        "rep_firewood -> firewood (m3/y): {0:.4f}".format(
            float(rep_firewood["sum"])
        )
    )
    print(
        "rep_bioenergy -> bioenergy (MWh/y): {0:.4f}".format(
            float(rep_bioenergy["sum"])
        )
    )
    print(
        "rep_sum_a_stumpage_value -> annual stumpage value"
        + " (EUR/y): {0:.4f}".format(
            float(rep_a_stumpage_value["sum"])
        )
    )
    print(
        "rep_ave_stumpage_value -> average stumpage value "
        + "(EUR/ha): {0:.4f}".format(
            float(rep_stump_value_ha["mean"])
        )
    )
    print(
        "rep_ave_a_stumpage_value -> average annual stumpage"
        + " value (EUR/ha*y-1): {0:.4f}".format(
            float(rep_a_stump_value_ha["mean"])
        )
    )
    print(
        "rep_annual_avoided_emission -> annual avoided "
        + "emissions (t): {0:.4f}".format(
            float(rep_annual_avoided_emission["sum"])
        )
    )
    print("\n---------------------------\n")
    if opts["ind1"] != "":
        print(
            "rep_"
            + opts["ind1"]
            + " -> annual value of wood on annual yield (euro/m3)"
            + ": {0:.4f}".format(
                float(rep_ind1["max"])
            )
        )
    if opts["ind2"] != "":
        print(
            "rep_"
            + opts["ind2"]
            + " -> carbon dioxide emission per cubic meter (t/m3)"
            + ": {0:.4f}".format(
                float(rep_ind2["max"])
            )
        )
    if opts["ind3"] != "":
        print(
            "rep_"
            + opts["ind3"]
            + " -> general index of forest surface utilization "
            + "(ha/y): {0:.4f}".format(
                float(rep_ind3["max"])
            )
        )
    if opts["ind4"] != "":
        print(
            "rep_"
            + opts["ind4"]
            + " -> general index of re-use (m3*y) sum"
            + ": {0:.4f}".format(
                float(rep_ind4["max"])
            )
        )
    if opts["ind5"] != "":
        print(
            "rep_"
            + opts["ind5"]
            + " -> potential value of wood on real value "
            + "(euro/euro): {0:.4f}".format(
                float(rep_ind5["max"])
            )
        )
    if opts["ind6"] != "":
        print(
            "rep_"
            + opts["ind6"]
            + " -> percentual of wood residuals used in "
            + "bioenergy production (%): {0:.4f}".format(
                float(rep_ind6["max"])
            )
        )
    if opts["ind7"] != "":
        print(
            "rep_"
            + opts["ind7"]
            + " -> avoided CO2 per unit of energy produced"
            + " (gCO2 /kWh): {0:.4f}".format(
                float(rep_ind7["max"])
            )
        )

    print("dist_tot -> AMC map: {0:.4f}".format(float(rep_dip["mean"])))
    print("\n#############################\n")

    if flgs["r"] == True:
        remove_map(opts, flgs, dic1, dic2, dic_ind2)


if __name__ == "__main__":
    main(*parser())
