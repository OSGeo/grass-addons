#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.soil.fertility
# AUTHOR(S):		Isaac Ullah, Michael Barton, Arizona State University
# PURPOSE:		Updates soil fertility thru time based on an impacts
#               	map created by an agent base model.
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
# COPYRIGHT:		(C) 2007 by Isaac Ullah, Michael Barton, Arizona State University
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: Updates soil fertility thru time based on an impact map created by an agent base model.
#%END

#%option
#% key: inmap
#% type: string
#% gisprompt: old,cell,raster
#% description: input soil fertility map (values coded 0-max)
#% required : yes
#%END

#%option
#% key: impacts
#% type: string
#% gisprompt: old,cell,raster
#% description: map of impacts on soil fertility values
#% required : yes
#%END

#%option
#% key: recovery
#% type: string
#% gisprompt: string
#% description: The rate at which soil recovers it's fertility per cycle (max fertility is 100)
#% answer: 1
#% required : yes
#%END

#%option
#% key: outmap
#% type: string
#% gisprompt: string
#% description: New soil fertility output map name (no prefix)
#% answer: s_fertility
#% required : yes
#%END

#%option
#% key: sf_color
#% type: string
#% gisprompt: string
#% description: path to color rules file for landcover map
#% answer: /usr/local/grass-6.5.svn/scripts/rules/sfertil_colors.txt
#% required : yes
#%END

#%flag
#% key: s
#% description: -s Output text file of soil fertility stats from the simulation (will be named "prefix"_sfertil_stats.txt, and will be overwritten if you run the simulation again with the same prefix)
#%END

import sys
import os
import subprocess
import tempfile
import  random
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass

#main block of code starts here
def main():
    #setting up variables for use later on
    inmap = os.getenv('GIS_OPT_inmap')
    impacts = os.getenv('GIS_OPT_impacts')
    outmap = os.getenv('GIS_OPT_outmap')
    recovery = os.getenv('GIS_OPT_recovery')
    sf_color = os.getenv('GIS_OPT_sf_color')
    txtout = outmap + '_sfertil_stats.txt'
    #Check to see if there is a MASK already, and if so, temporarily rename it
    if "MASK" in grass.list_grouped('rast')[grass.gisenv()['MAPSET']]:
        ismask = 1
        tempmask = 'mask_%i' % random.randint(0,100)
        grass.run_command('g.rename', quiet = "True", rast = 'MASK,' + tempmask)
    else:
        ismask = 0
    #Set MASK to input DEM
    grass.run_command('r.mask', input = inmap)
    #updating raw soil fertility category numbers
    grass.mapcalc('${outmap}=if(isnull(${impacts}) && ${inmap} >= 100 - ${recovery}, 100, if(isnull(${impacts}), (${inmap} + ${recovery}), if(${inmap} >= ${impacts}, (${inmap} - ${impacts}), 0 )))', outmap =  outmap, inmap = inmap, recovery = recovery, impacts =impacts )
    grass.run_command('r.colors', quiet = 'True', map = outmap, rules = sf_color)
    #checking total area of updated cells
    totarea = grass.read_command('r.stats',  flags = 'an', input = impacts, fs = ',', nsteps = '1').split(',')
    
    grass.message('\n\nTotal area of impacted zones = %s square meters\n\n' % totarea[1])
    #creating optional output text file of stats
    if os.getenv('GIS_FLAG_s') == '1':
        f = file(txtout, 'wt')
        f.write('Stats for ' + outmap+ '\n\nTotal area of impacted zones = ' + totarea[1] + ' square meters\n\nSoil Fertility Value,Area (sq. m)\n')
        areadict = grass.parse_command('r.stats',  flags = 'an', input = impacts)
        for key in areadict:
            f.write(key + '\n')
        f.close()
    grass.message('\nCleaning up...\n\n')
    grass.run_command('r.mask', flags = 'r')
    if ismask == 1:
        grass.run_command('g.rename', quiet = "True", rast = tempmask +',MASK')
    grass.message('DONE!\n\n')

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()
