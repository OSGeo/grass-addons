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
#%Module
#% description: Estimates bioenergy that can be collected to supply heating plants or biomass logistic centres and that is associated with a positive net revenue for the entire production process
#% keyword: raster
#% keyword: biomass
#% overwrite: yes
#%End
#%option G_OPT_V_INPUT
#% key: forest
#% type: string
#% description: Name of vector parcel map
#% label: Name of vector parcel map
#% required : yes
#%end
#%option G_OPT_V_INPUT
#% key: dhp
#% type: string
#% description: Name of vector district heating points
#% label: Name of vector district heating points
#% required : yes
#%end
#%option
#% key: forest_column_yield
#% type: string
#% description: Vector field of yield
#% required : yes
#%end
#%option
#% key: forest_column_yield_surface
#% type: string
#% description: Vector field of stand surface (ha)
#% required : yes
#%end
#%option
#% key: forest_column_management
#% type: string
#% description: Vector field of forest management (1: high forest, 2:coppice)
#% required : yes
#%end
#%option
#% key: forest_column_treatment
#% type: string
#% description: Vector field of forest treatment (1: final felling, 2:thinning)
#% required : yes
#%end
#%option
#% key: forest_column_wood_price
#% type: string
#% description: Vector field of wood prices
#% required : yes
#%end
#%option G_OPT_V_INPUT
#% key: forest_roads
#% type: string
#% description: Vector map of forest roads
#% label: Vector map of forest roads
#% required : yes
#%end
#%option G_OPT_V_INPUT
#% key: main_roads
#% type: string
#% description: Vector map of main roads
#% label: Vector map of main roads
#% required : yes
#%end
#%option G_OPT_R_ELEV
#% required: yes
#%end
#%option G_OPT_R_INPUT
#% key: technical_bioenergy
#% type: string
#% description: Total technical biomass potential [MWh/year]
#% guisection: Opt files
#% required : no
#%end
#%option G_OPT_R_INPUT
#% key: tech_bioc
#% type: string
#% description: Technical biomass potential for coppices [MWh/year]
#% guisection: Opt files
#% required : no
#%end
#%option G_OPT_R_INPUT
#% key: tech_biohf
#% type: string
#% description: Technical biomass potential in high forest [MWh/year]
#% guisection: Opt files
#% required : no
#%end
#%option G_OPT_R_INPUT
#% key: soilp2_map
#% type: string
#% description: Soil production map
#% guisection: Opt files
#% required : no
#%end
#%option G_OPT_R_INPUT
#% key: tree_diam
#% type: string
#% description: Average tree diameter map
#% guisection: Opt files
#% required : no
#%end
#%option G_OPT_R_INPUT
#% key: tree_vol
#% type: string
#% description: Average tree volume map
#% guisection: Opt files
#% required : no
#%end
#%option G_OPT_V_INPUT
#% key: rivers
#% type: string
#% description: Vector map of rivers
#% label: Vector map of rivers
#% guisection: Opt files
#% required : no
#%end
#%option G_OPT_V_INPUT
#% key: lakes
#% type: string
#% description: Vector map of lakes
#% label: Vector map of lakes
#% guisection: Opt files
#% required : no
#%end
#%option
#% key: forest_column_roughness
#% type: string
#% description: Vector field of roughness
#% guisection: Opt files
#%end
#%option
#% key: slp_min_cc
#% type: double
#% description: Percent slope lower limit with Cable Crane
#% answer: 30.
#% guisection: Technical data
#%end
#%option
#% key: slp_max_cc
#% type: double
#% description: Percent slope higher limit with Cable Crane
#% answer: 100.
#% guisection: Technical data
#%end
#%option
#% key: dist_max_cc
#% type: double
#% description: Maximum distance with Cable Crane
#% answer: 800.
#% guisection: Technical data
#%end
#%option
#% key: slp_max_fw
#% type: double
#% description: Percent slope higher limit with Forwarder
#% answer: 30.
#% guisection: Technical data
#%end
#%option
#% key: dist_max_fw
#% type: double
#% description: Maximum distance with Forwarder
#% answer: 600.
#% guisection: Technical data
#%end
#%option
#% key: slp_max_cop
#% type: double
#% description: Percent slope higher limit with other techniques for Coppices
#% answer: 30.
#% guisection: Technical data
#%end
#%option
#% key: dist_max_cop
#% type: double
#% description: Maximum distance with other techniques for Coppices
#% answer: 600.
#% guisection: Technical data
#%end
#%option
#% key: price_energy_woodchips
#% type: double
#% description: Price for energy from woodchips €/MWh
#% answer: 19.50
#% guisection: Prices
#%end
#%option
#% key: cost_chainsaw
#% type: double
#% description: Felling and/or felling-processing cost with chainsaw €/h
#% answer: 13.17
#% guisection: Costs
#%end
#%option
#% key: cost_processor
#% type: double
#% description: Processing cost with processor €/h
#% answer: 87.42
#% guisection: Costs
#%end
#%option
#% key: cost_harvester
#% type: double
#% description: Felling and processing cost with harvester €/h
#% answer: 96.33
#% guisection: Costs
#%end
#%option
#% key: cost_cablehf
#% type: double
#% description: Extraction cost with high power cable crane €/h
#% answer: 111.44
#% guisection: Costs
#%end
#%option
#% key: cost_cablec
#% type: double
#% description: Extraction cost with medium power cable crane €/h
#% answer: 104.31
#% guisection: Costs
#%end
#%option
#% key: cost_forwarder
#% type: double
#% description: Extraction cost with forwarder €/h
#% answer: 70.70
#% guisection: Costs
#%end
#%option
#% key: cost_skidder
#% type: double
#% description: Extraction cost with skidder €/h
#% answer: 64.36
#% guisection: Costs
#%end
#%option
#% key: cost_chipping
#% type: double
#% description: Chipping cost €/h
#% answer: 150.87
#% guisection: Costs
#%end
#%option
#% key: cost_transport
#% type: double
#% description: Transport with truck €/h
#% answer: 64.90
#% guisection: Costs
#%end
#%option
#% key: ton_tops_hf
#% type: double
#% description: BEF for tops and branches in high forest [ton/m3]
#% answer: 0.25
#% guisection: Forest
#%end
#%option
#% key: ton_vol_hf
#% type: double
#% description: BEF for the whole tree in high forest (tops, branches and stem) in ton/m³
#% answer: 1
#% guisection: Plant
#%end
#%option
#% key: ton_tops_cop
#% type: double
#% description: BEF for tops and branches for Coppices in ton/m³
#% answer: 0.30
#% guisection: Forest
#%end
#%flag
#% key: r
#% description: Remove all operational maps
#%end
#%option G_OPT_R_OUTPUT
#% key: econ_bioenergy
#% type: string
#% key_desc: name
#% description: Name of raster map with the financial potential of bioenergy [Mwh/year]
#% required: yes
#% guisection: Output maps
#%end
#%option G_OPT_R_OUTPUT
#% key: net_revenues
#% type: string
#% key_desc: name
#% description: Name of raster map with the net present value [€/year]
#% required: yes
#% answer: net_revenues
#% guisection: Output maps
#%end
#%option G_OPT_R_OUTPUT
#% key: total_revenues
#% type: string
#% key_desc: name
#% description: Name of raster map with the total revenues [€/year]
#% required: no
#% guisection: Output maps
#%end
#%option G_OPT_R_OUTPUT
#% key: total_cost
#% type: string
#% key_desc: name
#% description: Name of raster map with the total cost [€/year]
#% required: no
#% guisection: Output maps
#%end
#%option G_OPT_R_OUTPUT
#% key: econ_bioenergyhf
#% type: string
#% key_desc: name
#% description: Name of raster map with the financial potential of bioenergy in high forest [Mwh/year]
#% required: no
#% guisection: Output maps
#%end
#%option G_OPT_R_OUTPUT
#% key: econ_bioenergyc
#% type: string
#% key_desc: name
#% description: Name of raster map with the financial potential of bioenergy for coppices[Mwh/year]
#% required: no
#% guisection: Output maps
#%end

