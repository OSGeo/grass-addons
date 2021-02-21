#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.land.assess.py
# AUTHOR(S):		Isaac Ullah, Michael Barton, Arizona State University
# PURPOSE:		Assess which land cells agents will use, and creates output impacts maps, and adjusts landcover and soil fertility according to agent impacts.
#               	
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
# COPYRIGHT:		(C) 2012 by Isaac Ullah, Michael Barton, Arizona State University
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: Assess which land cells agents will use, and creates output impacts maps, and adjusts landcover and soil fertility according to agent impacts.
#%END

#%option
#% key: inputdata
#% type: string
#% description: HH#, Village#, HH Population, # Wheat plots, # Barley Plots, # of Grazing plots[; HH#, Village#, ...; etc...]
#% multiple: yes
#% required : yes
#%END

#%option
#% key: precip
#% type: string
#% description: Meters of precipitation in the region
#% required : yes
#%END

#%option
#% key: maxbarley
#% type: string
#% description: Maximum barley yield that can be possibly achieved (kg/ha)
#% required : yes
#%END

#%option
#% key: maxwheat
#% type: string
#% description: Maximum wheat yield that can be possibly achieved (kg/ha)
#% required : yes
#%END

#%option
#% key: wooduse
#% type: string
#% description: Number of kilograms of wood used per person per year
#% answer: 1662.98
#% required : yes
#%END

#%option
#% key: ocdensity
#% type: string
#% description: Ovicaprid density factor (percent stocking capacity, 0-1)
#% answer: 3
#% required : yes
#%END

#%option
#% key: degrade_rate
#% type: string
#% description: Rate at which farming degrades soil fertility (in percentage points per year)
#% answer: 3
#% required : yes
#%END

#%option
#% key: recovery
#% type: string
#% gisprompt: string
#% description: Rate at which soil recovers it's fertility per cycle (in percentage points per year)
#% answer: 2
#% required : yes
#%END

#%option
#% key: intensity
#% type: string
#% description: intensity of woodgathering (kilograms of wood gathered per square meter per year)
#% answer: 0.08
#% required : yes
#%END

#%option
#% key: wooddistweight
#% type: string
#% description: Distance weighting factor for the woodgathering evaluation equation (higher wooddistweight will make smaller woodgathering catchments)
#% answer : 3
#% required : yes
#%END

#%option
#% key: gdistweight
#% type: string
#% description: Distance weighting factor for grazing evaluation equation (gdistweight higher than lcovweight will make larger grazing catchments)
#% answer : 1
#% required : yes
#%END

#%option
#% key: lcovweight
#% type: string
#% description: Landcover weighting factor for grazing evaluation equation (lcovweight higher than gdistweight will make smaller grazing catchments)
#% answer : 1
#% required : yes
#%END

#%option
#% key: fdistweight
#% type: string
#% description: Distance weighting factor for farming evaluation equation (higher value of fdistweight will make smaller agricultural catchments)
#% answer : 1
#% required : yes
#%END

#%option
#% key: sfertilweight
#% type: string
#% description: Soil fertility weighting factor for farming evaluation equation (sfertilweight higher than sdepthweight gives preference to soil fertility in farm plot choice)
#% answer : 1
#% required : yes
#%END

#%option
#% key: sdepthweight
#% type: string
#% description: Soil depth weighting factor for farming evaluation equation (sdepthweight higher than sfertilweight gives preference to soil depth in farm plot choice)
#% answer : 1
#% required : yes
#%END

#%option
#% key: maxfarmcost
#% type: string
#% description: Maximum cost distance that a farmer is willing to walk to get to a farming plot (in seconds of walking time)
#% answer: 10800
#% required : yes
#%END

#%option
#% key: maxgrazecost
#% type: string
#% description: Maximum cost distance that a shepherd is willing to walk to get to a grazing plot (in seconds of walking time)
#% answer: 28800
#% required : yes
#%END

#%option
#% key: maxlcov
#% type: string
#% gisprompt: string
#% description: Maximum landcover value
#% answer: 50
#% required : yes
#%END

#%option
#% key: farmval
#% type: string
#% gisprompt: string
#% description: Landcover value for farmed plots
#% answer: 5
#% required : yes
#%END

#%option
#% key: farmbreaks
#% type: string
#% description: Farming landcover devaluation remapping pairs in the form: "x1,y1;x2,y2" where x is a landcover value (between farmval and maxlcov), and y is a devaluation number between 0 and 100. (Two pairs are needed, with the lower landcover value first. The second landcover value should be the same as maxlcov).
#% answer: 30,25;50,90
#% required : yes
#%END

#%option
#% key: dropval
#% type: string
#% description: Fertility value at which tenured land will be dropped (0-100). Will only be used if -t flag enabled. NOTE: This doesn't do anything yet.
#% answer: 40
#% required : yes
#%END

#%option
#% key: slope
#% type: string
#% gisprompt: old,cell,raster
#% description: Input slope map
#% required : yes
#%END

#%option
#% key: lcov
#% type: string
#% gisprompt: old,cell,raster
#% description: Input landcover map (values coded 0-maxlcov)
#% required : yes
#%END

#%option
#% key: sfertil
#% type: string
#% gisprompt: old,cell,raster
#% description: Map of current soil fertility (values coded 0-100)
#% required : yes
#%END

#%option
#% key: sdepth
#% type: string
#% gisprompt: old,cell,raster
#% description: Map of current soil depths (in meters)
#% required : yes
#%END

#%option
#% key: villageland
#% type: string
#% gisprompt: old,cell,raster
#% description: Map of the area taken up by the village(s) (village cells should be coded "40", and all others should be NULL)
#% required : yes
#%END

#%option
#% key: costsurfs
#% type: string
#% gisprompt: old,cell,raster
#% description: Input map(s) of walking costs from village locations (as output from r.walk, comma sep for multiple). !!!NOTE!!! The list of cost-surface maps MUST be in ascending order starting with Village 0!!!
#% multiple: yes
#% required : yes
#%END

#%option
#% key: prefix
#% type: string
#% gisprompt: string
#% description: Name-stem of all other output maps
#% required : yes
#%END

#%option
#% key: prevyr
#% type: string
#% gisprompt: string
#% description: Name-stem (prefix) from the previous year (needed for land tenure assessment) NOTE: this doesn't do anything yet
#% required : yes
#%END

#%option
#% key: out_lcov
#% type: string
#% gisprompt: string
#% description: Name of output landcover map
#% required : yes
#%END

#%option
#% key: out_fertil
#% type: string
#% gisprompt: string
#% description: Name of output soil fertility map
#% required : yes
#%END

