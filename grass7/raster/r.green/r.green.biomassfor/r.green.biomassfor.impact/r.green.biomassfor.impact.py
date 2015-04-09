#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.biomassfor.impact
# AUTHOR(S):   Sandro Sacchelli, Francesco Geri
#              Converted to Python by Francesco Geri, reviewed by Marco Ciolli 
# PURPOSE:     Calculates impacts and multifunctionality values regarding fertility maintenance, 
#              soil water protection, biodiversity, sustainable bioenergy, 
#              avoided CO2 emission, fire risk, recreation
# COPYRIGHT:   (C) 2013 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
#%Module
#% description: Calculates impact and multifunctionality values
#% keyword: raster
#% keyword: biomass
#%End
#%option G_OPT_V_INPUT
#% key: forest
#% type: string
#% description: Name of vector parcel map
#% label: Name of vector parcel map
#% required : yes
#% guisection: Base
#%end
#%option G_OPT_R_INPUT
#% key: yield1
#% type: string
#% description: Map of forest yield (cubic meters)
#% required : yes
#% guisection: Base
#%end
#%option G_OPT_R_INPUT
#% key: yield_surface
#% type: string
#% description: Map of stand surface (ha)
#% required : yes
#% guisection: Base
#%end
#%option G_OPT_R_INPUT
#% key: management
#% type: string
#% description: Map of forest management (1: high forest, 2:coppice)
#% required : yes
#% guisection: Base
#%end
#%option G_OPT_R_INPUT
#% key: treatment
#% type: string
#% description: Map of forest treatment (1: final felling, 2:thinning)
#% required : yes
#% guisection: Base
#%end
#%option G_OPT_R_INPUT
#% key: forest_roads
#% type: string
#% description: Raster map of forest roads (0, 1)
#% required : yes
#% guisection: Base
#%end
#%option
#% key: energy_tops_hf
#% type: double
#% description: Energy for tops and branches in high forest in MWh/m³
#% answer: 0.49
#% required : yes
#% guisection: Base
#%end
#%option
#% key: energy_cormometric_vol_hf
#% type: double
#% description: Energy for tops and branches for high forest in MWh/m³
#% answer: 1.97
#% required : yes
#% guisection: Base
#%end
#%option
#% key: energy_tops_cop
#% type: double
#% description: Energy for tops and branches for Coppices in MWh/m³
#% answer: 0.55
#% required : yes
#% guisection: Base
#%end
#%option G_OPT_R_INPUT
#% key: energy_map
#% description: Bioenergy map in MWh/m³
#% required : yes
#% guisection: Base
#%end
#%option G_OPT_V_INPUT
#% key: dhp
#% type: string
#% description: Name of vector district heating points
#% label: Name of vector district heating points
#% required : yes
#% guisection: Base
#%end
#%option 
#% key: output_sw_map
#% type: string
#% description: Name for output soil and water reduction bioenergy map
#% key_desc : name
#% guisection: Soil and water protection
#%end
#%option G_OPT_R_INPUT
#% key: dtm
#% type: string
#% description: Name of Digital terrain model map
#% required : no
#% guisection : Soil and water protection
#%end
#%option G_OPT_R_INPUT
#% key: soiltx_map
#% type: string
#% description: Soil texture map
#% required : no
#% guisection: Soil and water protection
#%end
#%option G_OPT_R_INPUT
#% key: soild_map
#% type: string
#% description: Soil depth map
#% required : no
#% guisection: Soil and water protection
#%end
#%option G_OPT_R_INPUT
#% key: soilcmp_map
#% type: string
#% description: Soil compaction risk map
#% required : no
#% guisection: Soil and water protection
#%end
#%option 
#% key: output_co2_map
#% type: string
#% description: Name for output CO2 emissions map
#% key_desc : name
#% guisection: CO2 Emission
#%end
#%option 
#% key: output_aco2_map
#% type: string
#% description: Name for output avoided CO2 emissions map
#% key_desc : name
#% guisection: CO2 Emission
#%end
#%option 
#% key: output_netco2_map
#% type: string
#% description: Name for output net CO2 emissions map
#% key_desc : name
#% guisection: CO2 Emission
#%end
#%option G_OPT_R_INPUT
#% key: dtm2
#% type: string
#% description: Name of Digital terrain model map
#% required : no
#% guisection : CO2 Emission
#%end
#%option G_OPT_R_INPUT
#% key: roughness
#% type: string
#% description: Name of roughness map
#% required : no
#% guisection: CO2 Emission
#%end
#%option G_OPT_R_INPUT
#% key: soilp2_map
#% type: string
#% description: Soil production map
#% required : no
#% guisection: CO2 Emission
#%end
#%option G_OPT_R_INPUT
#% key: tree_diam
#% type: string
#% description: Average tree diameter map
#% required : no
#% guisection: CO2 Emission
#%end
#%option G_OPT_R_INPUT
#% key: tree_vol
#% type: string
#% description: Average tree volume map
#% required : no
#% guisection: CO2 Emission
#%end
#%option G_OPT_R_INPUT
#% key: main_roads
#% type: string
#% description: Name of raster main roads
#% label: Name of raster main roads
#% required : yes
#% guisection: CO2 Emission
#%end
#%option G_OPT_R_INPUT
#% key: rivers
#% type: string
#% description: Raster map of rivers (0, 1)
#% required : no
#% guisection: CO2 Emission
#%end
#%option G_OPT_R_INPUT
#% key: lakes
#% type: string
#% description: Raster map of lakes (0, 1)
#% required : no
#% guisection: CO2 Emission
#%end
#%option
#% key: slp_min_cc
#% type: double
#% description: Percent slope lower limit with Cable Crane
#% answer: 30.
#% required : no
#% guisection: CO2 Emission
#%end
#%option
#% key: slp_max_cc
#% type: double
#% description: Percent slope higher limit with Cable Crane
#% answer: 100.
#% required : no
#% guisection: CO2 Emission
#%end
#%option
#% key: dist_max_cc
#% type: double
#% description: Maximum distance with Cable Crane
#% answer: 800.
#% required : no
#% guisection: CO2 Emission
#%end
#%option
#% key: slp_max_fw
#% type: double
#% description: Percent slope higher limit with Forwarder
#% answer: 30.
#% required : no
#% guisection: CO2 Emission
#%end
#%option
#% key: dist_max_fw
#% type: double
#% description: Maximum distance with Forwarder
#% answer: 600.
#% required : no
#% guisection: CO2 Emission
#%end
#%option
#% key: slp_max_cop
#% type: double
#% description: Percent slope higher limit with other techniques for Coppices
#% answer: 30.
#% required : no
#% guisection: CO2 Emission
#%end
#%option
#% key: dist_max_cop
#% type: double
#% description: Maximum distance with other techniques for Coppices
#% answer: 600.
#% required : no
#% guisection: CO2 Emission
#%end
#%option 
#% key: output_fr_map
#% type: string
#% description: Name for output reduction map of fire risk
#% key_desc : name
#% guisection: Fire risk
#%end
#%option G_OPT_R_INPUT
#% key: firerisk_map
#% type: string
#% description: Fire risk map
#% required : no
#% guisection: Fire risk
#%end
#%option 
#% key: output_tot_re_map
#% type: string
#% description: Name for output total recreational map
#% key_desc : name
#% guisection: Recreational
#%end
#%option 
#% key: output_imp_re_map
#% type: string
#% description: Name for output improved recreational map
#% key_desc : name
#% guisection: Recreational
#%end
#%option G_OPT_R_INPUT
#% key: touristic_map
#% type: string
#% description: Touristic map
#% required : no
#% guisection: Recreational
#%end
#%option G_OPT_V_INPUT
#% key: tev
#% type: string
#% description: Name of vector Total Economic Value map
#% label: Name of vector Total Economic Value map
#% required : no
#% guisection: TEV
#%end
#%option 
#% key: field_tev
#% type: string
#% description: Name of field with TEV value
#% key_desc : name
#% guisection: TEV
#%end
#%option 
#% key: area_tev
#% type: string
#% description: Area of TEV polygons
#% key_desc : name
#% guisection: TEV
#%end
#%option 
#% key: output_tev
#% type: string
#% description: TEV result
#% key_desc : name
#% guisection: TEV
#%end
#%option
#% key: expl
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Exploited areas [Energy/m2]
#% guisection: TEV
#%end
#%option
#% key: impact
#% type: double
#% description: Percentange of the impact
#% guisection: TEV
#% answer: 0
#%end
#%option
#% key: base
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Map of the reference situation for the impact
#% guisection: TEV
#%end
#%flag
#% key: r
#% description: Remove all operational maps
#%end