import grass.script as grass
from grass.script.core import run_command, parser, overwrite, warning
from grass.pygrass.raster import RasterRow
from grass.pygrass.modules.shortcuts import raster as r
import numpy as np
import os
import atexit
from grass.pygrass.utils import set_path
set_path('r.green', 'libhydro', '..')
set_path('r.green', 'libgreen', os.path.join('..', '..'))
# finally import the module in the library
from libgreen.utils import cleanup

ow = overwrite()


def conmbination(management, treatment):
    pid = os.getpid()
    # set combination to avoid several if
    m1t1 = "tmprgreen_%i_m1t1" % pid
    exp = ("{combination}=if(({management}=={c1} && ({treatment}=={c2}"
           "||{treatment}==99999)),1,0)")
    r.mapcalc(exp.format(combination=m1t1,
                         management=management,
                         c1=1,
                         treatment=treatment,
                         c2=1),
              overwrite=ow)
    run_command("r.null", map=m1t1, null=0)
    m1t2 = "tmprgreen_%i_m1t2" % pid
    exp = ("{combination}=if(({management}=={c1} && {treatment}=={c2}),1,0)")
    r.mapcalc(exp.format(combination=m1t2,
                         management=management,
                         c1=1,
                         treatment=treatment,
                         c2=2),
              overwrite=ow)
    run_command("r.null", map=m1t2, null=0)
    m2 = "tmprgreen_%i_m2" % pid
    exp = ("{combination}=if({management}=={c1},1,0)")
    r.mapcalc(exp.format(combination=m2,
                         management=management,
                         c1=2),
              overwrite=ow)
    run_command("r.null", map=m2, null=0)
    m1 = "tmprgreen_%i_m1" % pid
    exp = ("{combination}=if({management}=={c1},1,0)")
    r.mapcalc(exp.format(combination=m1,
                         management=management,
                         c1=1),
              overwrite=ow)
    run_command("r.null", map=m1, null=0)
    not2 = "tmprgreen_%i_not2" % pid
    exp = ("{combination}=if(({treatment}=={c1} && {treatment}=={c2}),1,0)")
    r.mapcalc(exp.format(combination=not2,
                         c1=1,
                         treatment=treatment,
                         c2=99999),
              overwrite=ow)
    run_command("r.null", map=not2, null=0)
    #TODO: try to remove all the r.nulle, since I
    # have done it at the beginning
    return m1t1, m1t2, m1, m2, not2