#%option
#% key: out_impacts
#% type: string
#% gisprompt: string
#% description: Name of output agent impacts map (for display)
#% required : yes
#%END

#%option
#% key: lc_rules
#% type: string
#% description: Path to reclass rules file for making a "labels" map. If no rules specified, no labels map will be made.
#% answer:
#% required : no
#%END

#%option
#% key: lc_color
#% type: string
#% description: Path to color rules file for landcover map
#% answer:
#% required : no
#%END

#%option
#% key: sf_color
#% type: string
#% gisprompt: string
#% description: path to color rules file for landcover map
#% answer:
#% required : yes
#%END

#%option
#% key: statsfile
#% type: string
#% gisprompt: string
#% description: Name of stats file where landcover stats will be written (NOTE. Include directory path. If the file already exists in the specified location, stats from the current year will be automatically appended to the last line of the existing stats file. )
#% required : no
#%END

#%option
#% key: fertilstats
#% type: string
#% gisprompt: string
#% description: Name of stats file where soil fertilty stats will be written (NOTE. Include directory path. If the file already exists in the specified location, stats from the current year will be automatically appended to the last line of the existing stats file.)
#% required : no
#%END

#%flag
#% key: t
#% description: -t Implement land tenuring (households keep farming same cells for multiple years) NOTE: Currently, this simply disenables yearly randomization of household land choosing order in the "round robin" land grab. This doesn't ensure land tenureing, but it makes it more likely that a household will get the same patches of land from year to year when the population is stable.
#%END

#%flag
#% key: b
#% description: -b Keep a map of above-ground biomass
#%END


import sys
import os
import tempfile
import random
import math
from operator import itemgetter
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass

#returns the median value from a list of numeric values (float or int) **Note that I choose to use this custom class over the need to rely on external library numpy**
def getMedian(numericValues):
    theValues = sorted(numericValues)
    count = len(theValues)
    if count % 2 == 1:
        return theValues[(count+1)/2-1]
    else:
        lower = theValues[count/2-1]
        upper = theValues[count/2]
        return (float(lower + upper)) / 2

##NOTES: 1) If the amount of wood gathered from newly cleared farm fields (swiddenwood) is more than what the village needs, then the "woodgathering impacts" map will be null. This will almost always happen the first year, and could also occur for any years iwhere many new plots are cleared. 2) If the vegetation regrowth rate for a cell is very high and the grazing density isn't very high, then there will NO net impacts from grazing. With low densities, this may continue indefinitely in the areas outside the farming catchment, and the only areas that you'll see an effect from grazing will be areas that were previously farmed and now have low fertility/depth, and thus a lowered regrowth rate. 3) Some of the land patch choice equations, and the biomass recode rules have been hardcoded to our mediterranean vegetation succession scheme. If the model is going to be used outside of the Mediterranean zone, these hardcoded values will have to be changed. I have made a note where such hardcoded values have been used.

