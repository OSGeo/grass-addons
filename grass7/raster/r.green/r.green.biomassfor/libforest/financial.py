# -*- coding: utf-8 -*-
############################################################################
#
# AUTHOR(S):   Giulia Garegnani
# PURPOSE:     libraries for the financial module of biomassfor
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
from grass.script.core import find_file
from grass.script.core import run_command
from grass.pygrass.modules.shortcuts import raster as r


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
    run_command("r.mapcalc", overwrite=True, expression=exprpix)
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
              overwrite=True)
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
    #FIXME: to remove this big list of temporary file
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
              overwrite=True)
    #view the paper appendix for the formulas
    expr = ("{fell_productHFtr1} = {mt}*{cable_crane_extraction}"
            "*(42-2.6*{tree_diam})/(-20.0)*1.65*(1-{slope___}/100.0)")
    r.mapcalc(expr.format(fell_productHFtr1=fell_productHFtr1,
                          mt=m1t1,
                          cable_crane_extraction="cable_crane_extraction",
                          tree_diam="tmprgreen_%i_tree_diam" % pid,
                          slope___='tmprgreen_%i_slope' % pid), overwrite=True)
    run_command("r.null", map=fell_productHFtr1, null=0)

    expr = ("{fell_productHFtr2} = {mt}*{cable_crane_extraction}*"
            "(42-2.6*{tree_diam})/(-20)*1.65*(1-(1000-90*{slope}/(-80))/100)")
    r.mapcalc(expr.format(fell_productHFtr2=fell_productHFtr2,
                          mt=m1t2,
                          cable_crane_extraction="cable_crane_extraction",
                          tree_diam="tmprgreen_%i_tree_diam" % pid,
                          slope='tmprgreen_%i_slope' % pid), overwrite=True)
    run_command("r.null", map=fell_productHFtr2, null=0)
    #FIXME: it is different from the paper, to check
    expr = ("{fell_proc_productC} = {m2}*"
            "(0.3-1.1*{soilp2_map})/(-4)*(1-{slope}/100)")
    r.mapcalc(expr.format(fell_proc_productC=fell_proc_productC,
                          m2=m2,
                          soilp2_map="tmprgreen_%i_soilp2_map" % pid,
                          slope='tmprgreen_%i_slope' % pid), overwrite=True)
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
              overwrite=True)
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
              overwrite=True)
    r.mapcalc(expr.format(out=fell_proc_productHFtr2,
                          mt=m1t2,
                          extraction="forwarder_extraction",
                          k=1.5, st=2, sb=2.5,
                          tree_vol="tmprgreen_%i_tree_vol" % pid,
                          slope="tmprgreen_%i_slope" % pid,
                          perc=0.8),
              overwrite=True)
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
              overwrite=True)
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
                  overwrite=True)
        run_command("r.null", map=key, null=0)

    #cost of the transport distance
    #this is becouse the wood must be sell to the collection point
    #instead the residual must be brung to the heating points
    tot_roads = "tmprgreen_%i_tot_roads" % pid
    run_command("r.mapcalc", overwrite=True,
                expression=('%s = %s ||| %s' % (tot_roads,
                                                forest_roads, main_roads)))
    run_command("r.null", map=tot_roads, null=0)

    expr = ("{frict_surf_tr}={frict_surf_extr}*not({tot_roads})"
            "*{tot_roads}*((ewres()+nsres())/2)")
    r.mapcalc(expr.format(frict_surf_tr="tmprgreen_%i_frict_surf_tr" % pid,
                          frict_surf_extr='tmprgreen_%i_frict_surf_extr' % pid,
                          tot_roads=tot_roads
                          ),
              overwrite=True)

    transp_dist = "tmprgreen_%i_transp_dist" % pid
    extr_dist = "tmprgreen_%i_extr_dist" % pid
    try:
        tot_dist = "tmprgreen_%i_tot_dist" % pid
        run_command("r.cost", overwrite=True,
                    input=("tmprgreen_%i_frict_surf_tr" % pid),
                    output=tot_dist,
                    stop_points=opts['forest'],
                    start_points=dhp,
                    max_cost=100000)
        run_command("r.mapcalc", overwrite=True,
                    expression=("%s = %s - %s"
                                % (transp_dist, tot_dist, extr_dist)))
    except:
        run_command("r.mapcalc", overwrite=True,
                    expression=('% = %s' % (transp_dist, extr_dist)))

    expr = ("{transport_prod} = {transp_dist}/30000"
            "*({not2}*({yield_pix}/32)*2 +{m1t2}*({yield_pix}*2.7/32)*2)")

    r.mapcalc(expr.format(transport_prod=transport_prod,
                          yield_pix="yield_pix1",
                          not2=not2,
                          m1t2=m1t2,
                          transp_dist="tmprgreen_%i_transp_dist" % pid
                          ),
              overwrite=True)
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
                  overwrite=True)
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
                  overwrite=True)
        run_command("r.null",
                    map=("tmprgreen_%i_cost_%s" % (pid, key)),
                    null=0)
        command += "tmprgreen_%i_cost_%s+" % (pid, key)

    run_command("r.mapcalc", overwrite=True,
                expression=command[:-1])
    #FIXME: the correction about negative cost have to be done in
    # the productivity single map in my opinion
    ######## patch to correct problem of negative costs #######
    prod_costs = "tmprgreen_%i_prod_cost" % pid
    expr = '{prod_costs} =  {prod_costs}>=0 ? {prod_costs} : 0'
    r.mapcalc(expr.format(prod_costs=prod_costs,
                          ),
              overwrite=True)
    ######## end patch ##############
    direction_cost = "tmprgreen_%i_direction_cost" % pid
    administrative_cost = "tmprgreen_%i_administrative_cost" % pid
    interests = "tmprgreen_%i_interests" % pid
    run_command("r.mapcalc", overwrite=True,
                expression='%s =  %s *0.05' % (direction_cost,
                                               prod_costs))
    run_command("r.mapcalc", overwrite=True,
                expression=('%s =  %s*0.07' % (administrative_cost,
                                               total_revenues)))
    run_command("r.mapcalc", overwrite=True,
                expression=('%s= (%s + %s)*0.03/4'
                            % (interests, prod_costs, administrative_cost)))

    #management and administration costs

    ###########################
    # patch for solve the absence of some optional mapss

    map_prodcost = find_file(prod_costs, element='cell')
    map_admcost = find_file(administrative_cost, element='cell')
    map_dircost = find_file(direction_cost, element='cell')

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
    run_command("r.mapcalc", overwrite=True,
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
    run_command("r.mapcalc", overwrite=True,
                expression='%s = %s - %s' % (net_revenues, total_revenues,
                                             total_costs))
    positive_net_revenues = "tmprgreen_%i_positive_net_revenues" % pid
    run_command("r.mapcalc", overwrite=True,
                expression=('%s = if(%s<=0,0,1)' % (positive_net_revenues,
                                                    net_revenues)))

    #per evitare che vi siano pixel con revenues>0 sparsi
    #si riclassifica la mappa
    #in order to avoid pixel greater than 0 scattered
    #the map must be reclassified
    #considering only the aree clustered greater than 1 hectares
    economic_surface = "tmprgreen_%i_economic_surface" % pid
    run_command("r.reclass.area", overwrite=True,
                input=positive_net_revenues,
                output=economic_surface, value=1, mode="greater")

    expr = "{econ_bioenergy} = {economic_surface}*{tech_bio}"
    r.mapcalc(expr.format(econ_bioenergy=econ_bioenergyHF,
                          economic_surface=economic_surface,
                          tech_bio=tech_bioHF
                          ),
              overwrite=True)
    r.mapcalc(expr.format(econ_bioenergy=econ_bioenergyC,
                          economic_surface=economic_surface,
                          tech_bio=tech_bioC
                          ),
              overwrite=True)

    econtot = ("%s = %s + %s" % (econ_bioenergy, econ_bioenergyC,
                                 econ_bioenergyHF))
    run_command("r.mapcalc", overwrite=True, expression=econtot)