def slope_computation(opts):
    pid = os.getpid()
    tmp_slope = 'tmprgreen_%i_slope' % pid
    tmp_slope_deg = 'tmprgreen_%i_slope_deg' % pid
    run_command("r.slope.aspect", overwrite=ow,
                elevation=opts['elevation'], slope=tmp_slope, format="percent")
    run_command("r.slope.aspect", overwrite=ow,
                elevation=opts['elevation'], slope=tmp_slope_deg)


def yield_pix_process(opts, vector_forest, yield_, yield_surface,
                      rivers, lakes, forest_roads, m1, m2,
                      m1t1, m1t2, roughness):
    pid = os.getpid()
    tmp_slope = 'tmprgreen_%i_slope' % pid
    tmp_slope_deg = 'tmprgreen_%i_slope_deg' % pid
    technical_surface = "tmprgreen_%i_technical_surface" % pid
    cable_crane_extraction = "cable_crane_extraction"
    forwarder_extraction = "forwarder_extraction"
    other_extraction = "other_extraction"

    run_command("r.param.scale", overwrite=ow,
                input=opts['elevation'], output="morphometric_features",
                size=3, method="feature")
    # peaks have an higher cost/distance in order not to change the valley

    expr = "{pix_cross} = ((ewres()+nsres())/2)/ cos({tmp_slope_deg})"
    r.mapcalc(expr.format(pix_cross=('tmprgreen_%i_pix_cross' % pid),
                          tmp_slope_deg=tmp_slope_deg),
              overwrite=ow)
    #FIXME: yield surface is a plan surface and not the real one of the forest
    #unit, do I compute the real one?#
    # if yield_pix1 == 0 then yield is 0, then I can use yield or
    #  use yeld_pix but I will compute it only once in the code
    run_command("r.mapcalc", overwrite=ow,
                expression=('yield_pix1 = (' + yield_+'/' +
                            yield_surface+')*((ewres()*nsres())/10000)'))

    run_command("r.null", map="yield_pix1", null=0)
    run_command("r.null", map="morphometric_features", null=0)

# FIXME: initial control on the yield in order to verify if it is positive
#    exprmap = ("{frict_surf_extr} = {pix_cross} + if(yield_pix1<=0, 99999)"
#               "+ if({morphometric_features}==6, 99999)")

    exprmap = ("{frict_surf_extr} = {pix_cross}"
               "+ if({morphometric_features}==6, 99999)")
    if rivers:
        run_command("v.to.rast", input=rivers, output=('tmprgreen_%i_rivers'
                                                       % pid),
                    use="val", value=99999, overwrite=True)
        run_command("r.null", map=rivers, null=0)
        exprmap += "+ %s" % ('tmprgreen_%i_rivers' % pid)

    if lakes:
        run_command("v.to.rast", input=lakes, output=('tmprgreen_%i_lakes'
                                                      % pid),
                    use="val", value=99999, overwrite=True)
        run_command("r.null", map=lakes, null=0)
        exprmap += '+ %s' % ('tmprgreen_%i_lakes' % pid)

    frict_surf_extr = 'tmprgreen_%i_frict_surf_extr' % pid
    extr_dist = 'tmprgreen_%i_extr_dist' % pid
    r.mapcalc(exprmap.format(frict_surf_extr=frict_surf_extr,
                             pix_cross=('tmprgreen_%i_pix_cross' % pid),
                             morphometric_features='morphometric_features',
                             ),
              overwrite=ow)

    run_command("r.cost", overwrite=ow,
                input=frict_surf_extr, output=extr_dist,
                stop_points=vector_forest,
                start_rast='tmprgreen_%i_forest_roads' % pid,
                max_cost=1500)
    slp_min_cc = opts['slp_min_cc']
    slp_max_cc = opts['slp_max_cc']
    dist_max_cc = opts['dist_max_cc']
    ccextr = ("{cable_crane_extraction} = if({yield_} >0 && {tmp_slope}"
              "> {slp_min_cc} && {tmp_slope} <= {slp_max_cc} && {extr_dist}<"
              "{dist_max_cc} , 1)")
    r.mapcalc(ccextr.format(cable_crane_extraction=cable_crane_extraction,
                            yield_=yield_, tmp_slope=tmp_slope,
                            slp_min_cc=slp_min_cc, slp_max_cc=slp_max_cc,
                            dist_max_cc=dist_max_cc,
                            extr_dist=extr_dist),
              overwrite=ow)

    fwextr = ("{forwarder_extraction} = if({yield_}>0 && {tmp_slope}<="
              "{slp_max_fw} && ({roughness} ==0 ||"
              "{roughness}==1 || {roughness}==99999) &&"
              "{extr_dist}<{dist_max_fw}, {m1}*1)")

    r.mapcalc(fwextr.format(forwarder_extraction=forwarder_extraction,
                            yield_=yield_, tmp_slope=tmp_slope,
                            slp_max_fw=opts['slp_max_fw'],
                            m1=m1,
                            roughness=roughness,
                            dist_max_fw=opts['dist_max_fw'],
                            extr_dist=extr_dist),
              overwrite=ow)

    oextr = ("{other_extraction} = if({yield_}>0 &&"
             "{tmp_slope}<={slp_max_cop} &&"
             "({roughness}==0 || {roughness}==1 ||"
             "{roughness}==99999) && {extr_dist}< {dist_max_cop}, {m2}*1)")

    r.mapcalc(oextr.format(other_extraction=other_extraction,
                           yield_=yield_, tmp_slope=tmp_slope,
                           slp_max_cop=opts['slp_max_cop'],
                           m2=m2, roughness=roughness,
                           dist_max_cop=opts['dist_max_cop'],
                           extr_dist=extr_dist),
              overwrite=ow)

    run_command("r.null", map=cable_crane_extraction, null=0)
    run_command("r.null", map=forwarder_extraction, null=0)
    run_command("r.null", map=other_extraction, null=0)