import grass.script as grass
from grass.script.core import run_command, parser,overwrite, read_command
from grass.pygrass.messages import get_msgr
import numpy as np
from grass.pygrass.raster import RasterRow
import pdb


ow = overwrite()




def remove_map(opts, flgs):


    run_command("g.remove", type="raster", flags="f", name="tot_roads")
    run_command("g.remove", type="raster", flags="f", name="tot_roads_neg")
    run_command("g.remove", type="raster", flags="f", name="frict_surf_tr1")
    run_command("g.remove", type="raster", flags="f", name="frict_surf_tr")
    run_command("g.remove", type="raster", flags="f", name="transp_dist")
    run_command("g.remove", type="raster", flags="f", name="transport_prod")
    run_command("g.remove", type="raster", flags="f", name="chipp_prod")
    run_command("g.remove", type="raster", flags="f", name="chipp_prodHF")
    run_command("g.remove", type="raster", flags="f", name="chipp_prodC")
    run_command("g.remove", type="raster", flags="f", name="extr_cost_cableC")
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
    run_command("g.remove", type="raster", flags="f", name="tot_dist")
    run_command("g.remove", type="raster", flags="f", name="yield_pix")
    run_command("g.remove", type="raster", flags="f", name="yield_pix1")
    run_command("g.remove", type="raster", flags="f", name="yield_pix2")
    run_command("g.remove", type='raster', flags='f', name='slope__')
    run_command("g.remove", type='raster', flags='f', name='slope___')
    run_command("g.remove", type='raster', flags='f', name='slope_deg__')
    run_command("g.remove", type='raster', flags='f', name='fell_HFtr1_em')
    run_command("g.remove", type='raster', flags='f', name='fell_HFtr2_em')
    run_command("g.remove", type='raster', flags='f', name='fell_proc_C_em')
    run_command("g.remove", type='raster', flags='f', name='proc_HFtr1_em')
    run_command("g.remove", type='raster', flags='f', name='fell_proc_HFtr1_em')
    run_command("g.remove", type='raster', flags='f', name='fell_proc_HFtr2_em')
    run_command("g.remove", type='raster', flags='f', name='chipp_em')
    run_command("g.remove", type='raster', flags='f', name='extr_cableHF_em')
    run_command("g.remove", type='raster', flags='f', name='extr_cableC_em')
    run_command("g.remove", type='raster', flags='f', name='extr_forw_em')
    run_command("g.remove", type='raster', flags='f', name='extr_other_em')
    run_command("g.remove", type='raster', flags='f', name='transport_em')




