#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.landcover.update
# AUTHOR(S):		Isaac Ullah, Michael Barton, Arizona State University
# PURPOSE:		Updates a map of landcover by the amounts specified in an impacts
#               	map
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
# COPYRIGHT:		(C) 2009 by Isaac Ullah, Michael Barton, Arizona State University
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: Updates a map of landcover by the amounts specified in an impacts map
#%END

#%option
#% key: inmap
#% type: string
#% gisprompt: old,cell,raster
#% description: input landcover map (values coded 0-max)
#% required : yes
#%END

#%option
#% key: impacts
#% type: string
#% gisprompt: old,cell,raster
#% description: map of impacts on landcover values
#% required : yes
#%END

#%option
#% key: villages
#% type: string
#% gisprompt: old,cell,raster
#% description: input map of village locations (coded as the landcover value for village surfaces)
#% required : yes
#%END

#%option
#% key: sfertil
#% type: string
#% gisprompt: old,cell,raster
#% description: map of current soil fertility
#% required : yes
#%END

#%option
#% key: sdepth
#% type: string
#% gisprompt: old,cell,raster
#% description: map of current soil depths
#% required : yes
#%END

#%option
#% key: max
#% type: string
#% gisprompt: string
#% description: maximum value for landcover maps (number for climax veg)
#% answer: 50.0
#% required : yes
#%END

#%option
#% key: outmap
#% type: string
#% gisprompt: string
#% description: land cover output map name (no prefix)
#% answer: landcover
#% required : yes
#%END

#%option
#% key: lc_rules
#% type: string
#% gisprompt: string
#% description: Path to reclass rules file for making a "labels" map. If no rules specified, no labels map will be made.
#% answer:
#% required : no
#%END

#%option
#% key: lc_color
#% type: string
#% gisprompt: string
#% description: Path to color rules file for landcover map
#% answer:
#% required : no
#%END

#%flag
#% key: s
#% description: -s Output text file of land-use stats from the simulation (will be named "prefix"_luse_stats.txt, and will be overwritten if you run the simulation again with the same prefix)
#%END

#%flag
#% key: r
#% description: -r Save the map of vegetation regrowth rates.
#%END

import sys
import os
import subprocess
import tempfile
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass

#main block of code starts here
def main():
    #setting up variables for use later on
    inmap = os.getenv('GIS_OPT_inmap') 
    impacts = os.getenv('GIS_OPT_impacts') 
    villages = os.getenv('GIS_OPT_villages')
    sfertil = os.getenv('GIS_OPT_sfertil') 
    sdepth = os.getenv('GIS_OPT_sdepth') 
    outmap = os.getenv('GIS_OPT_outmap') 
    max = os.getenv('GIS_OPT_max') 
    lc_rules = os.getenv('GIS_OPT_lc_rules') 
    lc_color = os.getenv('GIS_OPT_lc_color') 
    txtout = outmap + '_landcover_stats.txt'
    temp_rate = 'temp_rate'
    temp_lcov = 'temp_lcov'
    temp_reclass = 'temp_reclass'
    reclass_out = outmap + '_labels'
    #setting initial conditions of map area
    grass.run_command('r.mask', quiet = True, input = inmap, maskcats = '*')
    # calculating rate of regrowth based on current soil fertility and depths. Recoding fertility (0 to 100) and depth (0 to >= 1) with a power regression curve from 0 to 1, then taking the mean of the two as the regrowth rate
    grass.mapcalc('${out}=if(${map1} <= 1.0, ( ( ( (-0.000118528 * (exp(${map2},2.0))) + (0.0215056 * ${map2}) + 0.0237987 ) + ( ( -0.000118528 * (exp((100*${map1}),2.0))) + (0.0215056 * (100*${map1})) + 0.0237987 ) ) / 2.0 ), ( ( ( (-0.000118528 * (exp(${map2},2.0))) + (0.0215056 * ${map2}) + 0.0237987 ) + 1.0) / 2.0 ) )', out = temp_rate, map1 = sdepth, map2 = sfertil)
    #updating raw landscape category numbers based on agent impacts and newly calculated regrowth rate
    grass.mapcalc('${out}=if(${inm} == ${m} && isnull(${imp}), double(${m}), if(${inm} < ${m} && isnull(${imp}), (double(${inm}) + double(${tr})), if(${inm} > ${m}, (double(${m}) - double(${imp})), if(${inm} <= 0.0, 0.0, (double(${inm}) - double(${imp})) ) ) ) )', out = temp_lcov, m = max, inm = inmap, imp = impacts, tr = temp_rate)
    try:
        lc_rules
    except NameError:
        lc_rules = None
    if lc_rules is None:
        grass.message( "No Labels reclass rules specified, so no Labels map will be made")
    else:
        grass.message( 'Creating reclassed Lables map (' + reclass_out +') of text descriptions to raw landscape categories')
        grass.run_command('r.reclass', quiet = True, input = temp_lcov, output = temp_reclass, rules = lc_rules)
        grass.mapcalc('${out}=${input}', out = reclass_out, input = temp_reclass)
        grass.run_command('r.colors', quiet = True, map = reclass_out, rules = lc_color)
    #checking total area of updated cells
    statdict = grass.parse_command('r.stats', quiet = True, flags = 'Aan', input = impacts, fs = ':', nv ='*', parse = (grass.parse_key_val, { 'sep' : ':' }))
    sumofimpacts = 0.0
    for key in statdict:
        sumofimpacts = sumofimpacts + float(statdict[key])
    grass.message('Total area of impacted zones = %s square meters\n' % sumofimpacts)
    #creating optional output text file of stats
    if os.getenv('GIS_FLAG_s') == '1':
        f = file(txtout, 'wt')
        f.write('Stats for ' + prfx + '_landcover\n\nTotal area of impacted zones = %s square meters\n\n\nLandcover class #, Landcover description, Area (sq. m)\n' % sumofimpacts)
        p1 = grass.parse_command('r.stats', quiet = True, flags = 'aln', input = prfx + '_landuse1', fs = ':', nv ='*', nsteps = max, parse = (grass.parse_key_val, { 'sep' : ':' }))
        for key in p1:
            f.write(str(key) + ',' + str(p1[key]))
        f.close()
    grass.run_command('r.patch', quiet = True, input = villages + ',' + temp_lcov, output= outmap)
    grass.run_command('r.colors', quiet = True, map = outmap, rules = lc_color)
    grass.message('\nCleaning up\n')
    if os.getenv('GIS_FLAG_r') == '1':
        grass.run_command('g.remove', quiet =True, rast = 'MASK,temp_reclass,temp_lcov')
        grass.run_command('g.rename', quiet = True, rast='temp_rate,' + outmap +'_rate')
    else:
        grass.run_command('g.remove', quiet =True, rast = 'MASK,temp_rate,temp_reclass,temp_lcov')
    grass.message("\nDONE!\n")
    return

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()