#main block of code starts here
def main():
    #setting up variables for use later on
    statsfile = os.getenv('GIS_OPT_statsfile') 
    fertilstats = os.getenv('GIS_OPT_fertilstats') 
    lcov = os.getenv('GIS_OPT_lcov') 
    slope = os.getenv('GIS_OPT_slope')
    inputdata = os.getenv('GIS_OPT_inputdata').split(";") 
    #Key to inputdata: HH Number, Village number, Population, # Wheat plots, # Barley plots, # grazing plots[; HH Number, Village number, ....,# grazing plots; etc...]
    villageland = os.getenv('GIS_OPT_villageland')
    sfertil = os.getenv('GIS_OPT_sfertil') 
    sdepth = os.getenv('GIS_OPT_sdepth') 
    prefix = os.getenv('GIS_OPT_prefix') 
    prevyr = os.getenv('GIS_OPT_prevyr') 
    maxwheat = float(os.getenv('GIS_OPT_maxwheat'))
    maxbarley = float(os.getenv('GIS_OPT_maxbarley'))
    maxfarmcost = os.getenv('GIS_OPT_maxfarmcost')
    maxgrazecost = os.getenv('GIS_OPT_maxgrazecost')
    wooddistweight = os.getenv('GIS_OPT_wooddistweight')
    gdistweight = float(os.getenv('GIS_OPT_gdistweight'))
    lcovweight = float(os.getenv('GIS_OPT_lcovweight'))
    fdistweight = float(os.getenv('GIS_OPT_fdistweight'))
    sfertilweight = float(os.getenv('GIS_OPT_sfertilweight'))
    sdepthweight = float(os.getenv('GIS_OPT_sdepthweight'))
    precip = float(os.getenv('GIS_OPT_precip'))
    ocdensity = float(os.getenv('GIS_OPT_ocdensity'))
    wooduse = (float((os.getenv("GIS_OPT_wooduse"))))
    intensity = (float((os.getenv("GIS_OPT_intensity"))))
    maxlcov = os.getenv('GIS_OPT_maxlcov')
    farmval = float(os.getenv('GIS_OPT_farmval'))
    farmbreaks = os.getenv('GIS_OPT_farmbreaks').split(";") 
    dropval = float(os.getenv('GIS_OPT_dropval'))
    degrade_rate = float(os.getenv('GIS_OPT_degrade_rate'))
    recovery = os.getenv('GIS_OPT_recovery')
    costlist = os.getenv("GIS_OPT_costsurfs").split(',')
    sf_color = os.getenv('GIS_OPT_sf_color')
    lc_rules = os.getenv('GIS_OPT_lc_rules')
    lc_color = os.getenv('GIS_OPT_lc_color')

    region = grass.region()
    cellperhectare = 100000 / (float(region['nsres']) * float(region['ewres']))
    cellpersqm = 1 / (float(region['nsres']) * float(region['ewres']))

    #Setting names for some files
    slopeval = "tempry_Slope_Evaluation_Factor_map_" + prefix
    depthval = "tempry_Depth_Evaluation_Factor_map_" + prefix
    fertval = "tempry_Fertility_Evaluation_Factor_map_" + prefix
    lcovval = "tempry_Landcover_Evaluation_Factor_map_" + prefix
    flcovval = "tempry_Farming_Landcover_Evaluation_Factor_map_" + prefix
    gwimpactsmap_lcov = "tempry_All_Vils_Graz_Wdgath_Imp_Map_" + prefix
    gwimpactsmap_biomass = "tempry_All_Vils_Graz_Wdgath_biom_Imp_Map_" + prefix
    gimpactsmap ="tempry_All_Vils_Graz_Imp_Map_" + prefix
    wimpactsmap ="tempry_All_Vils_Wdgath_Imp_Map_" + prefix
    fimpactsmap ="tempry_All_Vils_Frmng_Imp_Map_" + prefix
    temp_rate = "tempry_lcover_regrowth_rates_" + prefix
    temp_reclass = "tempry_rclass_lcover_labels_" + prefix
    tempwheatreturn = "tempry_wheat_return_" + prefix
    tempbarleyreturn = "tempry_barley_return_" + prefix

    prevtenure = prevyr + "_Land_Tenure_map"
    landtenurename = prefix + "_Land_Tenure_map"
    wheatreturnsname = prefix + "_Wheat_Returns_map"
    barleyreturnsname = prefix + "_Barley_Returns_map"
    grazereturnsname = prefix + "_Grazing_Returns_map"
    biomass = prefix + "_Above_Ground_Biomass_map"
    out_impacts = os.getenv('GIS_OPT_out_impacts')
    out_lcov = os.getenv('GIS_OPT_out_lcov')
    reclass_out = out_lcov + "_labels"
    out_fertil = os.getenv('GIS_OPT_out_fertil')

    #Set up some recode rules for tranlating veg type into above ground biomass and back
    #NOTE: The following two recode rules have landcover values HARDCODED to Mediterranean values. When reparammeterizing for non-Mediterranean environments, these will need to be recoded.
    recodeto = tempfile.NamedTemporaryFile()
    recodeto.write('0.000:5.000:0.000:0.100\n5.000:18.500:0.100:0.660\n18.500:35.000:0.660:0.740\n35.000:50.000:0.740:1.910')
    recodeto.flush()
    recodefrom = tempfile.NamedTemporaryFile()
    recodefrom.write('0.000:0.100:0.000:5.000\n0.100:0.660:5.000:18.500\n0.660:0.740:18.500:35.000\n0.740:1.910:35.000:50.000')
    recodefrom.flush()
    #Calculate some temporary regression maps/values to be used in the individual valuation equations below
    grass.mapcalc("${slopeval}=if(${slope} <= 10, 1.0, if(${slope} <= 20, 0.75, if(${slope} <= 60, 0.25, 0.0)))", quiet = "True", slopeval = slopeval, slope = slope)
    grass.mapcalc("${depthval}=eval(x=(100*((0.28 * log(${sdepth})) + 0.87)), if(x > 100, 100, x))", quiet = "True", depthval = depthval, sdepth = sdepth)    
    grass.mapcalc("${fertval}=eval(x=100*((0.19 * log(${sfertil}/100)) + 1), if(x > 100, 100, x))", quiet = "True", fertval = fertval, sfertil = sfertil)
    rainval = 100.0*((0.51 * math.log(float(precip))) + 1.03)
    #NOTE: The following equation has landcover values HARDCODED to Mediterranean values. When reparammeterizing for non-Mediterranean environments, these will need to be recoded.
    grass.mapcalc("${lcovval}=if(${lcov} == 40 || ${lcov} == 41, 39, if(${lcov} == 42 || ${lcov} == 43, 38, if(${lcov} == 44 || ${lcov} == 45, 37, if(${lcov} == 46 || ${lcov} == 47, 36, if(${lcov} == 48 || ${lcov} == 49 || ${lcov} == 50, 35, ${lcov})))))", quiet = "True", lcovval = lcovval, lcov = lcov)
    grass.mapcalc("${flcovval}=graph(${lcov}, 0,0, ${farmval},0, ${farmbreak1}, ${farmbreak2})", quiet = "True", flcovval = flcovval, lcov = lcov, farmval = farmval, farmbreak1 = farmbreaks[0], farmbreak2 = farmbreaks[1])
    #Calculate the wheat yield map (kg/cell)
    grass.mapcalc("${tempwheatreturn}=eval(x=(0.51*log(${precip}))+1.03, y=(0.28*log(${sfertil}))+0.87, z=(0.19*log(${sdepth}))+1, ((((x*y*z)/3)*${slopeval}*${maxwheat})/${cellperhectare}))", quiet = "True", tempwheatreturn = tempwheatreturn, precip = precip, sfertil = sfertil, sdepth = sdepth, slopeval = slopeval, maxwheat = maxwheat, cellperhectare = cellperhectare)
    grass.mapcalc("${wheatreturnsname}=if(${tempwheatreturn} < 0, 0, ${tempwheatreturn})", quiet = "True", wheatreturnsname = wheatreturnsname, tempwheatreturn = tempwheatreturn)
    #Calculate barley yield map (kg/cell)
    grass.mapcalc("${tempbarleyreturn}=eval(x=(0.48*log(${precip}))+1.51, y=(0.34*log(${sfertil}))+1.09, z=(0.18*log(${sdepth}))+0.98, ((((x*y*z)/3)*${slopeval}*${maxbarley})/${cellperhectare}))", quiet = "True", tempbarleyreturn = tempbarleyreturn, precip = precip, sfertil = sfertil, sdepth = sdepth, slopeval = slopeval, maxbarley = maxbarley, cellperhectare = cellperhectare)
    grass.mapcalc("${barleyreturnsname}=if(${tempbarleyreturn} < 0, 0, ${tempbarleyreturn})", quiet = "True", barleyreturnsname = barleyreturnsname, tempbarleyreturn = tempbarleyreturn)
    #Calculate the grazing yield map (kg/cell)
    #NOTE: The following equation has landcover values HARDCODED to Mediterranean values. When reparammeterizing for non-Mediterranean environments, these will need to be recoded.
    grass.mapcalc("${grazereturnsname}=eval(x=if(${lcov} >= 40, 800-(10*${lcov}), if(${lcov} < 40 && ${lcov} >= 27, (27.27*${lcov})-663.64, if(${lcov} < 27 && ${lcov} >=4, (2.27*${lcov})+38.64, if(${lcov} < 4 && ${lcov} >=1, (12.5*${lcov}), 0)))), (x/${cellperhectare})*${ocdensity})", quiet = "True", grazereturnsname = grazereturnsname, lcov = lcov, cellperhectare = cellperhectare, ocdensity = ocdensity)
    #Calculate the standing biomass map (kg/sq m)
    grass.run_command('r.recode', quiet = 'True', input = lcov, output = biomass, rules = recodeto.name)
    #Set up a master list of nested lists of villages, households, and input parameters. This list will be used to control everything. 
    ##Example structure of masterlist: [{'costmap': 'map1', 'houses': [[list of info], [list of info], [list of info]]}, {'costmap': 'map2', 'houses': [[list of info], [list of info], [list of info]]}, {'costmap': 'map3', 'houses': [[list of info], [list of info], [list of info]]}]. Each dictionary {} is a village.
    ##Key to "list of info" in any "house" of any "village": [0] HH Number, [1] Village number, [2] Population, [3] # Wheat Plots, [4] # Barley Plots, [5] # grazing plots
    #NOTE! It is VERY important that the list of cost-surface maps in the input variable "costsurfs" be in order starting with Village 0!!! This is a fundamental assumption used to set up the masterlist and coordinate the inputdata from each village to the proper cost map.
    masterlist = []
    for number, costmap in enumerate(costlist):
        masterlist.append({})
        masterlist[number]["costmap"] = costmap
        masterlist[number]["houses"] = []
        for item in inputdata:
            if item.split(',')[1] == str(number):
                masterlist[number]["houses"].append(item.split(','))
    #set up an output dictionary for the values that will get passed back to AP-Sim
    outputdict = {}

    #------------------Do farming routine
    wimpactsmaplist = []
    bimpactsmaplist = []
    fimpactsmapslist = []
    #create temporary file to store land tenure information from this year
    tenuretemp = tempfile.NamedTemporaryFile()
    #see if we want to randomize the villages for this year or not...
    if os.getenv('GIS_FLAG_t') == '1':
        pass
    else:
        #randomly shuffle the masterlist of villages so the same one doesn't get to pick their farming land first every year
        random.shuffle(masterlist)
    for village in masterlist:
        #generate the proper map names and update the list of maps
        agvalname = prefix + "_V" + str(village["houses"][0][1]) + "_ag_land_value"
        #get some stats on the current cost map
        costdict = {}
        costdict = grass.parse_command('r.univar', flags = 'g', map = village["costmap"])
        #Calculate the agricultural land evaluation map for making decisions on. Note that grazing cannot take place on land that is being farmed, on land occupied by village buildings, or on land that it too far away. Also note that we are forbidding agents from farming on land already chosen by another village. This logic is necessary b/c we are modeling an entire years' worth of decision in one single step. To compensate for this, we randomize the order of the villages from year to year so that each village will have an equal chance to get the first pick in any given year.
        #also note that -a flag is accounted for here. When flag is enabled, there will be no preference for plots with already reduced landcover (i.e., with no trees to cut down).

        if len(fimpactsmapslist) == 0:
            grass.mapcalc("${agvalname}=if(${sfertil} == 0.0 || ${depthval} == 0.0 || ${slopeval} == 0.0, 0.0, if(${costmap} <= ${maxfarmcost} && isnull(${villageland}), ${slopeval} * (  (  ( (${sfertilweight} * ${sfertil}) + (${sdepthweight} * ${depthval}) ) / (${sfertilweight} + ${sdepthweight}) ) - (${fdistweight} * (${costmap} / ${maxcost}) ) ), null() ) )", quiet = "True", agvalname = agvalname, maxfarmcost = maxfarmcost, sfertil = sfertil, slopeval = slopeval, depthval = depthval, costmap = village["costmap"], maxcost = costdict["max"], fdistweight = fdistweight, sfertilweight = sfertilweight, sdepthweight = sdepthweight, villageland = villageland)
        else:
            grass.mapcalc("${agvalname}=if(${sfertil} == 0.0 || ${depthval} == 0.0 || ${slopeval} == 0.0, 0.0, if(${costmap} <= ${maxfarmcost} && isnull(${villageland}) && isnull(${fimpactsmaps}), ${slopeval} * (  (  ( (${sfertilweight} * ${sfertil}) + (${sdepthweight} * ${depthval}) ) / (${sfertilweight} + ${sdepthweight}) ) - (${fdistweight} * (${costmap} / ${maxcost}) ) ), null() ))", quiet = "True", agvalname = agvalname, maxfarmcost = maxfarmcost, sfertil = sfertil, slopeval = slopeval, depthval = depthval, costmap = village["costmap"], maxcost = costdict["max"], fdistweight = fdistweight, sfertilweight = sfertilweight, sdepthweight = sdepthweight, villageland = villageland, fimpactsmaps = " + ".join(fimpactsmapslist))
        #Grab the x, y, and value of all cells in the farm value and wheat and barley returns maps for the village, and rank that list in order from least to most desireable
        agval1 = grass.read_command("r.stats", quiet = "True", flags = '1gn', input = agvalname + ',' + wheatreturnsname + ',' + barleyreturnsname, fs = ',').splitlines()
        agvalues = []
        for item in agval1:
            templist = []
            for thing in item.split(','):
                templist.append(float(thing))
            agvalues.append(templist)
        #This has made a list of: [0] x, [1] y, [2] ag land value, [3] wheat return value, [4] barley return value. 
        #Now sort the list in place:
        agvalues.sort(key=itemgetter(2))
        #see if we want to randomize the villages for this year or not...
        if os.getenv('GIS_FLAG_t') == '1':
            pass
        else:
            #randomly shuffle the list of households so the same one doesn't get to "go first" every year
            random.shuffle(village["houses"])
        #Create some lists and dictionaries. Some of these will be our loop timing and control criteria, and some are containters for output data. 1) figure out how many individual farmplots and grazeplots are wanted by all households in the village, 2) list of  how many farm and graze plots each house wants, and 3) add placemark entries into the output dictionary to eventually hold the data. 
        outputdict[village["houses"][0][1]] = {}
        villagepop = 0
        numwheatplots = 0
        numbarleyplots = 0
        wheatplotslist = []
        barleyplotslist = []
        #For each house, figure out how many plots are for wheat, and pick the best plots for those. The remaining plots will be for barley. 
        for house in village["houses"]:
            villagepop = villagepop + int(house[2])
            numwheatplots = numwheatplots + int(house[3])
            numbarleyplots = numbarleyplots + int(house[4])
            wheatplotslist.append(range(int(house[3])))
            barleyplotslist.append(range(int(house[4])))
            #set up some blank lists linked to a key for each house in this village in the output dictionary that will hold the results of the farm and graze plot choice routine. The dictionary is set up like this: {(village)1: {(hh)1: {"farmplots": [[x, y, agval, wheatreturns, barleyreturns], [...], ...]; "grazeplots": [[x, y, grazval, grazereturns], [...], ...]}; {(hh)2: {"wheatplots": [[x, y, agval, wheatreturns, barleyreturns], [...], ...]; "barleyplots": [[x, y, agval, wheatreturns, barleyreturns], [...], ...]; "grazeplots": [[x, y, grazval, grazereturns], [...], ...]}}; (village)2: {(hh)1: {"farmplots"...etc... }}} so that the list of farming plots for village 2, household 3, for example, can be obtained by this key structure: outputdict[2][3]["farmplots"]. Remember that each plot is itself a list of x, y, and values: [234555.5, 456677.3, 39.2, 345], so to get the x coordinate of the third-ranked farm plot for village 2, household 3,you use this key structure: outputdict[2][3]["farmplots"][2][0], and similarly, the y coordinate of that plot: outputdict[2][3]["farmplots"][2][1]
            outputdict[house[1]][house[0]] = {}
            outputdict[house[1]][house[0]]["wheatplots"] = []
            outputdict[house[1]][house[0]]["barleyplots"] = []
        outputdict[village["houses"][0][1]]["villagepop"] = villagepop
        #now, loop through the total number of needed plots, popping out the x,y,value information and updateing lists for each household. There are controls that are set up so that each household gets the number it desired. 
        #households use their best land for wheat farming, so allocate the highest ranked farmplots in the "wheatplots" dictionary item 
        for num in range(numwheatplots):
            for house, wheatplots in zip(village["houses"], wheatplotslist):
                #if there are no more wheat plots needed by this particular house, then skip it and go on to the next house until all houses have what they want
                if len(wheatplots) == 0:
                    pass
                else:
                    wheatplots.remove(wheatplots[0])
                    outputdict[house[1]][house[0]]["wheatplots"].append(agvalues.pop())
                #if we've run out of land then we break out of the loop and the remaining households' needs will not be fulfilled.
                if len(agvalues) == 0:
                    break
        #after wheat is taken care of, take the next best pieces of land and put them in the "barleyplots" dictionary item
        for num in range(numbarleyplots):
            for house, barleyplots in zip(village["houses"], barleyplotslist):
                #if there are no more barley plots needed by this particular house, then skip it and go on to the next house until all houses have what they want
                if len(barleyplots) == 0:
                    pass
                else:
                    #if we've run out of land then we break out of the loop and the remaining households' needs will not be fulfilled.
                    if len(agvalues) == 0:
                        break
                    else:
                        barleyplots.remove(barleyplots[0])
                        outputdict[house[1]][house[0]]["barleyplots"].append(agvalues.pop())
        #now make the impact map of agriculture for the village
        #Make a temp file so we can get the impacts data into grass as a map via r.in.xyz
        a = tempfile.NamedTemporaryFile()
        b = tempfile.NamedTemporaryFile()
        wimpactsmapname = prefix + "_V" + str(village["houses"][0][1])  +  "_wheat_impacts" 
        bimpactsmapname = prefix + "_V" + str(village["houses"][0][1])  +  "_barley_impacts"        
        fimpactsmapname = prefix + "_V" + str(village["houses"][0][1])  +  "_farming_impacts"
        fimpactsmapslist.append(fimpactsmapname)
        for house in village["houses"]:
            for item in outputdict[house[1]][house[0]]["wheatplots"]:
                write1 = a.write("%s|%s|1\n" % (item[0], item[1]))
                write2 = tenuretemp.write("%s|%s|%s\n" % (item[0], item[1], house[0]))
            success1 = a.flush()
            success2 = tenuretemp.flush()
        creating = grass.run_command('r.in.xyz', quiet = "True", input = a.name, output = wimpactsmapname, x = '1', y = '2', z = '3', type = 'DCELL')
        success3 = a.close()
        grass.run_command('r.colors', quiet = "True", map = wimpactsmapname, color = 'bgyr')
        for house in village["houses"]:            
            for item in outputdict[house[1]][house[0]]["barleyplots"]:
                write1 = b.write("%s|%s|2\n" % (item[0], item[1], house[0]))
                write2 = tenuretemp.write("%s|%s|%s\n" % (item[0], item[1], house[0]))
            success1 = b.flush()
            success2 = tenuretemp.flush()
        creating = grass.run_command('r.in.xyz', quiet = "True", input = b.name, output = bimpactsmapname, x = '1', y = '2', z = '3', type = 'DCELL')
        success3 = b.close()
        grass.run_command('r.colors', quiet = "True", map = bimpactsmapname, color = 'bgyr')
        grass.run_command('r.patch', quiet = "True", input = bimpactsmapname + ',' + wimpactsmapname, output = fimpactsmapname)
        grass.run_command('r.colors', quiet = "True", map = fimpactsmapname, color = 'bgyr')
    #Patch all the villages' impacts maps together to make a single maps for all villages...
    if len(fimpactsmapslist) > 1:
        grass.run_command('r.patch', quiet = "True", input =  ",".join(fimpactsmapslist), output = fimpactsmap)
    elif len(fimpactsmapslist) == 1:
        fimpactsmap = fimpactsmapslist[0]
    else:
        grass.message('Impacts map missing')
        return
    #Make the landtenure map for this year
    creating = grass.run_command('r.in.xyz', quiet = "True", input = tenuretemp.name, output = landtenurename, x = '1', y = '2', z = '3', type = 'DCELL')
    tenuretemp.close()
    #---------------Do woodgathering and grazing routine
    gimpactsmapslist = []
    wimpactsmapslist = []
    #randomly shuffle the masterlist of villages so the same one doesn't get to pick their farming land first every year
    random.shuffle(masterlist)
    for village in masterlist:
        villagepop = outputdict[village["houses"][0][1]]["villagepop"]
        grazevalname = prefix + "_V" + str(village["houses"][0][1])  + "_graze_land_value"
        gathervalname = prefix + "_V" + str(village["houses"][0][1])  + "_woodgathering_land_value"
        #this is just generating the right agval name so we can figure out the amount of wood gotten from clearing new farm plots
        agvalname = prefix + "_V" + str(village["houses"][0][1]) + "_ag_land_value"
        #get some stats on the current cost map
        costdict = {}
        costdict = grass.parse_command('r.univar', flags = 'g', map = village["costmap"])
        #Calculate the grazing land evaluation map for making decisions on. Note that grazing cannot take place on land that is being farmed, on land occupied by village buildings, or on land that it too far away. This logic is necessary b/c we are modeling an entire years' worth of decision in one single step. To compensate for this, we've randomize the order of the villages from year to year so that each village will have an equal chance to get the first pick in any given year.
        grass.mapcalc("${grazevalname}=if(${costmap} <= ${maxgrazecost} && isnull(${villageland}) && isnull(${fimpactsmap}), if(${costmap} > 0 && ${lcovval} > 0, 100 * ( (${gdistweight} * (1-(${costmap}/${maxcost})) ) + (${lcovweight} * (${lcovval}/39))/(${lcovweight} + ${gdistweight}) ), 0), null())", quiet = "True", maxgrazecost = maxgrazecost, grazevalname = grazevalname, lcovval = lcovval, gdistweight = gdistweight, lcovweight = lcovweight, maxcost = costdict['max'], costmap = village["costmap"], villageland = villageland, fimpactsmap = fimpactsmap)

        #Calculate the woodgathering land evaluation map for making decisions on. Note that grazing cannot take place on land that is being farmed, on land occupied by village buildings, on land that does not have at least a moderate density of shrubs on it (lcov value above 8), or on land that it too far away. We are assuming that the maximum time cost for woodgathering (the maximum one-way time distance that a woodgatherer will travel to gather wood) is the same as the maximum time cost for grazing, so we will use "maxgrazcost" as the upper limit to define the wood gathering catchment. Also note that we are NOT forbidding agents from woodgathering on land already chosen for woodgathering by another village or that is being grazed on this year. This allows for "tragedy of the commons" type behavior, which is appropriate for woodgathering and grazing where the land isn't fully "owned" by any particular village (as opposed to farming, where households at least have a tenure on particular plots). In our scenario, we assume that the housholds in a village will try not to "double gather" from a plot. That is, within each village, agents will not gather more wood from an individual plot than is specified by the "intensity" parameter, but they will not avoid a plot if it has also been chosen by another village. 
        grass.mapcalc("${gathervalname}=if((isnull(${villageland}) && isnull(${fimpactsmap}) && ${costmap} <= ${maxgrazecost} && ${lcov} >= 9), ( (2*${lcov}) + (100*${wooddistweight}*(1-(${costmap}/${maxcost}))) )/(1 + ${wooddistweight}), null())", quiet = "True", gathervalname = gathervalname, costmap = village["costmap"], maxcost = costdict['max'], maxgrazecost = maxgrazecost, wooddistweight = wooddistweight, villageland = villageland, fimpactsmap = fimpactsmap, lcov = lcov)
        #Grab the x, y, and value of all cells in the graze value and grazing returns maps for the village, and rank that list in order from least to most desireable
        grazeval1 = grass.read_command("r.stats", quiet = "True", flags = '1gn', input = grazevalname + ',' + grazereturnsname, fs = ',').splitlines()
        grazevalues = []
        for item in grazeval1:
            templist = []
            for thing in item.split(','):
                templist.append(float(thing))
            grazevalues.append(templist)
        #This has made a list of: [0] x, [1] y, [2] graze land value, [3] graze return value
        #Now sort the list in place:
        grazevalues.sort(key=itemgetter(2))
        #Grab the x, y, and value of all cells in the woodgathering value and biomass returns maps for the village, and rank that list in order from least to most desireable
        gatherval1 = grass.read_command("r.stats", quiet = "True", flags = '1gn', input = gathervalname + ',' + biomass, fs = ',').splitlines()
        gathervalues = []
        for item in gatherval1:
            templist = []
            for thing in item.split(','):
                templist.append(float(thing))
            gathervalues.append(templist)
        #This has made a list of: [0] x, [1] y, [2] woodgathering land value, [3] biomass return value
        #Now sort the list in place:
        gathervalues.sort(key=itemgetter(2))
        #randomly shuffle the list of households so the same one doesn't get to "go first" every year
        random.shuffle(village["houses"])
        ###################################
        #Create some lists and dictionaries. Some of these will be our loop timing and control criteria, and some are containters for output data. 1) figure out how many individual farmplots and grazeplots are wanted by all households in the village, 2) list of  how many farm and graze plots each house wants, and 3) add placemark entries into the output dictionary to eventually hold the data. 
        numgrazeplots = 0
        grazeplotslist = []
        gatherplotslist = []
        for house in village["houses"]:
            numgrazeplots = numgrazeplots + int(house[5])
            grazeplotslist.append(range(int(house[5])))
            #set up some blank lists linked to a key for each house in this village in the output dictionary that will hold the results of the farm and graze plot choice routine. 
            ##The dictionary is set up like this: {(village)1: {{(hh)1: {"wheatplots": [[x, y, agval, wheatreturns, barleyreturns], [...], ...]; "barleyplots": [[x, y, agval, wheatreturns, barleyreturns], [...], ...]; "grazeplots": [[x, y, grazval, grazereturns], [...], ...]; (hh)2: {"grazeplots": [[x, y, grazval, grazereturns], [...], ...]...}; "woodplots": [[x, y, woodamount], [...]]; "villagepop": 'some int #'}; (village)2: {(hh)1: {"grazeplots"...etc... }}} 
            ##Remember that each plot is itself a list of x, y, and values: [234555.5, 456677.3, 39.2, 345], so to get the x coordinate of the third-ranked farm plot for village 2, household 3,you use this key structure: outputdict[2][3]["farmplots"][2][0], and similarly, the y coordinate of that plot: outputdict[2][3]["farmplots"][2][1]
            outputdict[house[1]][house[0]]["grazeplots"] = []
        outputdict[village["houses"][0][1]]["woodplots"] = []
        #now, loop through the total number of needed grazing plots, popping out the x,y,value information and updateing lists for each household. There are controls that are set up so that each household gets the number it desired.
        for num in range(numgrazeplots):
            for house, grazeplots in zip(village["houses"], grazeplotslist):
                if len(grazeplots) == 0:
                    pass
                else:
                    #if we've run out of land then we break out of the loop and the households' needs will not be fulfilled.
                    if len(grazevalues) == 0:
                        break
                    else:
                        templist = []
                        grazeplots.remove(grazeplots[0])
                        outputdict[house[1]][house[0]]["grazeplots"].append(grazevalues.pop())

        #now we figure out how many cells that the village needs for woodgathering, and then pick the best of them. 
        #first, figure out how much wood was obtained when any new farm fields were cleared
        swiddenwoodmap = "tempry_swid_wood_" + prefix
        grass.mapcalc('${swiddenwoodmap}=if(isnull(${fimpactsmap}), null(), abs((0.1 - ${biomass}) / ${cellpersqm}) )', quiet = "True", swiddenwoodmap = swiddenwoodmap, fimpactsmap = fimpactsmap, biomass = biomass, cellpersqm = cellpersqm)
        swiddenwoodamount = grass.parse_command("r.sum", quiet = "True", rast = swiddenwoodmap)
        #If the user has selected the intensity to be 0, then we set the catchment to be 0, which means no wood gathering happens.
        t1 = int( ((villagepop * wooduse) - float(swiddenwoodamount['SUM']))/ (intensity / cellpersqm) )
        if intensity == 0.0 or t1 <= 0:
            numgathercells = 0
        else:
            numgathercells = t1
        for num in range(numgathercells):
            outputdict[village["houses"][0][1]]["woodplots"] .append(gathervalues.pop())
            #if we've run out of land then we break out of the loop and the villagers' needs will not be fulfilled. NOTE. Currently there are no consequences to agents for not making the woodgathering quota.
            if len(gathervalues) == 0:
                break
        #Make the grazing and woodgathering impacts maps
        gimpactsmapname = prefix + "_V" + str(village["houses"][0][1])  + "_grazing_impacts"
        wimpactsmapname = prefix + "_V" + str(village["houses"][0][1])  + "_woodgathering_impacts"
        gimpactsmapslist.append(gimpactsmapname)
        wimpactsmapslist.append(wimpactsmapname)
        #grazing map
        a = tempfile.NamedTemporaryFile()
        #b = file("V_%s_temp_vector.txt" % str(village["houses"][0][1]), 'w')
        for house in village["houses"]:
            for item in outputdict[house[1]][house[0]]["grazeplots"]:
                #amount that will be grazed away in any cell (in units of kg/sq m)
                impactsamount = float(item[3]) * cellpersqm
                a.write("%s|%s|%s\n" % (item[0], item[1], round(impactsamount, 5)))
                #b.write("%s|%s|%s\n" % (item[0], item[1], round(impactsamount, 5)))
            a.flush()
            #b.flush()
        creating = grass.run_command('r.in.xyz', quiet = "True", input = a.name, x  = '1', y = '2', z = '3', output = gimpactsmapname, type = 'DCELL')
        a.close()
        #b.close()
        grass.run_command('r.colors', quiet = "True", map = gimpactsmapname, color = 'bgyr')
        #woodgathering map
        if len(outputdict[village["houses"][0][1]]["woodplots"]) == 0:
            grass.mapcalc("${wimpactsmapname}=null()", quiet = "True", wimpactsmapname = wimpactsmapname)
        else:
            a = tempfile.NamedTemporaryFile()
            for item in outputdict[village["houses"][0][1]]["woodplots"]:
                a.write("%s|%s|%s|Woodgathering\n" % (item[0], item[1], intensity))
            a.flush()
            creating = grass.run_command('r.in.xyz', quiet = "True", input = a.name, output = wimpactsmapname, x = '1', y = '2', z = '3', type = 'DCELL')
            a.close()
            grass.run_command('r.colors', quiet = "True", map = wimpactsmapname, color = 'bgyr')
    #Patch all the villages' impacts maps together to make a single maps for all villages... (NOTE. we are using r.series here because grazing and woodgathering may occur simultaneously on the same cell, and woodgathering may be done on the same cell by different villages. Thus we need to ADD them together, not patch them, and r.series lets us do that without having to worry about nulls propigating as they do in mapcalc)
    grass.run_command('r.series', quiet = "True", input = ",".join(gimpactsmapslist) + "," + ",".join(wimpactsmapslist), output = gwimpactsmap_biomass, method = "sum") 

    #--------------------Do Landcover and Soil Fertility Updating Routine