def yield_pix_process(opts, flgs):

    #YPIX = 'yield_pix = yield_pix1*%d + yield_pix2*%d'
    YPIX = ''

    yield_surface=opts['yield_surface']
    yield_=opts['yield1']

    expr_surf='analysis_surface='+opts['energy_map']+'>0'
    run_command('r.mapcalc', overwrite=ow,expression=expr_surf)

    # run_command("r.stats.zonal", overwrite=ow,
    #             base="compartment", cover="analysis_surface", method="sum",
    #             output="techn_pix_comp")

    run_command("r.mapcalc", overwrite=ow,  
        expression='yield_pix1 = ('+yield_+'/'+yield_surface+')*((ewres()*nsres())/10000)')


    run_command("r.null", map="yield_pix1", null=0)
    # run_command("r.mapcalc", overwrite=ow,
    #     expression='yield_pix2 = yield/(analysis_surface*techn_pix_comp)')   


    # run_command("r.mapcalc", overwrite=ow,
    #     expression=YPIX % (1 if flgs['u'] else 0, 0 if flgs['u'] else 1,))

    #run_command("r.mapcalc", overwrite=ow,expression=YPIX)


    run_command("r.mapcalc", overwrite=ow,expression="yield_pix=yield_pix1")

    #run_command("r.mapcalc",overwrite=ow,expression='yield_pix=yield_pix1*0+yield_pix2*1')

