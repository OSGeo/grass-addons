#!/usr/bin/python
#
############################################################################
#
# MODULE:       	r.cfactor
# AUTHOR(S):		Isaac Ullah, Michael Barton, Arizona State University
# PURPOSE:		Converts a map of landcover values to a c-factor map based 
#               	on a set of reclass rules
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
# COPYRIGHT:		(C) 2009 by Isaac Ullah, Michael Barton, Arizona State University
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: Converts a map of landcover values to a c-factor map based on a set of reclass rules
#%END

#%option
#% key: inmap
#% type: string
#% gisprompt: old,cell,raster
#% description: input landcover map (integer values aligned with reclass rules)
#% required : yes
#%END

#%option
#% key: outcfact
#% type: string
#% gisprompt: string
#% description: c_factor output map name
#% answer: year1_cfactor
#% required : yes
#%END

#%option
#% key: cfact_rules
#% type: string
#% gisprompt: string
#% description: path to recode rules file for c-factor map
#% answer: /usr/local/grass-6.5.svn/scripts/rules/cfactor_recode_rules.txt
#% required : yes
#%END

#%option
#% key: cfact_color
#% type: string
#% gisprompt: string
#% description: path to color rules file for c-factor map
#% answer: /usr/local/grass-6.5.svn/scripts/rules/cfactor_colors.txt
#% required : yes
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
#main block of code starts here
def main():
    #setting up variables for use later on
    inmap = os.getenv("GIS_OPT_inmap")
    outcfact = os.getenv("GIS_OPT_outcfact")
    cfact_rules = os.getenv("GIS_OPT_cfact_rules")
    cfact_color = os.getenv("GIS_OPT_cfact_color")
    #setting initial conditions of map area
    grass_com('g.region rast=' + inmap)
    grass_com('r.mask --quiet input=' + inmap + ' maskcats=*') 
    #creating c-factor map and setting colors
    grass_com('r.recode --quiet input=' + inmap + ' output=' + outcfact + ' rules=' + cfact_rules)
    grass_com('r.colors map=' + outcfact + ' rules=' + cfact_color)
    grass_print('\nCleaning up\n')
    grass_com('g.remove --quiet rast=MASK')
    grass_print('\nDONE\n')
    return

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()
