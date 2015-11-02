#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#!/usr/bin/env python
#
# MODULE:      r.green.biomassfor.economic
# AUTHOR(S):   Sandro Sacchelli, Francesco Geri
#              Converted to Python by Pietro Zambelli and Francesco Geri, reviewed by Marco Ciolli
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
#% key: boundaries
#% type: string
#% description: Name of vector boundaries map (boolean map)
#% label: Name of vector boundaries map (boolean map)
#% required : yes
#%end
#%option 
#% key: forest_column_price
#% type: string
#% description: Vector field of wood typologies
#% required : yes
#%end
#%option 
#% key: conditions
#% type: string
#% description: List of wood assorments:price
#% required : yes
#%end
#%option 
#% key: output_basename
#% type: string
#% description: Basename for economic bioenergy (HF,CC and total)
#% gisprompt: new
#% key_desc : name
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
#%option G_OPT_R_INPUT
#% key: dtm2
#% type: string
#% description: Name of Digital terrain model map
#% required : yes
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
#% key: energy_tops_hf
#% type: double
#% description: Energy for tops and branches in high forest in MWh/m³
#% answer: 0.49
#% guisection: Energy
#%end
#%option
#% key: energy_cormometric_vol_hf
#% type: double
#% description: Energy for the whole tree in high forest (tops, branches and stem) in MWh/m³
#% answer: 1.97
#% guisection: Energy
#%end
#%option
#% key: energy_tops_cop
#% type: double
#% description: Energy for tops and branches for Coppices in MWh/m³
#% answer: 0.55
#% guisection: Energy
#%end
#%flag
#% key: r
#% description: Remove all operational maps
#%end




import grass.script as grass
from grass.script.core import run_command, parser,overwrite
from grass.pygrass.raster import RasterRow
import numpy as np



ow = overwrite()




