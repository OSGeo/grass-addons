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
#% key: max
#% type: string
#% gisprompt: string
#% description: maximum value for soil fertility maps (number for highest fertility)
#% answer: 100
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
# m is a grass/bash command that will generate some info to stdout. You must invoke this command in the form of "variable to be made" = out2var('command')
def out2var(m):
        pn = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
        return pn.stdout.read()
# m is a grass/bash command that will generate some list of info to stdout, n is the character that seperates individual pieces of information, and  o is a defined blank list to write results to
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
    outmap = os.getenv('GIS_OPT_outmap')
    max = os.getenv('GIS_OPT_max')
    sf_color = os.getenv('GIS_OPT_sf_color')
    txtout = outmap + '_sfertil_stats.txt'
    #setting initial conditions of map area
    grass_com('g.region rast=' + inmap)
    grass_com('r.mask --quiet -o input=' + inmap + ' maskcats=*')
    #updating raw soil fertility category numbers
    grass_com('r.mapcalc "' + outmap + '=if(' + inmap + ' == ' + max + ' && isnull(' + impacts + '), ' + max + ', (if (' + inmap + ' < ' + max + ' && isnull(' + impacts + '), (' + inmap + ' + 1), if (' + inmap + ' > ' + max + ', (' + max + ' - ' + impacts + '), if (' + inmap + ' < 0, 0, (' + inmap + ' - ' + impacts + '))))))"')
    grass_com('r.colors --quiet map=' + outmap + ' rules=' + sf_color)
    #checking total area of updated cells
    temparea = []
    out2list2('r.stats -a -n input=' + impacts + ' fs=, nv=* nsteps=1',  ',',  temparea)
    grass_print('\n\nTotal area of impacted zones = %s square meters\n\n' % temparea[1])
    #creating optional output text file of stats
    if os.getenv('GIS_FLAG_s') == '1':
        f = file(txtout, 'wt')
        f.write('Stats for ' + outmap+ '\n\nTotal area of impacted zones = ' + temparea[1] + ' square meters\n\nSoil Fertility Value,Area (sq. m)\n\n')
        p1 = subprocess.Popen('r.stats -A -a -n input=' + outmap + ' fs=, nv=* nsteps=' + max, stdout=subprocess.PIPE, shell='bash')
        p2 = p1.stdout.readlines()
        for y in p2:
            f.write(y)
        f.close()
    grass_print('\nCleaning up...\n\n')
    grass_com('g.remove --quiet rast=MASK')
    grass_print('DONE!\n\n')

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()