# FIXME: or instead of plus
    expression = ("{technical_surface} = {cable_crane_extraction} +"
                  "{forwarder_extraction} + {other_extraction}")
    r.mapcalc(expression.format(technical_surface=technical_surface,
                                cable_crane_extraction=cable_crane_extraction,
                                forwarder_extraction=forwarder_extraction,
                                other_extraction=other_extraction),
              overwrite=ow)

    run_command("r.null", map=technical_surface, null=0)
# FIXME: in my opinion we cannot sum two different energy coefficients
# is the energy_vol_hf including the energy_tops?
    ehf = ("{tech_bioHF} = {technical_surface}*{yield_pix}*"
           "({m1t1}*{ton_tops_hf}+"
           "{m1t2}*({ton_vol_hf}+{ton_tops_hf}))")
    tech_bioHF = ('tmprgreen_%i_tech_bioenergyHF' % pid)
    r.mapcalc(ehf.format(tech_bioHF=tech_bioHF,
                         technical_surface=technical_surface,
                         m1t1=m1t1, m1t2=m1t2,
                         yield_pix='yield_pix1',
                         ton_tops_hf=opts['ton_tops_hf'],
                         ton_vol_hf=opts['ton_vol_hf']),
              overwrite=ow)
    tech_bioC = 'tmprgreen_%i_tech_bioenergyC' % pid
    ecc = ("{tech_bioC} = {technical_surface}*{m2}*{yield_pix}"
           "*{ton_tops_cop}")
    r.mapcalc(ecc.format(tech_bioC=tech_bioC,
                         technical_surface=technical_surface,
                         m2=m2,
                         yield_pix='yield_pix1',
                         ton_tops_cop=opts['ton_tops_cop']),
              overwrite=ow)
    technical_bioenergy = "tmprgreen_%i_techbio" % pid
    exp = "{technical_bioenergy}={tech_bioHF}+{tech_bioC}"
    r.mapcalc(exp.format(technical_bioenergy=technical_bioenergy,
                         tech_bioC=tech_bioC,
                         tech_bioHF=tech_bioHF),
              overwrite=ow)

    run_command("r.null", map=technical_bioenergy, null=0)

    with RasterRow(technical_bioenergy) as pT:
        T = np.array(pT)
    print ("Tech bioenergy stimated (ton): %.2f" % np.nansum(T))
    return technical_bioenergy, tech_bioC, tech_bioHF


def revenues(opts, yield_surface, m1t1, m1t2, m1, m2,
             forest, yield_, technical_bioenergy):
    # Calculate revenues
    pid = os.getpid()
    #FIXME: tmp_yield is the raster yield in the other sections of the module
    tmp_yield = 'tmprgreen_%i_yield' % pid
    tmp_wood = 'tmprgreen_%i_wood_price' % pid
    tmp_rev_wood = 'tmprgreen_%i_rev_wood' % pid

    exprpix = '%s=%s*%s/%s*(ewres()*nsres()/10000)' % (tmp_rev_wood, tmp_wood,
                                                       tmp_yield,
                                                       yield_surface)
    run_command("r.mapcalc", overwrite=ow, expression=exprpix)
    # FIXME: Does the coppice produces timber?
    tr1 = ("{total_revenues} ="
           "{technical_surface}*(({m1t1}|||{m2})*({tmp_rev_wood} +"
           "{technical_bioenergy}*{price_energy_woodchips})+"
           "{m1t2}*{technical_bioenergy}*{price_energy_woodchips})")

    r.mapcalc(tr1.format(total_revenues=("tmprgreen_%i_total_revenues" % pid),
                         technical_surface=('tmprgreen_%i_technical_surface'
                                            % pid),
                         m1t1=m1t1, m2=m2, m1t2=m1t2,
                         tmp_rev_wood=tmp_rev_wood,
                         technical_bioenergy=technical_bioenergy,
                         price_energy_woodchips=opts['price_energy_woodchips']
                         ),
              overwrite=ow)
    return ("tmprgreen_%i_total_revenues" % pid)


def productivity(opts,
                 m1t1, m1t2, m1, m2, not2, soilp2_map,
                 tree_diam, tree_vol, forest_roads, main_roads):
    # return a dictionary with the productivity maps as key and
    # the cost form the GUI as value