def remove_map(opts, flgs):

    prf_yield = opts['field_prefix']

    pricelist=opts['prices'].split(',')

    run_command("g.remove", type="raster", flags="f", name="tot_roads")
    run_command("g.remove", type="raster", flags="f", name="tot_roads_neg")
    run_command("g.remove", type="raster", flags="f", name="frict_surf_tr1")
    run_command("g.remove", type="raster", flags="f", name="frict_surf_tr")
    run_command("g.remove", type="raster", flags="f", name="transp_dist")
    run_command("g.remove", type="raster", flags="f", name="transport_prod")
    run_command("g.remove", type="raster", flags="f", name="fell_costHFtr1")
    run_command("g.remove", type="raster", flags="f", name="chipp_cost")
    run_command("g.remove", type="raster", flags="f", name="fell_costHFtr2")
    run_command("g.remove", type="raster", flags="f", name="fell_proc_costC")
    run_command("g.remove", type="raster", flags="f", name="proc_costHFtr1")
    run_command("g.remove", type="raster", flags="f", name="proc_costHFtr2")
    run_command("g.remove", type="raster", flags="f", name="extr_cost_cablehf")
    run_command("g.remove", type="raster", flags="f", name="extr_cost_forw")
    run_command("g.remove", type="raster", flags="f", name="extr_cost_other")
    run_command("g.remove", type="raster", flags="f", name="transport_cost")
    run_command("g.remove", type="raster", flags="f", name="prod_costs")
    run_command("g.remove", type="raster", flags="f", name="direction_cost")
    run_command("g.remove", type="raster", flags="f", name="administrative_cost")
    run_command("g.remove", type="raster", flags="f", name="total_costs")
    run_command("g.remove", type="raster", flags="f", name="interests")
    run_command("g.remove", type="raster", flags="f", name="net_revenues")
    run_command("g.remove", type="raster", flags="f", name="positive_net_revenues")
    run_command("g.remove", type="raster", flags="f", name="net_rev_pos")
    run_command("g.remove", type="raster", flags="f", name="economic_surface")
    run_command("g.remove", type="raster", flags="f", name="chipp_prod")
    run_command("g.remove", type="raster", flags="f", name="chipp_prodHF")
    run_command("g.remove", type="raster", flags="f", name="chipp_prodC")
    run_command("g.remove", type="raster", flags="f", name="extr_cost_cableC")
    run_command("g.remove", type="raster", flags="f", name="cable_crane_extraction")
    run_command("g.remove", type="raster", flags="f", name="extr_dist")
    run_command("g.remove", type="raster", flags="f", name="extr_product_other")
    run_command("g.remove", type="raster", flags="f", name="extr_cableHF_em")
    run_command("g.remove", type="raster", flags="f", name="extr_product_cableC")
    run_command("g.remove", type="raster", flags="f", name="extr_product_cableHF")
    run_command("g.remove", type="raster", flags="f", name="extr_product_forw")
    run_command("g.remove", type="raster", flags="f", name="fell_proc_costHFtr1")
    run_command("g.remove", type="raster", flags="f", name="fell_proc_costHFtr2")
    run_command("g.remove", type="raster", flags="f", name="fell_proc_productC")
    run_command("g.remove", type="raster", flags="f", name="fell_proc_productHFtr1")
    run_command("g.remove", type="raster", flags="f", name="fell_proc_productHFtr2")
    run_command("g.remove", type="raster", flags="f", name="fell_productHFtr1")
    run_command("g.remove", type="raster", flags="f", name="fell_productHFtr2")
    run_command("g.remove", type="raster", flags="f", name="forwarder_extraction")
    run_command("g.remove", type="raster", flags="f", name="frict_surf_extr")
    run_command("g.remove", type="raster", flags="f", name="other_extraction")
    run_command("g.remove", type="raster", flags="f", name="pix_cross")
    run_command("g.remove", type="raster", flags="f", name="proc_productHFtr1")
    run_command("g.remove", type="raster", flags="f", name="techn_pix_comp")
    run_command("g.remove", type="raster", flags="f", name="technical_surface")
    run_command("g.remove", type="raster", flags="f", name="tot_dist")
    run_command("g.remove", type="raster", flags="f", name="total_revenues")
    run_command("g.remove", type="raster", flags="f", name="total_revenues1")
    run_command("g.remove", type="raster", flags="f", name="total_revenues2")
    run_command("g.remove", type="raster", flags="f", name="yield_pix")
    run_command("g.remove", type="raster", flags="f", name="yield_pix1")
    run_command("g.remove", type="raster", flags="f", name="yield_pix2")
    run_command("g.remove", type="raster", flags="f", name="yield_pixp")
    run_command("g.remove", type="raster", flags="f", name="technical_bioenergy")
    run_command("g.remove", type="raster", flags="f", name="slope__")
    run_command("g.remove", type="raster", flags="f", name="slope___")
    run_command("g.remove", type="raster", flags="f", name="slope_deg__")

    for x in range(1,len(pricelist)+1):
        mapvol1=prf_yield+'_vol_typ'+str(x)+'pix'
        mapvol2=prf_yield+'_vol_typ'+str(x)+'pix2'
        run_command("g.remove", type="raster", flags="f", name=mapvol1)
        run_command("g.remove", type="raster", flags="f", name=mapvol2)


