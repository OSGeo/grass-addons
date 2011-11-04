#!/usr/bin/python

############################################################################
#
# MODULE:       r.pngmap
# AUTHOR(S):    iullah
# COPYRIGHT:    (C) 2007 GRASS Development Team/iullah
#
#  description: quickly outout a png of any map to a specified location and filename

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#############################################################################/

#%Module
#% description: quickly outout a png of any map to a specified location and filename
#%End
#%option
#% key: inmap
#% type: string
#% gisprompt: old,cell,raster
#% description: map write to png
#% required : yes
#%END
#%option
#% key: outpath
#% type: string
#% gisprompt: old,cell,raster
#% description: output path and file name
#% answer: ~/output.png
#% required : yes
#%END

import sys
import os
import subprocess

# m is a message (as a string) one wishes to have printed in the output window
def grass_print(m):
	subprocess.Popen('g.message message="%s"' % m, shell='bash').wait()
	return

def main():
    os.environ['GRASS_PNGFILE'] =  os.getenv("GIS_OPT_outpath")
    os.environ['GRASS_TRANSPARENT'] =  'TRUE'
    os.environ['GRASS_RENDER_IMMEDIATE'] =  'TRUE'
    os.environ['GRASS_TRUECOLOR'] =  'TRUE'
    subprocess.Popen('d.rast -o %s' % os.getenv("GIS_OPT_inmap"), shell='bash').wait()

if __name__ == "__main__":
    if ( len(sys.argv) <= 1 or sys.argv[1] != "@ARGS_PARSED@" ):
        os.execvp("g.parser", [sys.argv[0]] + sys.argv)
    else:
        main()