def fertility_maintenance(opts, flgs):

    energy_tops_hf=float(opts['energy_tops_hf'])
    energy_cormometric_vol_hf=float(opts['energy_cormometric_vol_hf'])  
    management=opts['management']
    treatment=opts['treatment']

    yield_pix_process(opts, flgs)

    expr_prodFF='site_prod_bioenergyFF = if(('+management+'==1 || '+management+'==2) && ('+treatment+'==1 || '+treatment+'==99999), '+opts['energy_map']+'*0.9)'
    expr_prodT='site_prod_bioenergyT = if('+treatment+'==2 && ('+opts['soilp_map']+'==1 || '+opts['soilp_map']+'==2), analysis_surface*yield_pix*%f*0+yield_pix*%f, if('+treatment+'==2 && '+opts['soilp_map']+'>2, analysis_surface*yield_pix*%f*0.7+yield_pix*%f))'
    # Fertility maintenance
    run_command("r.mapcalc", overwrite=ow, expression=expr_prodFF)
    run_command("r.mapcalc", overwrite=ow, expression=expr_prodT % (energy_tops_hf, energy_cormometric_vol_hf, energy_tops_hf, energy_cormometric_vol_hf))
    
    listmapsite=''
    map_site_prod_bioenergyT=grass.find_file('site_prod_bioenergyT',element='cell')  
    map_site_prod_bioenergyFF=grass.find_file('site_prod_bioenergyFF',element='cell') 

    if map_site_prod_bioenergyT['fullname']!='':
        listmapsite+=map_site_prod_bioenergyT['fullname']
        if map_site_prod_bioenergyFF['fullname']!='':
            listmapsite+=","+map_site_prod_bioenergyFF['fullname']
    else:
        if map_site_prod_bioenergyFF['fullname']!='':
            listmapsite+=map_site_prod_bioenergyFF['fullname']    
            
    run_command("r.mapcalc", overwrite=ow,
                expression=opts['output_fert_map']+'= max(%s)' % listmapsite)