def yield_pix_process(opts, flgs,vector_forest,yield_,yield_surface,rivers,lakes,forest_roads,management,treatment,roughness):


    run_command("r.slope.aspect", overwrite=ow,elevation=opts['dtm2'], slope="slope__", format="percent")
    run_command("r.slope.aspect", overwrite=ow,elevation=opts['dtm2'], slope="slope_deg__")

    run_command("r.param.scale", overwrite=ow,
                input=opts['dtm2'], output="morphometric_features",
                size=3, method="feature")


    run_command("r.mapcalc", overwrite=ow,
            expression='pix_cross = ((ewres()+nsres())/2)/ cos(slope_deg__)')

    run_command("r.mapcalc", overwrite=ow,  
        expression='yield_pix1 = ('+yield_+'/'+yield_surface+')*((ewres()*nsres())/10000)')

    run_command("r.null", map="yield_pix1", null=0)
    run_command("r.null", map="morphometric_features", null=0)

    exprmap='frict_surf_extr = pix_cross + if(yield_pix1<=0, 99999) + if(morphometric_features==6, 99999)'


    if rivers!='':
        run_command("v.to.rast", input=rivers,output="rivers", use="val", overwrite=True)
        rivers="rivers"
        run_command("r.null", map=rivers, null=0)
        exprmap+='+ if('+rivers+'>=1, 99999)'

    if lakes!='':        
        run_command("v.to.rast", input=lakes,output="lakes", use="val", overwrite=True)
        lakes="lakes"
        run_command("r.null", map=lakes, null=0)
        exprmap+='+ if('+lakes+'>=1, 99999)'


    run_command("r.mapcalc",overwrite=ow,expression=exprmap)

    run_command("r.cost", overwrite=ow,
            input="frict_surf_extr", output="extr_dist",
            stop_points=vector_forest, start_rast=forest_roads,
            max_cost=1500)

    CCEXTR = 'cable_crane_extraction = if('+yield_+'>0 && slope__>'+opts['slp_min_cc']+' && slope__<='+opts['slp_max_cc']+' && extr_dist<'+opts['dist_max_cc']+', 1)'

    FWEXTR = 'forwarder_extraction = if('+yield_+'>0 && slope__<='+opts['slp_max_fw']+' && '+management+'==1 && ('+roughness+'==0 || '+roughness+'==1 || '+roughness+'==99999) && extr_dist<'+opts['dist_max_fw']+', 1)'
    
    OEXTR = 'other_extraction = if('+yield_+'>0 && slope__<='+opts['slp_max_cop']+' && '+management+'==2 && ('+roughness+'==0 || '+roughness+'==1 || '+roughness+'==99999) && extr_dist<'+opts['dist_max_cop']+', 1)'


    run_command("r.mapcalc", overwrite=ow,expression=CCEXTR)
    run_command("r.mapcalc", overwrite=ow,expression=FWEXTR)
    run_command("r.mapcalc", overwrite=ow,expression=OEXTR)


    run_command("r.null", map="cable_crane_extraction", null=0)
    run_command("r.null", map="forwarder_extraction", null=0)
    run_command("r.null", map="other_extraction", null=0)


    run_command("r.mapcalc", overwrite=ow,expression='technical_surface = cable_crane_extraction + forwarder_extraction + other_extraction')
    
    run_command("r.null", map="technical_surface", null=0)


    EHF = 'tech_bioenergyHF = technical_surface*(if('+management+'==1 && '+treatment+'==1 || '+management+'==1 && '+treatment+'==99999, yield_pix*'+opts['energy_tops_hf']+', if('+management+'==1 && '+treatment+'==2, yield_pix *'+opts['energy_tops_hf']+' + yield_pix * '+opts['energy_cormometric_vol_hf']+')))'

    ECC = 'tech_bioenergyC = technical_surface*(if('+management+' == 2, yield_pix*'+opts['energy_tops_cop']+'))'

    ET='technical_bioenergy=tech_bioenergyHF+tech_bioenergyC'

    # run_command("r.stats.zonal", overwrite=ow,
    #             base="compartment", cover="technical_surface", method="sum",
    #             output="techn_pix_comp")

    # run_command("r.mapcalc", overwrite=ow,
    #     expression='yield_pix2 = yield/(technical_surface*techn_pix_comp)')   
    
    # YPIX = 'yield_pix = yield_pix1*%d + yield_pix2*%d'

    # run_command("r.mapcalc", overwrite=ow,
    #             expression=YPIX % (1 if flgs['u'] else 0, 0 if flgs['u'] else 1,))

    run_command("r.mapcalc", overwrite=ow,expression="yield_pix=yield_pix1")

    # run_command("r.mapcalc", overwrite=ow,expression=YPIX)

    run_command("r.mapcalc", overwrite=ow,expression=EHF)
    run_command("r.mapcalc", overwrite=ow,expression=ECC)
    run_command("r.mapcalc", overwrite=ow,expression=ET)

    run_command("g.remove", type="raster", flags="f", name="tech_bioenergyHF,tech_bioenergyC")

    run_command("r.null", map="technical_bioenergy", null=0)

    tech_bioenergy="technical_bioenergy"

    with RasterRow(tech_bioenergy) as pT:
        T = np.array(pT)
    print ("Tech bioenergy stimated (Mwh): %.2f" % np.nansum(T))