#    if tree_diam == '':
#        tree_diam="99999"
#    if tree_vol == '':
#        tree_vol="9.999"
#    if soilp2_map == '':
#        soilp2_map="99999"
    pid = os.getpid()
    dhp = opts['dhp']
    fell_productHFtr1 = "tmprgreen_%i_fell_productHFtr1" % pid
    fell_productHFtr2 = "tmprgreen_%i_fell_productHFtr2" % pid
    fell_proc_productC = "tmprgreen_%i_fell_proc_productC" % pid
    proc_productHFtr1 = "tmprgreen_%i_proc_productHFtr1" % pid
    fell_proc_productHFtr1 = "tmprgreen_%i_fell_proc_productHFtr1" % pid
    fell_proc_productHFtr2 = "tmprgreen_%i_fell_proc_productHFtr2" % pid
    chipp_prod = "tmprgreen_%i_chipp_prod" % pid
    extr_dist = "tmprgreen_%i_extr_dist" % pid
    extr_product_cableHF = "tmprgreen_%i_extr_product_cableHF" % pid
    extr_product_cableC = "tmprgreen_%i_extr_product_cableC" % pid
    extr_product_forw = "tmprgreen_%i_extr_product_forw" % pid
    extr_product_other = "tmprgreen_%i_extr_product_other" % pid
    transport_prod = "tmprgreen_%i_transport_prod" % pid
    dic1 = {fell_productHFtr1: opts['cost_chainsaw'],
            fell_productHFtr2: opts['cost_chainsaw'],
            fell_proc_productC: opts['cost_chainsaw'],
            proc_productHFtr1: opts['cost_processor'],
            fell_proc_productHFtr1: opts['cost_harvester'],
            fell_proc_productHFtr2: opts['cost_harvester'],
            extr_product_cableHF: opts['cost_cablehf'],
            extr_product_cableC: opts['cost_cablec'],
            extr_product_forw: opts['cost_forwarder'],
            extr_product_other: opts['cost_skidder']}
    dic2 = {chipp_prod: opts['cost_chipping'],
            transport_prod: opts['cost_transport']}
    # Calculate productivity
    #FIXME:in my opinion is better to exclude area with negative slope!!!
    expression = "{tmp_slope}=if({tmp_slope}<=100,{tmp_slope},100)"
    r.mapcalc(expression.format(tmp_slope="tmprgreen_%i_slope" % pid),
              overwrite=ow)
    #view the paper appendix for the formulas
    expr = ("{fell_productHFtr1} = {mt}*{cable_crane_extraction}"
            "*(42-2.6*{tree_diam})/(-20.0)*1.65*(1-{slope___}/100.0)")
    r.mapcalc(expr.format(fell_productHFtr1=fell_productHFtr1,
                          mt=m1t1,
                          cable_crane_extraction="cable_crane_extraction",
                          tree_diam="tmprgreen_%i_tree_diam" % pid,
                          slope___='tmprgreen_%i_slope' % pid), overwrite=ow)
    run_command("r.null", map=fell_productHFtr1, null=0)

    expr = ("{fell_productHFtr2} = {mt}*{cable_crane_extraction}*"
            "(42-2.6*{tree_diam})/(-20)*1.65*(1-(1000-90*{slope}/(-80))/100)")
    r.mapcalc(expr.format(fell_productHFtr2=fell_productHFtr2,
                          mt=m1t2,
                          cable_crane_extraction="cable_crane_extraction",
                          tree_diam="tmprgreen_%i_tree_diam" % pid,
                          slope='tmprgreen_%i_slope' % pid), overwrite=ow)
    run_command("r.null", map=fell_productHFtr2, null=0)
    #FIXME: it is different from the paper, to check
    expr = ("{fell_proc_productC} = {m2}*"
            "(0.3-1.1*{soilp2_map})/(-4)*(1-{slope}/100)")
    r.mapcalc(expr.format(fell_proc_productC=fell_proc_productC,
                          m2=m2,
                          soilp2_map="tmprgreen_%i_soilp2_map" % pid,
                          slope='tmprgreen_%i_slope' % pid), overwrite=ow)
    run_command("r.null", map=fell_proc_productC, null=0)

    ###### check fell_proc_productC ######
    #9999: default value, if is present take into the process
    #the average value (in case of fertility is 33) Giulia is it 3?

    expr = ("{proc_productHFtr1} = {mt}*{cable_crane_extraction}"
            "*0.363*{tree_diam}^1.116")
    r.mapcalc(expr.format(proc_productHFtr1=proc_productHFtr1,
                          mt=m1t1,
                          cable_crane_extraction="cable_crane_extraction",
                          tree_diam="tmprgreen_%i_tree_diam" % pid),
              overwrite=ow)
    run_command("r.null", map=proc_productHFtr1, null=0)
    expr = ("{out} = {mt}*{extraction}"
            "*60/({k}*"
            "exp(0.1480-0.3894*{st}+0.0002*({slope}^2)-0.2674*{sb})"
            "+1.0667+0.3094/{tree_vol}-0.1846*{perc})")
    r.mapcalc(expr.format(out=fell_proc_productHFtr1,
                          mt=m1t1,
                          extraction="forwarder_extraction",
                          k=1.5, st=2, sb=2.5,
                          tree_vol="tmprgreen_%i_tree_vol" % pid,
                          slope="tmprgreen_%i_slope" % pid,
                          perc=1),
              overwrite=ow)
    r.mapcalc(expr.format(out=fell_proc_productHFtr2,
                          mt=m1t2,
                          extraction="forwarder_extraction",
                          k=1.5, st=2, sb=2.5,
                          tree_vol="tmprgreen_%i_tree_vol" % pid,
                          slope="tmprgreen_%i_slope" % pid,
                          perc=0.8),
              overwrite=ow)
    run_command("r.null", map=fell_proc_productHFtr1, null=0)
    run_command("r.null", map=fell_proc_productHFtr2, null=0)

    expr = ("{chipp_prod} = {m1t1}*{yield_pix}/{num11}"
            "+{m1t2}*{yield_pix}/{num12}"
            "+{m2}*{yield_pix}/{num2}")
    r.mapcalc(expr.format(chipp_prod=chipp_prod,
                          yield_pix="yield_pix1",
                          m1t1=m1t1,
                          num11=34,
                          m1t2=m1t2,
                          num12=20.1,
                          m2=m2,
                          num2=45.9
                          ),
              overwrite=ow)
    run_command("r.null", map=chipp_prod, null=0)

    extr_product = {}
    extr_product[extr_product_cableHF] = [m1, 'cable_crane_extraction',
                                          149.33, extr_dist,
                                          -1.3438, 0.75]
    extr_product[extr_product_cableC] = [m2, 'cable_crane_extraction',
                                         149.33, extr_dist,
                                         -1.3438, 0.75]
    extr_product[extr_product_forw] = [1, 'forwarder_extraction',
                                       36.293, extr_dist,
                                       -1.1791, 0.6]
    extr_product[extr_product_other] = [1, 'other_extraction',
                                        36.293, extr_dist,
                                        -1.1791, 0.6]
    expr = ("{extr_product} = {m}*{extraction}"
            "*{coef1}*({extr_dist}^{expo})* {extr_dist}/8*{coef2}")
    for key, val in extr_product.items():
        r.mapcalc(expr.format(extr_product=key,
                              m=val[0],
                              extraction=val[1],
                              coef1=val[2],
                              extr_dist=val[3],
                              expo=val[4],
                              coef2=val[5]),
                  overwrite=ow)
        run_command("r.null", map=key, null=0)

    #cost of the transport distance
    #this is becouse the wood must be sell to the collection point
    #instead the residual must be brung to the heating points
    tot_roads = "tmprgreen_%i_tot_roads" % pid
    run_command("r.mapcalc", overwrite=ow,
                expression=('%s = %s ||| %s' % (tot_roads,
                                                forest_roads, main_roads)))
    run_command("r.null", map=tot_roads, null=0)

    expr = ("{frict_surf_tr}={frict_surf_extr}*not({tot_roads})"
            "*{tot_roads}*((ewres()+nsres())/2)")
    r.mapcalc(expr.format(frict_surf_tr="tmprgreen_%i_frict_surf_tr" % pid,
                          frict_surf_extr='tmprgreen_%i_frict_surf_extr' % pid,
                          tot_roads=tot_roads
                          ),
              overwrite=ow)

    transp_dist = "tmprgreen_%i_transp_dist" % pid
    extr_dist = "tmprgreen_%i_extr_dist" % pid
    try:
        tot_dist = "tmprgreen_%i_tot_dist" % pid
        run_command("r.cost", overwrite=ow,
                    input=("tmprgreen_%i_frict_surf_tr" % pid),
                    output=tot_dist,
                    stop_points=opts['forest'],
                    start_points=dhp,
                    max_cost=100000)
        run_command("r.mapcalc", overwrite=ow,
                    expression=("%s = %s - %s"
                                % (transp_dist, tot_dist, extr_dist)))
    except:
        run_command("r.mapcalc", overwrite=ow,
                    expression=('% = %s' % (transp_dist, extr_dist)))

    expr = ("{transport_prod} = {transp_dist}/30000"
            "*({not2}*({yield_pix}/32)*2 +{m1t2}*({yield_pix}*2.7/32)*2)")

    r.mapcalc(expr.format(transport_prod=transport_prod,
                          yield_pix="yield_pix1",
                          not2=not2,
                          m1t2=m1t2,
                          transp_dist="tmprgreen_%i_transp_dist" % pid
                          ),
              overwrite=ow)
    #the cost of distance transport derived by the negative of the
    # friction surface
    #the DHP must be inside the study area and connected with the road network
    #FIXME: move the DHP on the closest road
    return dic1, dic2


