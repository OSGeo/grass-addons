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
#% answer: 50
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
#% answer: /usr/local/grass-6.5.svn/scripts/rules/luse_reclass_rules.txt
#% required : no
#%END

#%option
#% key: lc_color
#% type: string
#% gisprompt: string
#% description: Path to color rules file for landcover map
#% answer: /usr/local/grass-6.5.svn/scripts/rules/luse_colors.txt
#% required : no
#%END

#%flag
#% key: s
#% description: -s Output text file of land-use stats from the simulation (will be named "prefix"_luse_stats.txt, and will be overwritten if you run the simulation again with the same prefix)
#%END

import sys
import os
import subprocess
import tempfile
# first define some useful custom methods

# m is a message (as a string) one wishes to have printed in the output window
def grass_print(m):
	subprocess.Popen('g.message message="%s"' % m, shell='bash').wait()
	return
# m is grass (or bash) command to execute (written as a string). script will wait for grass command to finish
def grass_com(m):
	subprocess.Popen('%s' % m, shell='bash').wait()
	return
# m is grass (or bash) command to execute (written as a string). script will not wait for grass command to finish
def grass_com_nw(m):
	subprocess.Popen('%s' % m, shell='bash')
	return
# m is a grass/bash command that will generate some list of keyed info to stdout, n is the character that seperates the key from the data, o is a defined blank dictionary to write results to
def out2dict(m, n, o):
    p1 = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
    p2 = p1.stdout.readlines()
    for y in p2:
        y0,y1 = y.split('%s' % n)
        o[y0] = y1.strip('\n')

# m is a grass/bash command that will generate some charcater seperated list of info to stdout, n is the character that seperates individual pieces of information, and  o is a defined blank list to write results to
def out2list2(m, n, o):
        p1 = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
        p2 = p1.stdout.readlines()
        for y in p2:
            y0,y1 = y.split('%s' % n)
            o.append(y0)
            o.append(y1.strip('\n'))

#main block of code starts here
def main():
    #setting up variables for use later on
    inmap = os.getenv('GIS_OPT_inmap') 
    impacts = os.getenv('GIS_OPT_impacts') 
    sfertil = os.getenv('GIS_OPT_sfertil') 
    sdepth = os.getenv('GIS_OPT_sdepth') 
    outmap = os.getenv('GIS_OPT_outmap') 
    max = os.getenv('GIS_OPT_max') 
    lc_rules = os.getenv('GIS_OPT_lc_rules') 
    lc_color = os.getenv('GIS_OPT_lc_color') 
    txtout = outmap + '_landcover_stats.txt'
    temp_rate = 'temp_rate'
    reclass_out = outmap + '_labels'
    #setting initial conditions of map area
    grass_com('g.region --quiet rast=' + inmap)
    grass_com('r.mask --quiet input=' + inmap + ' maskcats=*')
    # calculating rate of regrowth based on current soil fertility and depths. Recoding fertility (0 to 100) and depth (0 to >= 1) with a power regression curve from 0 to 1, then taking the mean of the two as the regrowth rate
    grass_com('r.mapcalc "' + temp_rate + '=if(' + sdepth + ' <= 1, ( ( ( (-0.000118528 * (exp(' + sfertil + ',2))) + (0.0215056 * ' + sfertil + ') + 0.0237987 ) + ( ( -0.000118528 * (exp((100*' + sdepth + '),2))) + (0.0215056 * (100*' + sdepth + ')) + 0.0237987 ) ) / 2 ), ( ( ( (-0.000118528 * (exp(' + sfertil + ',2))) + (0.0215056 * ' + sfertil + ') + 0.0237987 ) + 1) / 2 ) )"')
    #updating raw landscape category numbers based on agent impacts and newly calculated regrowth rate
    grass_com('r.mapcalc "' + outmap + '=if(' + inmap  + '== ' + max + ' && isnull(' + impacts + '), ' + max + ', if(' + inmap  + '< ' + max + ' && isnull(' + impacts + '), (' + inmap + ' + ' + temp_rate + '), if(' + inmap + ' > ' + max + ', (' + max + ' - ' + impacts + '), if(' + inmap + ' <= 0, 0, (' + inmap + ' - ' + impacts + ') )  )   )    )"')
    grass_com('r.colors --quiet map=' + outmap + ' rules=' + lc_color)
    try:
        lc_rules
    except NameError:
        lc_rules = None
    if lc_rules is None:
        grass_print( "No Labels reclass rules specified, so no Labels map will be made")
    else:
        grass_print( 'Creating reclassed Lables map (' + reclass_out +') of text descriptions to raw landscape categories')
        grass_com('r.reclass --quiet input=' + outmap + ' output=' + reclass_out + ' rules=' + lc_rules)
        grass_com('r.colors --quiet map=' + reclass_out + ' rules=' + lc_color)
    #checking total area of updated cells
    statlist = []
    out2list2('r.stats -a -n input=' + impacts + ' fs=, nv=* nsteps=1', ',', statlist)
    grass_print('Total area of impacted zones = ' + statlist[1] + ' square meters\n')
    #creating optional output text file of stats
    if os.getenv('GIS_FLAG_s') == '1':
        f = file(txtout,  'wt')
        f.write('Stats for ' + prfx + '_landcover\n\nTotal area of impacted zones = ' + statlist[1] + ' square meters\n\n\nLandcover class #, Landcover description, Area (sq. m)\n')
        p1 = grass_com_nw('r.stats --quiet -a -l -n input=' + prfx +'_landuse1 fs=, nv=* nsteps=' + max )
        p2 = p1.stdout.readlines()
        for y in p2:
            f.write(y)
        f.close()

    grass_print('\nCleaning up\n')
    grass_com('g.remove --quiet rast=MASK,' + temp_rate)
    grass_print("\nDONE!\n")
    return

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()