def revenues(opts, flgs,yield_surface,management,treatment,forest,yield_):
    # Calculate revenues
    fieldprice=opts['forest_column_price']
    fieldcond=opts['conditions']

    

    # pricelist=opts['prices'].split(',') #convert the string in list of string


    # for x in range(1,len(pricelist)+1):
    #     price_field=prf_yield+"_voltyp"+str(x)
    #     run_command("r.mapcalc", overwrite=ow,expression=prf_yield+'_vol_typ'+str(x)+'pix = ('+price_field+'/'+yield_surface+')*(ewres()*nsres()/10000)')
    #     run_command("r.null", map=prf_yield+'_vol_typ'+str(x)+'pix', null=0)

    listwoods=fieldcond.split(',')

    prices=''

    for wood in listwoods:
        #import ipdb; ipdb.set_trace()
        woodprice=wood.split('=')
        where_cond=fieldprice+" like "+"'"+woodprice[0]+"'"
        run_command("v.to.rast",input=forest,output='forest_'+woodprice[0],use="attr", attrcolumn=yield_, where=where_cond)
        exprpix='forest_'+woodprice[0]+'_pix=(forest_'+woodprice[0]+"/"+yield_surface+')*(ewres()*nsres()/10000)'
        run_command("r.mapcalc", overwrite=ow, expression=exprpix)
        nullmap='forest_'+woodprice[0]+'_pix'
        run_command("r.null", map=nullmap,null=0)
        prices+=nullmap+'*'+woodprice[1]+"+"
    prices=prices[:-1]
        
    #prices = '+'.join(["vol_typ%dpix*%f" % (i+1, price) for i, price in enumerate(opts['prices'])])
    #prices = '+'.join([prf_yield+"_vol_typ%dpix*%f" % (i+1, float(price)) for i, price in enumerate(pricelist)])

    #import ipdb; ipdb.set_trace()

    price_energy_woodchips=float(opts['price_energy_woodchips'])   
    

    TR1='total_revenues1 = technical_surface*(if('+management+' == 1 && '+treatment+'==1 || '+management+' == 1 && '+treatment+'==99999 || '+management+' == 2,('+prices+'+(technical_bioenergy*'+str(price_energy_woodchips)+')), if('+management+' == 1 && '+treatment+'==2, technical_bioenergy*'+str(price_energy_woodchips)+')))'


    run_command("r.mapcalc", overwrite=ow, expression=TR1)


    run_command("r.mapcalc",overwrite=ow,expression='total_revenues=total_revenues1')

    
    