##################################################
    # calculating rate of regrowth based on current soil fertility and depths. Recoding fertility (0 to 100) and depth (0 to >= 1) with a power regression curve from 0 to 1, then taking the mean of the two as the regrowth rate
    grass.mapcalc('${temp_rate}=if(${sdepth} <= 1.0, ( ( ( (-0.000118528 * (exp(${sfertil},2.0))) + (0.0215056 * ${sfertil}) + 0.0237987 ) + ( ( -0.000118528 * (exp((100*${sdepth}),2.0))) + (0.0215056 * (100*${sdepth})) + 0.0237987 ) ) / 2.0 ), ( ( ( (-0.000118528 * (exp(${sfertil},2.0))) + (0.0215056 * ${sfertil}) + 0.0237987 ) + 1.0) / 2.0 ) )', quiet = "True", temp_rate = temp_rate, sdepth = sdepth, sfertil = sfertil)
    #use our recode rules to convert the woodgathering/grazing impacts map created above from units of kg biomass / sq m to units of landcover value per cell
    grass.run_command('r.recode', quiet = "True", input = gwimpactsmap_biomass, output = gwimpactsmap_lcov, rules = recodefrom.name)
    #updating the landcover based on all impacts. Note that grazed and woodgathered patches will regrow by their calcualted rates EVERY year, regardless of whether or not they've been used, but farm patches only regrow if they were not used this year. All land is limited by the value of maxlcov for each cell in the input maxlcov map (or by a single maxlcov numerical value, if entered that way). The ONLY time this rule is broken is if the maxlcov a patch is less than farmval, but the patch has been farmed in that year. If so, lcov is set == farmval in that patch for this year. If not subsequently farmed in the next year, then lcov will go back to == maxlcov for that patch.
    grass.mapcalc('${out_lcov}=eval(x=if(isnull(${villageland}) && isnull(${fimpactsmap}) && isnull(${gwimpactsmap_lcov}), (${lcov} + ${temp_rate}), if(isnull(${villageland}) && isnull(${fimpactsmap}), (${lcov} - ${gwimpactsmap_lcov} + ${temp_rate}), if(isnull(${villageland}), ${farmval}, ${villageland}) ) ), if(x < 0, 0, if(x > ${maxlcov} && isnull(${fimpactsmap}), ${maxlcov}, x)) )', quiet = "True", out_lcov = out_lcov, villageland = villageland, fimpactsmap = fimpactsmap, gwimpactsmap_lcov = gwimpactsmap_lcov, lcov = lcov, maxlcov = maxlcov, farmval = farmval, temp_rate = temp_rate)
    #set colors
    try:
        grass.run_command('r.colors', quiet = "True", map = out_lcov, rules = lc_color)
    except:
        pass
    #updating fertility based on farming impacts
    grass.mapcalc('${out_fertil}=eval(x=if(isnull(${fimpactsmap}), ${sfertil} + ${recovery}, ${sfertil} - ${degrade_rate}), if(x < 0, 0, if(x > 100, 100, x)) )', quiet = "True", out_fertil = out_fertil, fimpactsmap = fimpactsmap, sfertil = sfertil, degrade_rate = degrade_rate, recovery = recovery)
    #set colors
    try:
        grass.run_command('r.colors', quiet = 'True', map = out_fertil, rules = sf_color)
    except:
        pass
    #if asked to, creat reclassed landcover labels map
    if bool(os.getenv('GIS_OPT_lc_rules')) is True:
        grass.run_command('r.reclass', quiet = "True", input = out_lcov, output = temp_reclass, rules = lc_rules)
        grass.mapcalc('${out}=${input}', quiet = "True", out = reclass_out, input = temp_reclass)
        #set colors
        try:
            grass.run_command('r.colors', quiet = "True", map = reclass_out, rules = lc_color)
        except:
            pass
        grass.run_command('g.remove', quiet = "True", rast = temp_reclass)
    else:
        pass
    #Create out_impacts map. This map is mainly for display purposes.
    impacts1 = "tempry_1_" + out_impacts
    impacts_reclass = "tempry_reclassed_" + out_impacts

    if len(gimpactsmapslist) > 1:
        grass.run_command('r.patch', quiet = "True", input =  ",".join(gimpactsmapslist), output = gimpactsmap)
        grass.run_command('r.patch', quiet = "True", input =  ",".join(wimpactsmapslist), output = wimpactsmap)
    elif len(gimpactsmapslist) == 1:
        gimpactsmap = gimpactsmapslist[0]
        wimpactsmap = wimpactsmapslist[0]
    else:
        grass.message('Grazing and/or woodgathering impacts map missing')
        return
    grass.mapcalc('${impacts1}=eval(x=if(isnull(${gimpactsmap}) && isnull(${wimpactsmap}), null(), if(isnull(${gimpactsmap}), 4, if(isnull(${wimpactsmap}), 3, 5))), if(isnull(${fimpactsmap}), x, ${fimpactsmap}) )', quiet = "True", impacts1 = impacts1, fimpactsmap = fimpactsmap, gimpactsmap = gimpactsmap, wimpactsmap = wimpactsmap)
    reclassrules = tempfile.NamedTemporaryFile()
    reclassrules.write('1 = 1 Wheat Farming\n2 = 2 Barley Farming\n3 = 3 Grazing\n4 = 4 Woodgathering\n5 = 5 Grazing AND Woodgathering')
    reclassrules.flush()
    grass.run_command('r.reclass', quiet = "True", input = impacts1, output = impacts_reclass, rules = reclassrules.name)
    grass.mapcalc('${out_impacts}=${impacts_reclass}', quiet = "True", out_impacts = out_impacts, impacts_reclass = impacts_reclass)
    reclassrules.close()
    grass.run_command('g.remove', quiet = "True", rast = impacts_reclass)


    #--------------------Do Landcover and Soil Fertilty Statistics Gathering Routine
    #First landcover
    #check if maxlcov is a map or a number
    try: 
        maxval = int(float(maxlcov))
    except:
        maxlcovdict = grass.parse_command('r.univar', flags = 'ge', map = maxlcov)
        maxval = int(float(maxlcovdict['max']))
    if bool(statsfile) is True:
        f = open(statsfile, 'a')
        if os.path.getsize(statsfile) == 0:
            f.write("Landcover Stats\n\nYear," + ",".join(str(i) for i in range(maxval + 1)) + "\n")
        statdict = grass.parse_command('r.stats', quiet = "True", flags = 'ani', input = out_lcov, fs = '=', nv ='*')
        f.write(prefix + ",")
        for key in range(maxval + 1):
            try:
                f.write(statdict[str(key)] + "," )
            except:
                f.write("0,")
        f.write("\n")
        f.close()
    else:
        pass
    #Now soil fertility
    if bool(fertilstats) is True:
        f = open(fertilstats, 'a')
        if os.path.getsize(fertilstats) == 0:
            f.write("Soil Fertility Stats\n\nYear,Mean,Median,Standard Deviation,Variance\n")
        fertildict = grass.parse_command('r.univar', flags = 'ge', map = out_fertil)
        f.write(prefix + "," + fertildict["mean"] + "," + fertildict["median"] + "," +  fertildict["stddev"] + "," + fertildict["variance"] +'\n')
        f.close()
    else:
        pass

    #------------------Clean up
    recodeto.close()
    recodefrom.close()
    grass.run_command('g.mremove', quiet = "True", flags = 'f', rast = "tempry*")
    if os.getenv('GIS_FLAG_b') == '1':
        pass
    else:
        grass.run_command('g.remove', quiet = "True", rast = biomass)

    #------------------Send output string of info to standard out
    #first, get the output dict sorted back in numerical order of village numbers
    #outputdict.sort(key=itemgetter(2))
    outputstring = ";"
    for village in sorted(outputdict.iterkeys()):
        for house in sorted(outputdict[village].iterkeys()):
            status = "True"
            try:
                int(house)
            except:
                status = "False"
            if status is "True":
                #first load the return values for all cells used by a house into a list (and make sure the values are floats)
                wheatlist = []
                for item in outputdict[village][house]["wheatplots"]:
                    wheatlist.append(float(item[3]))
                barleylist = []
                for item in outputdict[village][house]["barleyplots"]:
                    barleylist.append(float(item[4]))
                grazlist = []
                for item in outputdict[village][house]["grazeplots"]:
                    grazlist.append(float(item[3]))
                # Now, caclulate the sum of each list and save to a variable to write to the output string
                wheatsum = math.fsum(wheatlist)
                barleysum = math.fsum(barleylist)
                grazesum = math.fsum(grazlist)
                # Now, use the custom function to figure out the median return value from each list, and pad it to a randomly generated percentage that is drawn from a gaussian probability distribution with mu of the Median value and sigma of 0.0333. This means that the absolute max/min pad can only be up to +- %10 of the median value (eg. at the 3-sigma level of a gaussian distribution with sigma of 0.0333), and that pad values closer to 0% will be more likely than pad values close to +- 10%
                MedWheat = getMedian(wheatlist)
                outwheat = random.gauss(MedWheat, (MedWheat * 0.0333))
                MedBarley = getMedian(barleylist)
                outbarley = random.gauss(MedBarley, (MedBarley * 0.0333))
                MedGraze = getMedian(grazlist) 
                outgraze = random.gauss(MedGraze, (MedGraze * 0.0333))                
                #Configure the output string to village[house] back to AP-Sim. It must be configured properly so that AP-Sim can parse it correctly.
                ##outputstring format = ";HH#:avg_wheat_return,avg_barley_return,avgoc_return,wheat_yield,barley_yield,oc_yield;"
                outputstring = outputstring + house + ':' + str(outwheat) + ',' + str(outbarley) + ',' + str(outgraze) + ',' + str(wheatsum) + ',' + str(barleysum) + ',' + str(grazesum) + ';'
            else:
                pass
    return(outputstring)

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        txtout = main()
        print txtout
