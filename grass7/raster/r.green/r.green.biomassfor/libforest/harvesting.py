# -*- coding: utf-8 -*-
############################################################################
#
# AUTHOR(S):   Giulia Garegnani
# PURPOSE:     Libraries for the technical modul of biomassfor
#              original module developed by Francesco Geri and Pietro Zambelli
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

import os

import numpy as np

from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.raster import RasterRow
from grass.script.core import run_command


def combination(management, treatment):
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
              overwrite=True)
    run_command("r.null", map=m1t1, null=0)
    m1t2 = "tmprgreen_%i_m1t2" % pid
    exp = ("{combination}=if(({management}=={c1} && {treatment}=={c2}),1,0)")
    r.mapcalc(exp.format(combination=m1t2,
                         management=management,
                         c1=1,
                         treatment=treatment,
                         c2=2),
              overwrite=True)
    run_command("r.null", map=m1t2, null=0)
    m2 = "tmprgreen_%i_m2" % pid
    exp = ("{combination}=if({management}=={c1},1,0)")
    r.mapcalc(exp.format(combination=m2,
                         management=management,
                         c1=2),
              overwrite=True)
    run_command("r.null", map=m2, null=0)
    m1 = "tmprgreen_%i_m1" % pid
    exp = ("{combination}=if({management}=={c1},1,0)")
    r.mapcalc(exp.format(combination=m1,
                         management=management,
                         c1=1),
              overwrite=True)
    run_command("r.null", map=m1, null=0)
    not2 = "tmprgreen_%i_not2" % pid
    exp = ("{combination}=if(({treatment}=={c1} && {treatment}=={c2}),1,0)")
    r.mapcalc(exp.format(combination=not2,
                         c1=1,
                         treatment=treatment,
                         c2=99999),
              overwrite=True)
    run_command("r.null", map=not2, null=0)
    #TODO: try to remove all the r.nulle, since I
    # have done it at the beginning
    return m1t1, m1t2, m1, m2, not2


def slope_computation(elevation):
    pid = os.getpid()
    tmp_slope = 'tmprgreen_%i_slope' % pid
    tmp_slope_deg = 'tmprgreen_%i_slope_deg' % pid
    run_command("r.slope.aspect", overwrite=True,
                elevation=elevation, slope=tmp_slope, format="percent")
    run_command("r.slope.aspect", overwrite=True,
                elevation=elevation, slope=tmp_slope_deg)


def yield_pix_process(opts, vector_forest, yield_, yield_surface,
                      rivers, lakes, forest_roads, m1, m2,
                      m1t1, m1t2, roughness):
    pid = os.getpid()
    tmp_slope = 'tmprgreen_%i_slope' % pid
    tmp_slope_deg = 'tmprgreen_%i_slope_deg' % pid
    technical_surface = "tmprgreen_%i_technical_surface" % pid
    cable_crane_extraction = "tmprgreen_%i_cable_crane_extraction" % pid
    forwarder_extraction = "tmprgreen_%i_forwarder_extraction" % pid
    other_extraction = "tmprgreen_%i_other_extraction" % pid

    run_command("r.param.scale", overwrite=True,
                input=opts['elevation'], output="morphometric_features",
                size=3, method="feature")
    # peaks have an higher cost/distance in order not to change the valley

    expr = "{pix_cross} = ((ewres()+nsres())/2)/ cos({tmp_slope_deg})"
    r.mapcalc(expr.format(pix_cross=('tmprgreen_%i_pix_cross' % pid),
                          tmp_slope_deg=tmp_slope_deg),
              overwrite=True)
    #FIXME: yield surface is a plan surface and not the real one of the forest
    #unit, do I compute the real one?#
    # if yield_pix1 == 0 then yield is 0, then I can use yield or
    #  use yeld_pix but I will compute it only once in the code
    run_command("r.mapcalc", overwrite=True,
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
              overwrite=True)

    run_command("r.cost", overwrite=True,
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
              overwrite=True)

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
              overwrite=True)

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
              overwrite=True)

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
              overwrite=True)

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
              overwrite=True)
    tech_bioC = 'tmprgreen_%i_tech_bioenergyC' % pid
    ecc = ("{tech_bioC} = {technical_surface}*{m2}*{yield_pix}"
           "*{ton_tops_cop}")
    r.mapcalc(ecc.format(tech_bioC=tech_bioC,
                         technical_surface=technical_surface,
                         m2=m2,
                         yield_pix='yield_pix1',
                         ton_tops_cop=opts['ton_tops_cop']),
              overwrite=True)
    technical_bioenergy = "tmprgreen_%i_techbio" % pid
    exp = "{technical_bioenergy}={tech_bioHF}+{tech_bioC}"
    r.mapcalc(exp.format(technical_bioenergy=technical_bioenergy,
                         tech_bioC=tech_bioC,
                         tech_bioHF=tech_bioHF),
              overwrite=True)

    run_command("r.null", map=technical_bioenergy, null=0)
    #FIXME: use something more efficient
    with RasterRow(technical_bioenergy) as pT:
        T = np.array(pT)
    print(("Tech bioenergy stimated (ton): %.2f" % np.nansum(T)))
    return technical_bioenergy, tech_bioC, tech_bioHF
