#!/usr/bin/python
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
#% description: input landcover map (integer values aligned with reclass rules)
#% required : yes
#%END

#%option
#% key: villages
#% type: string
#% gisprompt: old,cell,raster
#% description: input map of village locations (coded as all one integer value)
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
# first define some useful custom methods

# m is a message (as a string) one wishes to have printed in the output window
def grass_print(m):
	subprocess.Popen('g.message message="%s"' % m, shell='bash').wait()
	return
# m is grass (or bash) command to execute (written as a string). script will wait for grass command to finish
def grass_com(m):
	subprocess.Popen('%s' % m, shell='bash').wait()
	return
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
    grass_com('g.region --quiet rast=' + inmap)
    grass_com('r.mask --quiet -o input=' + inmap +' maskcats=*')
    #discovering the value of the input villages map
    inval = out2var('r.stats -n input=%s fs=space nv=* nsteps=1' % villages)
    #setting up color and reclass rules
    colors = tempfile.NamedTemporaryFile()
    colors.write('%s red' % val)
    colors.flush()
    reclass =  tempfile.NamedTemporaryFile()
    reclass.write('%s = %s Village\n' % (inval.strip('\n'),  val))
    reclass.flush()
    #doing reclass and recolor
    grass_print('%s = %s Village\n' % (inval.strip('\n'),  val))
    grass_print('r.reclass --quiet input=' + villages + ' output=' + temp_villages + ' rules=%s' % reclass.name)
    grass_com('r.reclass --quiet input=' + villages + ' output=' + temp_villages + ' rules="%s"' % reclass.name)
    grass_com('r.colors --quiet map=' + temp_villages + ' rules="%s"' % colors.name)
    #patching maps together
    grass_com('r.patch --quiet input=' + temp_villages + ',' + inmap + ' output=' + outmap)
    grass_print('\nCleaning up...\n')
    grass_com('g.remove --quiet rast=MASK,' + temp_villages)
    colors.close()
    reclass.close()
    grass_print('\n\nDONE!\n')
    
# here is where the code in "main" actually gets executed. This way of programming is neccessary for the way g.parser needs to run.
if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()

