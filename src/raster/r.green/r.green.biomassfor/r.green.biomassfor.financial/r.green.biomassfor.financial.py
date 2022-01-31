#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#!/usr/bin/env python
#
# MODULE:      r.green.biomassfor.economic
# AUTHOR(S):   Sandro Sacchelli, Francesco Geri
#              Converted to Python by Pietro Zambelli, Francesco Geri,
#              reviewed by Marco Ciolli
#              Last version rewritten by Giulia Garegnani, Gianluca Grilli
# PURPOSE:     Calculates the economic value of a forests in terms of bioenergy assortments
# COPYRIGHT:   (C) 2013 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
# default values for prices1: 79.54,81.33,69.51,193,83.45
# %Module
# % description: Estimates bioenergy that can be collected to supply heating plants or biomass logistic centres and that is associated with a positive net revenue for the entire production process
# % keyword: raster
# % keyword: biomass
# % overwrite: yes
# %End
# %option G_OPT_V_INPUT
# % key: forest
# % type: string
# % description: Name of vector parcel map
# % label: Name of vector parcel map
# % required : yes
# %end
# %option G_OPT_V_INPUT
# % key: dhp
# % type: string
# % description: Name of vector district heating points
# % label: Name of vector district heating points
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
# %option
# % key: forest_column_wood_price
# % type: string
# % description: Vector field of wood prices
# % required : yes
# %end
# %option G_OPT_V_INPUT
# % key: forest_roads
# % type: string
# % description: Vector map of forest roads
# % label: Vector map of forest roads
# % required : yes
# %end
# %option G_OPT_V_INPUT
# % key: main_roads
# % type: string
# % description: Vector map of main roads
# % label: Vector map of main roads
# % required : yes
# %end
# %option G_OPT_R_ELEV
# % required: yes
# %end
# %option G_OPT_R_INPUT
# % key: technical_bioenergy
# % type: string
# % description: Total technical biomass potential [MWh/year]
# % guisection: Opt files
# % required : no
# %end
# %option G_OPT_R_INPUT
# % key: tech_bioc
# % type: string
# % description: Technical biomass potential for coppices [MWh/year]
# % guisection: Opt files
# % required : no
# %end
# %option G_OPT_R_INPUT
# % key: tech_biohf
# % type: string
# % description: Technical biomass potential in high forest [MWh/year]
# % guisection: Opt files
# % required : no
# %end
# %option G_OPT_R_INPUT
# % key: soilp2_map
# % type: string
# % description: Soil production map
# % guisection: Opt files
# % required : no
# %end
# %option G_OPT_R_INPUT
# % key: tree_diam
# % type: string
# % description: Average tree diameter map
# % guisection: Opt files
# % required : no
# %end
# %option G_OPT_R_INPUT
# % key: tree_vol
# % type: string
# % description: Average tree volume map
# % guisection: Opt files
# % required : no
# %end
# %option G_OPT_V_INPUT
# % key: rivers
# % type: string
# % description: Vector map of rivers
# % label: Vector map of rivers
# % guisection: Opt files
# % required : no
# %end
# %option G_OPT_V_INPUT
# % key: lakes
# % type: string
# % description: Vector map of lakes
# % label: Vector map of lakes
# % guisection: Opt files
# % required : no
# %end
# %option
# % key: forest_column_roughness
# % type: string
# % description: Vector field of roughness
# % guisection: Opt files
# %end
# %option
# % key: slp_min_cc
# % type: double
# % description: Percent slope lower limit with Cable Crane
# % answer: 30.
# % guisection: Technical data
# %end
# %option
# % key: slp_max_cc
# % type: double
# % description: Percent slope higher limit with Cable Crane
# % answer: 100.
# % guisection: Technical data
# %end
# %option
# % key: dist_max_cc
# % type: double
# % description: Maximum distance with Cable Crane
# % answer: 800.
# % guisection: Technical data
# %end
# %option
# % key: slp_max_fw
# % type: double
# % description: Percent slope higher limit with Forwarder
# % answer: 30.
# % guisection: Technical data
# %end
# %option
# % key: dist_max_fw
# % type: double
# % description: Maximum distance with Forwarder
# % answer: 600.
# % guisection: Technical data
# %end
# %option
# % key: slp_max_cop
# % type: double
# % description: Percent slope higher limit with other techniques for Coppices
# % answer: 30.
# % guisection: Technical data
# %end
# %option
# % key: dist_max_cop
# % type: double
# % description: Maximum distance with other techniques for Coppices
# % answer: 600.
# % guisection: Technical data
# %end
# %option
# % key: price_energy_woodchips
# % type: double
# % description: Price for energy from woodchips EUR/MWh
# % answer: 19.50
# % guisection: Prices
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
# % answer: 87.42
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
# % answer: 111.44
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
# % key: cost_chipping
# % type: double
# % description: Chipping cost EUR/h
# % answer: 150.87
# % guisection: Costs
# %end
# %option
# % key: cost_transport
# % type: double
# % description: Transport with truck EUR/h
# % answer: 64.90
# % guisection: Costs
# %end
# %option
# % key: ton_tops_hf
# % type: double
# % description: BEF for tops and branches in high forest [ton/m3]
# % answer: 0.25
# % guisection: Forest
# %end
# %option
# % key: ton_vol_hf
# % type: double
# % description: BEF for the whole tree in high forest (tops, branches and stem) in ton/m3
# % answer: 1
# % guisection: Forest
# %end
# %option
# % key: ton_tops_cop
# % type: double
# % description: BEF for tops and branches for Coppices in ton/m3
# % answer: 0.28
# % guisection: Forest
# %end
# %flag
# % key: r
# % description: Remove all operational maps
# %end
# %option G_OPT_R_OUTPUT
# % key: econ_bioenergy
# % type: string
# % key_desc: name
# % description: Name of raster map with the financial potential of bioenergy [Mwh/year]
# % required: yes
# % guisection: Output maps
# %end
# %option G_OPT_R_OUTPUT
# % key: net_revenues
# % type: string
# % key_desc: name
# % description: Name of raster map with the net present value [EUR/year]
# % required: yes
# % answer: net_revenues
# % guisection: Output maps
# %end
# %option G_OPT_R_OUTPUT
# % key: total_revenues
# % type: string
# % key_desc: name
# % description: Name of raster map with the total revenues [EUR/year]
# % required: no
# % guisection: Output maps
# %end
# %option G_OPT_R_OUTPUT
# % key: total_cost
# % type: string
# % key_desc: name
# % description: Name of raster map with the total cost [EUR/year]
# % required: no
# % guisection: Output maps
# %end
# %option G_OPT_R_OUTPUT
# % key: econ_bioenergyhf
# % type: string
# % key_desc: name
# % description: Name of raster map with the financial potential of bioenergy in high forest [Mwh/year]
# % required: no
# % guisection: Output maps
# %end
# %option G_OPT_R_OUTPUT
# % key: econ_bioenergyc
# % type: string
# % key_desc: name
# % description: Name of raster map with the financial potential of bioenergy for coppices[Mwh/year]
# % required: no
# % guisection: Output maps
# %end

