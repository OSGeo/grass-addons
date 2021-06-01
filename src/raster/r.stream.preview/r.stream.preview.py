#!/usr/bin/env python

############################################################################
#
# MODULE:      r.stream.preview.py
# AUTHOR(S):   Margherita Di Leo
# PURPOSE:     Create a preview for threshold value given the flow accumulation map
# COPYRIGHT:   (C) 2012 by Margherita Di Leo 
#              dileomargherita@gmail.com
#
#              This program is free software under the GNU General Public
#              License (>=v3.0) and comes with ABSOLUTELY NO WARRANTY.
#              See the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%module
#% description: Create a preview for a threshold value given the flow accumulation map
#% keywords: raster
#%end
#%option
#% key: acc
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: flow accumulation
#% description: Name of flow accumulation raster map 
#% required: yes
#%end
#%option
#% key: th
#% type: double
#% key_desc: threshold
#% description: threshold (integer)
#% required: yes
#%end

import sys
import os
import grass.script as grass

if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

def main():    
    r_acc = options['acc']
    th = options['th']

    # Creates temp rules file
    tmp = open('rules', 'w')
    tmp.write('*:' + th + ':0' + '\n')
    tmp.write(th + ':*:1')
    tmp.close()

    # recode
    grass.run_command('r.recode', input = r_acc,
                                  output = 'r_preview',
                                  rules = 'rules',
                                  overwrite = 'True')

    # Delete temp rules file 
    os.remove('rules')

    # display
    grass.run_command( 'd.mon', stop = 'x1' )
    grass.run_command( 'd.mon', start = 'x1' )
    grass.run_command( 'd.rast', map = 'r_preview' )


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