def soil_water_protection(opts, flgs):

    energy_tops_hf=float(opts['energy_tops_hf'])
    energy_cormometric_vol_hf=float(opts['energy_cormometric_vol_hf']) 

    management=opts['management']
    treatment=opts['treatment']
    

    run_command("r.slope.aspect", flags="a", overwrite=ow,elevation=opts['dtm'], slope="slope__", format="percent") 

    yield_pix_process(opts, flgs)

    # Soil and water protection

    expr_sw1='S_W_prot_bioenergy1 = if(('+treatment+'==1 || '+treatment+'==99999) && slope__<30,'+opts['energy_map']+'*0.67,if(('+treatment+'==1 || '+treatment+'==99999) && slope__>=30, '+opts['energy_map']+'*1))'
    expr_sw2='S_W_prot_bioenergy2 = if(('+treatment+'==1 || '+treatment+'==99999) && '+opts['soild_map']+'==1,0,if(('+treatment+'==1 || '+treatment+'==99999) && '+opts['soild_map']+'!=1, '+opts['energy_map']+'*1))'
    expr_sw3='S_W_prot_bioenergy3 = if(('+treatment+'==1 || '+treatment+'==99999) && '+opts['soiltx_map']+'==3,0,if(('+treatment+'==1 || '+treatment+'==99999) && '+opts['soiltx_map']+'!=3, '+opts['energy_map']+'*1))'
    expr_sw4='S_W_prot_bioenergy4 = if(('+treatment+'==1 || '+treatment+'==99999) && ('+opts['soilcmp_map']+'==4 || '+opts['soilcmp_map']+'==5),0,if(('+treatment+'==1 || '+treatment+'==99999) && ('+opts['soilcmp_map']+'<4 || '+opts['soilcmp_map']+'>5), '+opts['energy_map']+'*1))'


    run_command("r.mapcalc", overwrite=ow,expression=expr_sw1)
    run_command("r.mapcalc", overwrite=ow,expression=expr_sw2)
    run_command("r.mapcalc", overwrite=ow,expression=expr_sw3)
    run_command("r.mapcalc", overwrite=ow,expression=expr_sw4)
    


    string_sw_prot=''
    list_sw_prot=[]
    for i in range(1,4):
        file_sw='S_W_prot_bioenergy%s' % i
        map_sw=grass.find_file(file_sw,element='cell')
        if map_sw['fullname']!='':
            list_sw_prot.append(map_sw['fullname'])
    string_sw_prot=string.join(list_sw_prot,',')   

    
    expr_sw5='S_W_prot_bioenergy5 = if('+treatment+'==2 && slope__<30,0,if('+treatment+'==2 && slope__ >=30, '+opts['energy_map']+'*1))'
    expr_sw6='S_W_prot_bioenergy6 = if('+treatment+'==2 && '+opts['soild_map']+'==1,analysis_surface*(yield_pix*%f*0+yield_pix*%f),if('+treatment+'==2 && '+opts['soild_map']+'!=1, analysis_surface*(yield_pix*%f+yield_pix*%f)))'
    expr_sw7='S_W_prot_bioenergy7 = if('+treatment+'==2 && '+opts['soiltx_map']+'==3,analysis_surface*(yield_pix*%f*0.35+yield_pix*%f),if('+treatment+'==2 && '+opts['soiltx_map']+'!=3, analysis_surface*(yield_pix*%f+yield_pix*%f)))'
    expr_sw8='S_W_prot_bioenergy8 = if('+treatment+'==2 && ('+opts['soilcmp_map']+'==4 || '+opts['soilcmp_map']+'==5),analysis_surface*(yield_pix*%f*0+yield_pix*%f),if('+treatment+'==2 && ('+opts['soilcmp_map']+'<4 || '+opts['soilcmp_map']+'>5), analysis_surface*(yield_pix*%f+yield_pix*2.1)))'

    run_command("r.mapcalc", overwrite=ow,
                expression='S_W_prot_bioenergy_FF = min(%s)' % string_sw_prot)
    run_command("r.mapcalc", overwrite=ow, expression=expr_sw5)
    run_command("r.mapcalc", overwrite=ow,
                expression=expr_sw6 % (energy_tops_hf, energy_cormometric_vol_hf, energy_tops_hf, energy_cormometric_vol_hf))
    run_command("r.mapcalc", overwrite=ow,
                expression=expr_sw7  % (energy_tops_hf, energy_cormometric_vol_hf, energy_tops_hf, energy_cormometric_vol_hf))
    run_command("r.mapcalc", overwrite=ow,
                expression=expr_sw8 % (energy_tops_hf, energy_cormometric_vol_hf, energy_tops_hf))

    string_sw_prot=''
    list_sw_prot=[]
    for i in range(5,8):
        file_sw='S_W_prot_bioenergy%s' % i
        map_sw=grass.find_file(file_sw,element='cell')
        if map_sw['fullname']!='':
            list_sw_prot.append(map_sw['fullname'])
    string_sw_prot=string.join(list_sw_prot,',')

    run_command("r.mapcalc", overwrite=ow,
                expression='S_W_prot_bioenergy_T = min(%s)' % string_sw_prot)
    run_command("r.mapcalc", overwrite=ow,
                expression=opts['output_sw_map']+' = max(S_W_prot_bioenergy_FF, S_W_prot_bioenergy_T)')