def costs(opts, dic1, dic2, total_revenues, yield_pix):
    # Calculate costs
    pid = os.getpid()
    expr = "{out} = {cost}/{productivity}*{yield_pix}"
    command = "tmprgreen_%i_prod_cost = " % pid
    for key, val in dic1.items():
        r.mapcalc(expr.format(out="tmprgreen_%i_cost_%s" % (pid, key),
                              yield_pix="yield_pix1",
                              cost=val,
                              productivity=key
                              ),
                  overwrite=ow)
        run_command("r.null",
                    map=("tmprgreen_%i_cost_%s" % (pid, key)),
                    null=0)
        command += "tmprgreen_%i_cost_%s+" % (pid, key)

    expr = "{out} = {cost}*{productivity}"
    for key, val in dic2.items():
        r.mapcalc(expr.format(out="tmprgreen_%i_cost_%s" % (pid, key),
                              cost=val,
                              productivity=key
                              ),
                  overwrite=ow)
        run_command("r.null",
                    map=("tmprgreen_%i_cost_%s" % (pid, key)),
                    null=0)
        command += "tmprgreen_%i_cost_%s+" % (pid, key)

    run_command("r.mapcalc", overwrite=ow,
                expression=command[:-1])
    #FIXME: the correction about negative cost have to be done in
    # the productivity single map in my opinion
    ######## patch to correct problem of negative costs #######
    prod_costs = "tmprgreen_%i_prod_cost" % pid
    expr = '{prod_costs} =  {prod_costs}>=0 ? {prod_costs} : 0'
    r.mapcalc(expr.format(prod_costs=prod_costs,
                          ),
              overwrite=ow)
    ######## end patch ##############
    direction_cost = "tmprgreen_%i_direction_cost" % pid
    administrative_cost = "tmprgreen_%i_administrative_cost" % pid
    interests = "tmprgreen_%i_interests" % pid
    run_command("r.mapcalc", overwrite=ow,
                expression='%s =  %s *0.05' % (direction_cost,
                                               prod_costs))
    run_command("r.mapcalc", overwrite=ow,
                expression=('%s =  %s*0.07' % (administrative_cost,
                                               total_revenues)))
    run_command("r.mapcalc", overwrite=ow,
                expression=('%s= (%s + %s)*0.03/4'
                            % (interests, prod_costs, administrative_cost)))

    #management and administration costs

    ###########################
    # patch for solve the absence of some optional mapss

    map_prodcost = grass.find_file(prod_costs, element='cell')
    map_admcost = grass.find_file(administrative_cost, element='cell')
    map_dircost = grass.find_file(direction_cost, element='cell')

    listcost = ''

    if map_admcost['fullname'] != '':
        listcost += map_admcost['fullname']
    if map_dircost['fullname'] != '':
        listcost += "+" + map_dircost['fullname']
    if map_prodcost['fullname'] != '':
        listcost += "+" + map_prodcost['fullname']

    # end of patch
    ###########################
    total_cost = "tmprgreen_%i_total_cost" % pid
    run_command("r.mapcalc", overwrite=ow,
                expression='%s = %s' % (total_cost, listcost))
    return total_cost


