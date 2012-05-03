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
#% description: input landcover map (values aligned with reclass rules)
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
#% answer:
#% required : yes
#%END

#%option
#% key: cfact_color
#% type: string
#% gisprompt: string
#% description: path to color rules file for c-factor map
#% answer: 
#% required : yes
#%END

import sys
import os
import subprocess
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass

#main block of code starts here
def main():
    #setting up variables for use later on
    inmap = os.getenv("GIS_OPT_inmap")
    outcfact = os.getenv("GIS_OPT_outcfact")
    cfact_rules = os.getenv("GIS_OPT_cfact_rules")
    cfact_color = os.getenv("GIS_OPT_cfact_color")
    #creating c-factor map and setting colors
    grass.run_command('r.recode', quiet = True, input = inmap, output = outcfact, rules = cfact_rules)
    grass.run_command('r.colors',  quiet = True, map = outcfact, rules = cfact_color)
    return

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()