def biodiversity_maintenance(opts, flgs):
    # Biodiversity maintenance
    run_command("r.null", map='protected_areas', null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='biodiv_bioenergy = if(protected_areas>0,0,if(protected_areas==0, economic_bioenergy*1))')


def sustainable_bioenergy(opts, flgs):
    # Sustainable bioenergy
    run_command("r.mapcalc", overwrite=ow,
                expression='sustainable_bioenergy = min(site_prod_bioenergy,  S_W_prot_bioenergy,  biodiv_bioenergy)')




def avoided_CO2_emission(opts, flgs):

    vector_forest=opts['forest']
    management=opts['management']
    treatment=opts['treatment']
    roughness=opts['roughness']
    yield_=opts['yield1']
    tree_diam=opts['tree_diam']
    tree_vol=opts['tree_vol']
    soil_prod=opts['soilp2_map']
    forest_roads=opts['forest_roads']
    main_roads=opts['main_roads']
    rivers=opts['rivers']
    lakes=opts['lakes']


    if tree_diam == '':
        tree_diam="99999"
    if tree_vol == '':
        tree_vol="9.999"
    if soil_prod == '':
        soil_prod="99999"

    dhp=opts['dhp']

    #process the yield_pix map
    yield_pix_process(opts, flgs)

    #control and process the slope map
    run_command("r.slope.aspect", overwrite=ow,elevation=opts['dtm2'], slope="slope__", format="percent")
    run_command("r.slope.aspect", overwrite=ow,elevation=opts['dtm2'], slope="slope_deg__")

    run_command("r.param.scale", overwrite=ow,
                input=opts['dtm2'], output="morphometric_features",
                size=3, method="feature")

    #process the preparatory maps


    run_command("r.mapcalc", overwrite=ow,
            expression='pix_cross = ((ewres()+nsres())/2)/ cos(slope_deg__)')



    if roughness=='':
        run_command("r.mapcalc",overwrite=ow,expression='roughness=0')
        roughness='roughness'

    run_command("r.null", map="yield_pix1", null=0)
    run_command("r.null", map="morphometric_features", null=0)
    
    exprmap='frict_surf_extr = pix_cross + if(yield_pix1<=0, 99999) + if(morphometric_features==6, 99999)'
    
    if rivers!='':
        run_command("r.null", map=rivers, null=0)
        exprmap+='+ if('+rivers+'>=1, 99999)'

    if lakes!='':        
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

    run_command("r.mapcalc",overwrite=ow,expression="slope___=if(slope__<=100,slope__,100)")

    # Calculate productivity
    #view the paper appendix for the formulas
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_productHFtr1 = if('+management+' ==1 && ('+treatment+' ==1 || '+treatment+' ==99999) && '+tree_diam+' <99999,(cable_crane_extraction*(42-(2.6*'+tree_diam+'))/(-20))*1.65*(1-(slope___/100)), if('+management+' ==1 && ('+treatment+' ==1 || '+treatment+' ==99999) && '+tree_diam+' == 99999,(cable_crane_extraction*(42-(2.6*35))/(-20))*1.65*(1-(slope___/100))))')
    run_command("r.null", map="fell_productHFtr1", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_productHFtr2 = if('+management+' ==1 && '+treatment+' ==2 && '+tree_diam+' <99999,(cable_crane_extraction*(42-(2.6*'+tree_diam+'))/(-20))*1.65*(1-((1000-(90*slope___)/(-80))/100)), if('+management+' ==1 && '+treatment+' ==2 && '+tree_diam+' == 99999,(cable_crane_extraction*(42-(2.6*35))/(-20))*1.65*(1-((1000-(90*slope___)/(-80))/100))))')
    run_command("r.null", map="fell_productHFtr2", null=0)
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_productC = if('+management+' ==2 && '+soil_prod+' <99999,((0.3-(1.1*'+soil_prod+'))/(-4))*(1-(slope___/100)), if('+management+' ==2 && '+soil_prod+' == 99999,((0.3-(1.1*3))/(-4))*(1-(slope___/100))))')
    run_command("r.null", map="fell_proc_productC", null=0)
    ###### check fell_proc_productC ######

    #9999: default value, if is present take into the process the average value (in case of fertility is 33)

    #r.mapcalc --o 'fell_proc_productC = if(management@PERMANENT ==2 && soil_prod@PERMANENT <99999,((0.3-(1.1*soil_prod@PERMANENT))/(-4))*(1-(slope@PERMANENT/100)), if(management@PERMANENT ==2 && soil_prod@PERMANENT == 99999,((0.3-(1.1*3))/(-4))*(1-((1000-(90*slope@PERMANENT)/(-80))/100))))'



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
    #run_command("r.null", map=dhp, null=0)
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

    # Avoided carbon dioxide emission
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_HFtr1_em = yield_pix/fell_productHFtr1*4.725')
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_HFtr2_em = yield_pix/fell_productHFtr2*4.725')
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_C_em = yield_pix/fell_proc_productC*2.363')
    run_command("r.mapcalc", overwrite=ow,
                expression='proc_HFtr1_em =  yield_pix/proc_productHFtr1*37.729')
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_HFtr1_em = yield_pix/fell_proc_productHFtr1*36.899')
    run_command("r.mapcalc", overwrite=ow,
                expression='fell_proc_HFtr2_em = yield_pix/fell_proc_productHFtr2*36.899')
    run_command("r.mapcalc", overwrite=ow,
                expression='chipp_em = chipp_prod*130.599')
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_cableHF_em = yield_pix/extr_product_cableHF*20.730')
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_cableC_em = yield_pix/extr_product_cableC*12.956')
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_forw_em = yield_pix/extr_product_forw*25.394')
    run_command("r.mapcalc", overwrite=ow,
                expression='extr_other_em = yield_pix/extr_product_other*15.548')
    run_command("r.mapcalc", overwrite=ow,
                expression='transport_em =  transport_prod*24.041')
    run_command("r.null", map='fell_HFtr1_em', null=0)
    run_command("r.null", map='fell_HFtr2_em', null=0)
    run_command("r.null", map='fell_proc_C_em', null=0)
    run_command("r.null", map='proc_HFtr1_em', null=0)
    run_command("r.null", map='fell_proc_HFtr1_em', null=0)
    run_command("r.null", map='fell_proc_HFtr2_em', null=0)
    run_command("r.null", map='chipp_em', null=0)
    run_command("r.null", map='extr_cableHF_em', null=0)
    run_command("r.null", map='extr_cableC_em', null=0)
    run_command("r.null", map='extr_forw_em', null=0)
    run_command("r.null", map='extr_other_em', null=0)
    run_command("r.null", map='transport_em', null=0)
    run_command("r.mapcalc", overwrite=ow, expression=opts['output_co2_map']+' = (analysis_surface*(fell_HFtr1_em  + fell_HFtr2_em + fell_proc_C_em + proc_HFtr1_em + fell_proc_HFtr1_em + fell_proc_HFtr2_em + chipp_em + extr_cableHF_em + extr_cableC_em + extr_forw_em + extr_other_em + transport_em))/1000')
    run_command("r.mapcalc", overwrite=ow, expression=opts['output_aco2_map']+' = '+opts['energy_map']+'*320')
    #run_command("r.mapcalc", overwrite=ow, expression=opts['output_netco2_map']+' = analysis_surface*'+('+opts['output_aco2_map']+' - '+opts['output_co2_map']+')/1000')
    run_command("r.mapcalc", overwrite=ow, expression=opts['output_netco2_map']+' = analysis_surface*('+opts['output_aco2_map']+' - '+opts['output_co2_map']+')/1000')

    mapco2=opts['output_co2_map']
    with RasterRow(mapco2) as pT:
        T = np.array(pT)

    mapaco2=opts['output_netco2_map']
    with RasterRow(mapaco2) as pT1:
        A = np.array(pT1)
   
    print ("Total emission (Tons): %.2f" % np.nansum(T))
    print ("Total avoided emission (Tons): %.2f" % np.nansum(A))


def fire_risk_reduction(opts, flgs):
    # Fire risk reduction
    expr_surf='analysis_surface='+opts['energy_map']+'>0'
    run_command('r.mapcalc', overwrite=ow,expression=expr_surf)
    run_command("r.mapcalc", overwrite=ow, expression=opts['output_fr_map']+' = if(analysis_surface==1,'+opts['firerisk_map']+'*0.7, '+opts['firerisk_map']+'*1)')


def recreational_improvement(opts, flgs):
    # Recreational improvement
    expr_surf='analysis_surface='+opts['energy_map']+'>0'
    run_command('r.mapcalc', overwrite=ow,expression=expr_surf)
    run_command("r.mapcalc", overwrite=ow, expression=opts['output_tot_re_map']+' = (ewres()*nsres()/10000)*'+opts['touristic_map'])
    run_command("r.mapcalc", overwrite=ow, expression=opts['output_imp_re_map']+' = if(analysis_surface==1,(ewres()*nsres()/10000)*'+opts['touristic_map'])


def tev(opts,flgs):


    TEV = opts['tev']
    field_tev=opts['field_tev']
    expl = opts['expl']
    impact = opts['impact']
    base = opts['base']
    res = opts['output_tev']
    area_tev = opts['area_tev']


    forest_split=str.split(TEV,'@')

    fields=str.split(read_command('db.columns', table=forest_split[0]),"\n")


    vol_matching = [s for s in fields if field_tev in s]

    vol_matching2 = [s for s in fields if area_tev in s]

    #pdb.set_trace()

    if (len(vol_matching)<1) or (len(vol_matching2<1)) :
        #get_msgr().fatal("Field in vector TEV map not found")
        print "Errors in fields of TEV map"
        return

    run_command("v.to.rast", overwrite=ow, input=TEV,
                output="tev1", use="attr", attrcolumn=field_tev)

    run_command("v.to.rast", overwrite=ow, input=TEV,
                output="tev_area", use="attr", attrcolumn=area_tev)

    run_command("r.mapcalc", overwrite=ow, expression='tev_map=(tev1/tev_area)*ewres()*nsres()')

    TEV2="tev_area"

    if base:
        formula_tev = "%s=if(%s>0, %s-%f*%s/%s*%s)" % (res, expl, TEV2, impact,
                                                   expl, base, TEV2)
    else:
        formula_tev = "%s=if(%s>0, %s-%f*%s)" % (res, expl, TEV2, impact, expl,
                                             base, TEV2)
    mapcalc(formula_tev, overwrite=True)

    with RasterRow(TEV2) as pT:
        T = np.array(pT)
    with RasterRow(res) as pR:
        R = np.array(pR)

    print("_________")
    print("IMPACT")
    print("_________")
    print("Total value at the beginning %.2f" % np.nansum(T))
    print("Total value after the exploitation %.2f" % np.nansum(R))


def main(opts, flgs):

    # if(opts['output_fert_map'])!="":
    #     fertility_maintenance(opts, flgs)

    if(opts['output_sw_map'])!="":
        soil_water_protection(opts, flgs)
    
    # biodiversity_maintenance(opts, flgs)
    # sustainable_bioenergy(opts, flgs)

    if(opts['output_co2_map'])!="":        
        avoided_CO2_emission(opts, flgs)

    if(opts['output_fr_map'])!="":        
        fire_risk_reduction(opts, flgs)

    if(opts['output_tot_re_map'])!="":        
        recreational_improvement(opts, flgs)

    if(opts['output_tev'])!="":        
        tev(opts, flgs)

    if flgs['r'] == True:
         remove_map(opts, flgs)



if __name__ == "__main__":
    main(*parser())