def net_revenues(opts, technical_bioenergy, tech_bioC,
                 tech_bioHF, total_revenues, total_costs):
    pid = os.getpid()
    #TODO: I will split the outputs
    # each maps is an output:
    # mandatory maps: econ_bioenergy, net_revenues
    # optional: econ_bioenergyHF, econ_bioenergyC
    #         : total_revenues, total_cost
    econ_bioenergy = opts['econ_bioenergy']
    econ_bioenergyC = (opts['econ_bioenergyc'] if opts['econ_bioenergyc']
                       else "tmprgreen_%i_econ_bioenergyc" % pid)
    econ_bioenergyHF = (opts['econ_bioenergyhf'] if opts['econ_bioenergyhf']
                        else "tmprgreen_%i_econ_bioenergyhf" % pid)
    net_revenues = opts['net_revenues']

    # Calculate net revenues and economic biomass
    run_command("r.mapcalc", overwrite=ow,
                expression='%s = %s - %s' % (net_revenues, total_revenues,
                                             total_costs))
    positive_net_revenues = "tmprgreen_%i_positive_net_revenues" % pid
    run_command("r.mapcalc", overwrite=ow,
                expression=('%s = if(%s<=0,0,1)' % (positive_net_revenues,
                                                    net_revenues)))

    #per evitare che vi siano pixel con revenues>0 sparsi
    #si riclassifica la mappa
    #in order to avoid pixel greater than 0 scattered
    #the map must be reclassified
    #considering only the aree clustered greater than 1 hectares
    economic_surface = "tmprgreen_%i_economic_surface" % pid
    run_command("r.reclass.area", overwrite=ow,
                input=positive_net_revenues,
                output=economic_surface, value=1, mode="greater")

    expr = "{econ_bioenergy} = {economic_surface}*{tech_bio}"
    r.mapcalc(expr.format(econ_bioenergy=econ_bioenergyHF,
                          economic_surface=economic_surface,
                          tech_bio=tech_bioHF
                          ),
              overwrite=ow)
    r.mapcalc(expr.format(econ_bioenergy=econ_bioenergyC,
                          economic_surface="economic_surface",
                          tech_bio=tech_bioC
                          ),
              overwrite=ow)

    econtot = ("%s = %s + %s" % (econ_bioenergy, econ_bioenergyC,
                                 econ_bioenergyHF))
    run_command("r.mapcalc", overwrite=ow, expression=econtot)


def sel_columns(element):
    if len(element) > 0:
        return (element[:13] == 'forest_column')
    return False


