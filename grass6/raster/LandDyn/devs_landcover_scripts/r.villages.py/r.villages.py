#!/usr/bin/pythonr.villages.py
#
############################################################################
#
# MODULE:       	r.villages
# AUTHOR(S):		Isaac Ullah, Michael Barton, Arizona State University
# PURPOSE:		patches a map of village locations on a landcover landcover map 
# ACKNOWLEDGEMENTS:	National Science Foundation Grant #BCS0410269 
# COPYRIGHT:		(C) 2009 by Isaac Ullah, Michael Barton, Arizona State University
#			This program is free software under the GNU General Public
#			License (>=v2). Read the file COPYING that comes with GRASS
#			for details.
#
#############################################################################


#%Module
#%  description: patches a map of village locations on a landcover landcover map
#%END

#%option
#% key: inmap
#% type: string
#% gisprompt: old,cell,raster
#% description: input landcover map
#% required : yes
#%END

#%option
#% key: villages
#% type: string
#% gisprompt: old,cell,raster
#% description: input map of village locations (coded as all one value)
#% required : yes
#%END

#%option
#% key: val
#% type: integer
#% answer: 40
#% description: value for villages to be coded onto output map
#% required : yes
#%END

#%option
#% key: output
#% type: string
#% gisprompt: string
#% description: name for output map
#% answer: year1
#% required : yes
#%END

import sys
import os
import subprocess
import tempfile
grass_install_tree = os.getenv('GISBASE')
sys.path.append(grass_install_tree + os.sep + 'etc' + os.sep + 'python')
import grass.script as grass

# m is a grass/bash command that will generate some info to stdout. You must invoke this command in the form of "variable to be made" = out2var('command')
def out2var(m):
    pn = subprocess.Popen('%s' % m, stdout=subprocess.PIPE, shell='bash')
    return pn.stdout.read()

#main block of code starts here
def main():
    #setting up variables for use later on
    inmap = os.getenv('GIS_OPT_inmap')
    villages = os.getenv('GIS_OPT_villages')
    val = os.getenv('GIS_OPT_val')
    outmap = os.getenv('GIS_OPT_output')
    temp_villages = outmap + '_temporary_village_reclass'
    #setting initial conditions of map area
    grass.run_command('r.mask', quiet = True, input = inmap, maskcats = '*')
    #discovering the value of the input villages map
    inval = grass.read_command('r.stats',  flags = 'n',  input = villages, fs = 'space', nv = '*', nsteps = '1')
    #setting up color and reclass rules
    colors = tempfile.NamedTemporaryFile()
    colors.write('%s red' % val)
    colors.flush()
    reclass =  tempfile.NamedTemporaryFile()
    reclass.write('%s = %s Village\n' % (inval.strip('\n'),  val))
    reclass.flush()
    #doing reclass and recolor
    grass.run_command('r.reclass', quiet = True, input = villages, output = temp_villages, rules = reclass.name)
    grass.run_command('r.colors', quiet = True,  map = temp_villages, rules = colors.name)
    #patching maps together
    grass.run_command('r.patch', quiet = True,  input = temp_villages + ',' + inmap, output= outmap)
    grass.message('\nCleaning up...\n')
    grass.run_command('g.remove', quiet = True, rast ='MASK,' + temp_villages)
    colors.close()
    reclass.close()
    grass.message('\n\nDONE!\n')

# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()