import atexit
import os

from grass.pygrass.modules.shortcuts import raster as r
from grass.script.core import parser, run_command, warning
from grass.script.utils import set_path

try:
    # set python path to the shared r.green libraries
    set_path("r.green", "libforest", "..")
    set_path("r.green", "libgreen", os.path.join("..", ".."))
    from libforest.harvesting import combination
    from libforest.harvesting import slope_computation, yield_pix_process
    from libgreen.utils import cleanup
    from libgreen.utils import sel_columns

    # TODO: check the required column
    # from libgreen.checkparameter import check_required_columns,
    # exception2error
    from libforest.financial import revenues, productivity
    from libforest.financial import costs, net_revenues
except ImportError:
    warning("libgreen and libforest not in the python path!")


def main(opts, flgs):
    pid = os.getpid()
    pat = "tmprgreen_%i_*" % pid
    DEBUG = False
    # FIXME: debug from flag
    atexit.register(cleanup, pattern=pat, debug=DEBUG)

    forest = opts["forest"]

    forest_roads = opts["forest_roads"]
    main_roads = opts["main_roads"]

    ######## start import and convert ########
    ll = [x for x in opts.keys() if sel_columns(x, "forest_column")]
    for key in ll:
        try:
            run_command(
                "v.to.rast",
                input=forest,
                output=("tmprgreen_%i_%s" % (pid, key[14:])),
                use="attr",
                attrcolumn=opts[key],
                overwrite=True,
            )
            # FIXME: not to show the ERROR
            run_command("r.null", map=("tmprgreen_%i_%s" % (pid, key[14:])), null=0)
        except Exception:
            warning("no column %s selectd, values set to 0" % key)
            run_command(
                "r.mapcalc",
                overwrite=True,
                expression=("%s=0" % "tmprgreen_%i_%s" % (pid, key[14:])),
            )

    run_command(
        "v.to.rast",
        input=forest_roads,
        output=("tmprgreen_%i_forest_roads" % pid),
        use="val",
        overwrite=True,
    )
    run_command(
        "v.to.rast",
        input=main_roads,
        output=("tmprgreen_%i_main_roads" % pid),
        use="val",
        overwrite=True,
    )
    # FIXME: yiel surface can be computed by the code, plan surface or real?
    # FIXME: this map can be create here
    yield_pix = "tmprgreen_%i_yield_pix" % pid
    expr = "{pix} = {yield_}/{yield_surface}*" "((ewres()*nsres())/10000)"
    r.mapcalc(
        expr.format(
            pix=yield_pix,
            yield_=("tmprgreen_%i_yield" % pid),
            yield_surface="tmprgreen_%i_yield_surface" % pid,
        ),
        overwrite=True,
    )
    # TODO: add r.null
    ######## end import and convert ########
    dic = {"tree_diam": 35, "tree_vol": 3, "soilp2_map": 0.7}
    for key, val in dic.items():
        if not (opts[key]):
            warning("Not %s map, value set to %f" % (key, val))
            output = "tmprgreen_%i_%s" % (pid, key)
            run_command(
                "r.mapcalc", overwrite=True, expression=("%s=%f" % (output, val))
            )
    # create combination maps to avoid if construction
    m1t1, m1t2, m1, m2, not2 = combination(
        "tmprgreen_%i_management" % pid, "tmprgreen_%i_treatment" % pid
    )

    slope_computation(opts["elevation"])

    if opts["technical_bioenergy"] and opts["tech_bioc"] and opts["tech_biohf"]:
        technical_bioenergy = opts["technical_bioenergy"]
        tech_bioC = opts["tech_bioc"]
        tech_bioHF = opts["tech_biohf"]
        technical_surface = "tmprgreen_%i_technical_surface" % pid
        expr = "{technical_surface} = if({technical_bioenergy}, 1, 0)"
        r.mapcalc(
            expr.format(
                technical_surface=technical_surface,
                technical_bioenergy=technical_bioenergy,
            ),
            overwrite=True,
        )

    else:
        # FIXME: call directly the biomassfor.technical module
        out = yield_pix_process(
            opts=opts,
            vector_forest=forest,
            yield_=("tmprgreen_%i_yield" % pid),
            yield_surface=("tmprgreen_%i_yield_surface" % pid),
            rivers=opts["rivers"],
            lakes=opts["lakes"],
            forest_roads=("tmprgreen_%i_forest_roads" % pid),
            m1t1=m1t1,
            m1t2=m1t2,
            m1=m1,
            m2=m2,
            roughness=("tmprgreen_%i_roughness" % pid),
        )
        technical_bioenergy, tech_bioC, tech_bioHF = out

    total_revenues = revenues(
        opts=opts,
        yield_surface=("tmprgreen_%i_yield_surface" % pid),
        m1t1=m1t1,
        m1t2=m1t2,
        m1=m1,
        m2=m2,
        forest=forest,
        yield_=("tmprgreen_%i_yield" % pid),
        technical_bioenergy=technical_bioenergy,
    )

    dic1, dic2 = productivity(
        opts=opts,
        m1t1=m1t1,
        m1t2=m1t2,
        m1=m1,
        m2=m2,
        not2=not2,
        soilp2_map=("tmprgreen_%i_soilp2_map" % pid),
        tree_diam=("tmprgreen_%i_tree_diam" % pid),
        tree_vol=("tmprgreen_%i_tree_vol" % pid),
        forest_roads=("tmprgreen_%i_forest_roads" % pid),
        main_roads=("tmprgreen_%i_main_roads" % pid),
    )
    total_costs = costs(
        opts,
        total_revenues=total_revenues,
        dic1=dic1,
        dic2=dic2,
        yield_pix="yield_pix1",
    )
    net_revenues(
        opts=opts,
        total_revenues=total_revenues,
        technical_bioenergy=technical_bioenergy,
        tech_bioC=tech_bioC,
        tech_bioHF=tech_bioHF,
        total_costs=total_costs,
    )


# TODO: create a function based on r.univar or delete it
#    with RasterRow(econ_bioenergy) as pT:
#        T = np.array(pT)
#
#    print "Resulted maps: "+output+"_econ_bioenergyHF, "+output+"_econ_bioenergyC, "+output+"_econ_bioenergy"
#    print ("Total bioenergy stimated (Mwh): %.2f" % np.nansum(T))


if __name__ == "__main__":
    main(*parser())