def productivity(opts, flgs,management,treatment,soilp2_map,tree_diam,tree_vol,forest_roads,main_roads):

    if tree_diam == '':
        tree_diam="99999"
    if tree_vol == '':
        tree_vol="9.999"
    if soilp2_map == '':
        soilp2_map="99999"

    dhp=opts['dhp']

    run_command("r.mapcalc",overwrite=ow,
                expression="slope___=if(slope__<=100,slope__,100)")

    # Calculate productivity
    #view the paper appendix for the formulas
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_productHFtr1 = if('+management+' ==1 && ('+treatment+' ==1 || '+treatment+' ==99999) && '+tree_diam+' <99999,(cable_crane_extraction*(42-(2.6*'+tree_diam+'))/(-20))*1.65*(1-(slope___/100)), if('+management+' ==1 && ('+treatment+' ==1 || '+treatment+' ==99999) && '+tree_diam+' == 99999,(cable_crane_extraction*(42-(2.6*35))/(-20))*1.65*(1-(slope___/100))))')
    run_command("r.null", map="fell_productHFtr1", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_productHFtr2 = if('+management+' ==1 && '+treatment+' ==2 && '+tree_diam+' <99999,(cable_crane_extraction*(42-(2.6*'+tree_diam+'))/(-20))*1.65*(1-((1000-(90*slope___)/(-80))/100)), if('+management+' ==1 && '+treatment+' ==2 && '+tree_diam+' == 99999,(cable_crane_extraction*(42-(2.6*35))/(-20))*1.65*(1-((1000-(90*slope___)/(-80))/100))))')
    run_command("r.null", map="fell_productHFtr2", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_productC = if('+management+' ==2 && '+soilp2_map+' <99999,((0.3-(1.1*'+soilp2_map+'))/(-4))*(1-(slope___/100)), if('+management+' ==2 && '+soilp2_map+' == 99999,((0.3-(1.1*3))/(-4))*(1-(slope___/100))))')
    run_command("r.null", map="fell_proc_productC", null=0)
    ###### check fell_proc_productC ######

    #9999: default value, if is present take into the process the average value (in case of fertility is 33)



    run_command("r.mapcalc", overwrite=ow,
                expression='proc_productHFtr1 = if('+management+' == 1 && ('+treatment+' == 1 || '+treatment+' ==99999) && '+tree_diam+'==99999, cable_crane_extraction*0.363*35^1.116, if('+management+' == 1 && ('+treatment+' == 1 || '+treatment+' ==99999) && '+tree_diam+'<99999, cable_crane_extraction*0.363*'+tree_diam+'^1.116))')
    run_command("r.null", map="proc_productHFtr1", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_productHFtr1 = if('+management+' == 1 && ('+treatment+' == 1 || '+treatment+' ==99999) && '+tree_vol+'<9.999, forwarder_extraction*60/(1.5*(2.71^(0.1480-0.3894*2+0.0002*(slope___^2)-0.2674*2.5))+(1.0667+(0.3094/'+tree_vol+')-0.1846*1)), if('+management+' == 1 && ('+treatment+' == 1 || '+treatment+' ==99999) && '+tree_vol+'==9.999, forwarder_extraction*60/(1.5*(2.71^(0.1480-0.3894*2+0.0002*(slope___^2)-0.2674*2.5))+(1.0667+(0.3094/0.7)-0.1846*1))))')
    run_command("r.null", map="fell_proc_productHFtr1", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_productHFtr2 = if('+management+' == 1 && '+treatment+' == 2 && '+tree_vol+'<9.999, forwarder_extraction*60/(1.5*(2.71^(0.1480-0.3894*2+0.0002*(slope___^2)-0.2674*2.5))+(1.0667+(0.3094/'+tree_vol+')-0.1846*1))*0.8, if('+management+' == 1 && '+treatment+' == 2 && '+tree_vol+'==9.999, forwarder_extraction*60/(1.5*(2.71^(0.1480-0.3894*2+0.0002*(slope___^2)-0.2674*2.5))+(1.0667+(0.3094/0.7)-0.1846*1))*0.8))')
    run_command("r.null", map="fell_proc_productHFtr2", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='chipp_prodHF = if('+management+' ==1 && ('+treatment+' == 1 ||  '+treatment+' == 99999), yield_pix/34, if('+management+' ==1 && '+treatment+' == 2, yield_pix/20.1))')
    run_command("r.null", map="chipp_prodHF", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='chipp_prodC = if('+management+' ==2, yield_pix/45.9)')
    run_command("r.null", map="chipp_prodC", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='chipp_prod = chipp_prodHF + chipp_prodC')
    run_command("r.null", map="chipp_prod", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_product_cableHF = if('+management+' ==1, cable_crane_extraction*149.33*(extr_dist^-1.3438)* extr_dist/8*0.75)')
    run_command("r.null", map="extr_product_cableHF", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_product_cableC = if('+management+' ==2, cable_crane_extraction*149.33*(extr_dist^-1.3438)* extr_dist/8*0.75)')
    run_command("r.null", map="extr_product_cableC", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_product_forw = forwarder_extraction*36.293*(extr_dist^-1.1791)* extr_dist/8*0.6')
    run_command("r.null", map="extr_product_forw", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_product_other = other_extraction*36.293*(extr_dist^-1.1791)* extr_dist/8*0.6')
    run_command("r.null", map="extr_product_other", null=0)
        
    #cost of the transport distance
    #this is becouse the wood must be sell to the collection point
    #instead the residual must be brung to the heating points
    
    run_command("r.mapcalc", overwrite=ow,
                expression='tot_roads = '+forest_roads+' ||| '+main_roads)
    run_command("r.null", map="tot_roads", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='tot_roads_neg = if(tot_roads==1,0,1)')
    run_command("r.null", map="tot_roads_neg", null=1)
    run_command("r.mapcalc", overwrite=ow,
                expression='frict_surf_tr1 =  frict_surf_extr*tot_roads_neg')
    run_command("r.mapcalc", overwrite=ow,
                expression='frict_surf_tr = frict_surf_tr1+(tot_roads*((ewres()+nsres())/2))')

    try:
        run_command("r.cost", overwrite=ow, input="frict_surf_tr",
                    output="tot_dist", stop_points=opts['forest'], start_points=dhp,
                    max_cost=100000)
        run_command("r.mapcalc", overwrite=ow,
                    expression='transp_dist = tot_dist -  extr_dist')
    except:
        run_command("r.mapcalc", overwrite=ow,
                    expression='transp_dist = extr_dist')

    run_command("r.mapcalc", overwrite=ow,
                expression='transport_prod = if(('+treatment+' == 1 ||  '+treatment+' == 99999), ((transp_dist/1000/30)*(yield_pix*1/32)*2), if('+management+' ==1 && '+treatment+' == 2, ((transp_dist/1000/30)*(yield_pix*2.7/32)*2)))')

    #the cost of distance transport derived by the negative of the friction surface
    #the DHP must be inside the study area and connected with the road network

def costs(opts, flgs):
    # Calculate costs

    run_command("r.mapcalc", overwrite=ow,
                expression='fell_costHFtr1 = '+opts['cost_chainsaw']+'/fell_productHFtr1*yield_pix')
    run_command("r.null", map="fell_costHFtr1", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_costHFtr2 = '+opts['cost_chainsaw']+'/fell_productHFtr2*yield_pix')
    run_command("r.null", map="fell_costHFtr2", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_costC = '+opts['cost_chainsaw']+'/fell_proc_productC*yield_pix')
    run_command("r.null", map="fell_proc_costC", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='proc_costHFtr1 = '+opts['cost_processor']+'/proc_productHFtr1*yield_pix')
    run_command("r.null", map="proc_costHFtr1", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_costHFtr1 = '+opts['cost_harvester']+'/fell_proc_productHFtr1*yield_pix')
    run_command("r.null", map="fell_proc_costHFtr1", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_costHFtr2 = '+opts['cost_harvester']+'/fell_proc_productHFtr2*yield_pix')
    run_command("r.null", map="fell_proc_costHFtr2", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='chipp_cost = '+opts['cost_chipping']+'*chipp_prod')
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_cost_cableHF = '+opts['cost_cablehf']+'/extr_product_cableHF*yield_pix')
    run_command("r.null", map="extr_cost_cableHF", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_cost_cableC = '+opts['cost_cablec']+'/extr_product_cableC*yield_pix')
    run_command("r.null", map="extr_cost_cableC", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_cost_forw ='+opts['cost_forwarder']+'/extr_product_forw*yield_pix')
    run_command("r.null", map="extr_cost_forw", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_cost_other = '+opts['cost_skidder']+'/extr_product_other*yield_pix')
    run_command("r.null", map="extr_cost_other", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='transport_cost = '+opts['cost_transport']+'*transport_prod')
    run_command("r.mapcalc", overwrite=ow,
                expression='prod_costs1 = fell_costHFtr1 +  fell_costHFtr2+ fell_proc_costC + proc_costHFtr1 + fell_proc_costHFtr1 + fell_proc_costHFtr2 + chipp_cost + extr_cost_cableHF + extr_cost_cableC + extr_cost_forw + extr_product_other + transport_cost')
    


    ######## patch to correct problem of negative costs #######
    run_command("r.mapcalc", overwrite=ow,expression='prod_costs =  prod_costs1>=0 ? prod_costs1 : 0')
    ######## end patch ##############

    run_command("r.mapcalc", overwrite=ow,
                expression='direction_cost =  prod_costs *0.05')
    run_command("r.mapcalc", overwrite=ow,
                expression='administrative_cost =  total_revenues*0.07')
    run_command("r.mapcalc", overwrite=ow,
                expression='interests = (prod_costs +  administrative_cost)*0.03/4')
                
    
    #management and administration costs
    
    ###########################
    # patch for solve the absence of some optional maps 
                
    map_prodcost=grass.find_file('prod_costs',element='cell')
    map_admcost=grass.find_file('administrative_cost',element='cell')
    map_dircost=grass.find_file('direction_cost',element='cell')
    
    listcost=''
    
    if map_admcost['fullname']!='':
        listcost+=map_admcost['fullname']
    if map_dircost['fullname']!='':
        listcost+="+"+map_dircost['fullname']
    if map_prodcost['fullname']!='':
        listcost+="+"+map_prodcost['fullname']  
        
    # end of patch
    ###########################
    
    
    run_command("r.mapcalc", overwrite=ow,
                expression='total_costs = %s' % listcost)


def net_revenues(opts, flgs,management,treatment):



    output = opts['output_basename']

    econ_bioenergyHF=output+'_econ_bioenergyHF'
    econ_bioenergyC=output+'_econ_bioenergyC'
    econ_bioenergy=output+'_econ_bioenergy'

    
    # Calculate net revenues and economic biomass
    run_command("r.mapcalc", overwrite=ow,
                expression='net_revenues = total_revenues - total_costs')
    run_command("r.mapcalc", overwrite=ow,
                expression='positive_net_revenues = if(net_revenues<=0,0,1)')
    run_command("r.mapcalc", overwrite=ow,
                expression='net_rev_pos = net_revenues*positive_net_revenues')
    
    #per evitare che vi siano pixel con revenues>0 sparsi si riclassifica la mappa
    #in order to avoid pixel greater than 0 scattered the map must be reclassified
    #considering only the aree clustered greater than 1 hectares

    
    run_command("r.reclass.area", overwrite=ow,
                input="positive_net_revenues",
                output="economic_surface", value=1, mode="greater")

    ECONHF=econ_bioenergyHF+' = economic_surface*(if('+management+' == 1 && '+treatment+'==1 || '+management+' == 1 && '+treatment+'== 99999,yield_pix*'+opts['energy_tops_hf']+', if('+management+' == 1 && '+treatment+'==2, yield_pix*'+opts['energy_tops_hf']+'+yield_pix*'+opts['energy_cormometric_vol_hf']+')))'
    ECONC=econ_bioenergyC+'= economic_surface*(if('+management+' == 2, yield_pix*'+opts['energy_tops_cop']+'))'
    ECONTOT=econ_bioenergy+' = ('+econ_bioenergyHF+' + '+econ_bioenergyC+')'



    run_command("r.mapcalc", overwrite=ow, expression=ECONHF)

    run_command("r.mapcalc", overwrite=ow, expression=ECONC)

    run_command("r.mapcalc", overwrite=ow, expression=ECONTOT)


def main(opts, flgs):


    output = opts['output_basename']

    forest=opts['forest']
    boundaries=opts['boundaries']
    yield_=opts['forest_column_yield']
    management=opts['forest_column_management']
    treatment=opts['forest_column_treatment']
    yield_surface=opts['forest_column_yield_surface']
    roughness=opts['forest_column_roughness']
    forest_roads=opts['forest_roads']
    main_roads=opts['main_roads']

    rivers=opts['rivers']
    lakes=opts['lakes']

    tree_diam=opts['tree_diam']
    tree_vol=opts['tree_vol']
    soilp2_map=opts['soilp2_map']

    fieldprice=opts['forest_column_price']
    fieldcond=opts['conditions']


    econ_bioenergyHF=output+'_econ_bioenergyHF'
    econ_bioenergyC=output+'_econ_bioenergyC'
    econ_bioenergy=output+'_econ_bioenergy'



    ######## start import and convert ########

    run_command("g.region",vect=boundaries)
    run_command("v.to.rast", input=forest,output="yield", use="attr", attrcolumn=yield_,overwrite=True)
    run_command("v.to.rast", input=forest,output="yield_surface", use="attr", attrcolumn=yield_surface,overwrite=True)
    run_command("v.to.rast", input=forest,output="treatment", use="attr", attrcolumn=treatment,overwrite=True)
    run_command("v.to.rast", input=forest,output="management", use="attr", attrcolumn=management,overwrite=True)

    run_command("v.to.rast", input=forest_roads,output="forest_roads", use="val", overwrite=True)
    run_command("v.to.rast", input=main_roads,output="main_roads", use="val", overwrite=True)



    run_command("r.null", map='yield',null=0)
    run_command("r.null", map='yield_surface',null=0)
    run_command("r.null", map='treatment',null=0)
    run_command("r.null", map='management',null=0)


    ######## end import and convert ########


    ######## temp patch to link map and fields ######

    management="management"
    treatment="treatment"
    yield_surface="yield_surface"
    yield_="yield"
    forest_roads="forest_roads"
    main_roads="main_roads"

    ######## end temp patch to link map and fields ######

    if roughness=='':
        run_command("r.mapcalc",overwrite=ow,expression='roughness=0')
        roughness='roughness'
    else:
        run_command("v.to.rast", input=forest,output="roughness", use="attr", attrcolumn=roughness,overwrite=True)
        run_command("r.null", map='roughness',null=0)
        roughness='roughness'

    if tree_diam=='':
        run_command("r.mapcalc",overwrite=ow,expression='tree_diam=99999')
        tree_diam='tree_diam'

    if tree_vol=='':
        run_command("r.mapcalc",overwrite=ow,expression='tree_vol=9.999')
        tree_diam='tree_vol'

    if soilp2_map=='':
        run_command("r.mapcalc",overwrite=ow,expression='soil_map=99999')
        soilp2_map='soil_map'


    yield_pix_process(opts,flgs,forest,yield_,yield_surface,rivers,lakes,forest_roads,management,treatment,roughness)
    

    revenues(opts, flgs,yield_surface,management,treatment,forest,yield_)
    
    productivity(opts, flgs,management,treatment,soilp2_map,tree_diam,tree_vol,forest_roads,main_roads)
    costs(opts, flgs)
    net_revenues(opts, flgs,management,treatment)

    if flgs['r'] == True:
         remove_map(opts, flgs)


    with RasterRow(econ_bioenergy) as pT:
        T = np.array(pT)

    print "Resulted maps: "+output+"_econ_bioenergyHF, "+output+"_econ_bioenergyC, "+output+"_econ_bioenergy"
    print ("Total bioenergy stimated (Mwh): %.2f" % np.nansum(T))


    

if __name__ == "__main__":
    main(*parser())