def main(opts, flgs):
    pid = os.getpid()
    pat = "tmprgreen_%i_*" % pid
    DEBUG = False
    #FIXME: debug from flag
    atexit.register(cleanup,
                    pattern=pat,
                    debug=DEBUG)

    forest = opts['forest']

    forest_roads = opts['forest_roads']
    main_roads = opts['main_roads']

    ######## start import and convert ########

    for key in filter(sel_columns, opts.keys()):
        try:
            run_command("v.to.rast",
                        input=forest,
                        output=('tmprgreen_%i_%s' % (pid, key[14:])),
                        use="attr",
                        attrcolumn=opts[key], overwrite=True)
            run_command("r.null", map=('tmprgreen_%i_%s' % (pid, key[14:])),
                        null=0)
        except Exception:
            warning('no column %s selectd, values set to 0' % key)
            run_command("r.mapcalc", overwrite=ow,
                        expression=('%s=0' % 'tmprgreen_%i_%s'
                                    % (pid, key[14:])))

    run_command("v.to.rast", input=forest_roads,
                output=('tmprgreen_%i_forest_roads' % pid),
                use="val", overwrite=True)
    run_command("v.to.rast", input=main_roads,
                output=('tmprgreen_%i_main_roads' % pid),
                use="val", overwrite=True)
# FIXME: yiel surface can be computed by the code, plan surface or real?
# FIXME: this map can be create here
    yield_pix = 'tmprgreen_%i_yield_pix' % pid
    expr = ("{pix} = {yield_}/{yield_surface}*"
            "((ewres()*nsres())/10000)")
    r.mapcalc(expr.format(pix=yield_pix,
                          yield_=('tmprgreen_%i_yield' % pid),
                          yield_surface='tmprgreen_%i_yield_surface' % pid),
              overwrite=True)
    # TODO: add r.null
    ######## end import and convert ########
    dic = {'tree_diam': 35, 'tree_vol': 3, 'soilp2_map': 0.7}
    for key, val in dic.items():
        if not(opts[key]):
            warning("Not %s map, value set to %f" % (key, val))
            output = 'tmprgreen_%i_%s' % (pid, key)
            run_command("r.mapcalc", overwrite=ow,
                        expression=('%s=%f' % (output, val)))
    # create combination maps to avoid if construction
    m1t1, m1t2, m1, m2, not2 = conmbination(management=
                                            ('tmprgreen_%i_management' % pid),
                                            treatment=('tmprgreen_%i_treatment'
                                                       % pid))

    slope_computation(opts)

    if (opts['technical_bioenergy'] and opts['tech_bioc']
        and opts['tech_biohf']):
            technical_bioenergy = opts['technical_bioenergy']
            tech_bioC = opts['tech_bioc']
            tech_bioHF = opts['tech_biohf']
            technical_surface = 'tmprgreen_%i_technical_surface' % pid
            expr = "{technical_surface} = if({technical_bioenergy}, 1, 0)"
            r.mapcalc(expr.format(technical_surface=technical_surface,
                                  technical_bioenergy=technical_bioenergy
                                  ),
                                  overwrite=ow)
            
    else:
        out = yield_pix_process(opts=opts, vector_forest=forest,
                                yield_=('tmprgreen_%i_yield' % pid),
                                yield_surface=('tmprgreen_%i_yield_surface' % pid),
                                rivers=opts['rivers'],
                                lakes=opts['lakes'],
                                forest_roads=('tmprgreen_%i_forest_roads' % pid),
                                m1t1=m1t1, m1t2=m1t2, m1=m1, m2=m2,
                                roughness=('tmprgreen_%i_roughness' % pid))
        technical_bioenergy, tech_bioC, tech_bioHF = out

    total_revenues = revenues(opts=opts,
                              yield_surface=('tmprgreen_%i_yield_surface'
                                             % pid),
                              m1t1=m1t1, m1t2=m1t2, m1=m1, m2=m2,
                              forest=forest,
                              yield_=('tmprgreen_%i_yield' % pid),
                              technical_bioenergy=technical_bioenergy)

    dic1, dic2 = productivity(opts=opts,
                              m1t1=m1t1, m1t2=m1t2, m1=m1, m2=m2, not2=not2,
                              soilp2_map=('tmprgreen_%i_soilp2_map' % pid),
                              tree_diam=('tmprgreen_%i_tree_diam' % pid),
                              tree_vol=('tmprgreen_%i_tree_vol' % pid),
                              forest_roads=('tmprgreen_%i_forest_roads' % pid),
                              main_roads=('tmprgreen_%i_main_roads' % pid))
    total_costs = costs(opts, total_revenues=total_revenues,
                        dic1=dic1, dic2=dic2, yield_pix="yield_pix1")
    net_revenues(opts=opts,
                 total_revenues=total_revenues,
                 technical_bioenergy=technical_bioenergy,
                 tech_bioC=tech_bioC, tech_bioHF=tech_bioHF,
                 total_costs=total_costs)

#TODO: create a function based on r.univar or delete it
#    with RasterRow(econ_bioenergy) as pT:
#        T = np.array(pT)
#
#    print "Resulted maps: "+output+"_econ_bioenergyHF, "+output+"_econ_bioenergyC, "+output+"_econ_bioenergy"
#    print ("Total bioenergy stimated (Mwh): %.2f" % np.nansum(T))


if __name__ == "__main__":
    main(*parser())
