#!/usr/bin/env python
############################################################################
#
# MODULE:       d.mon(.py)
# AUTHOR:       M. Hamish Bowman, Dunedin, New Zealand
# PURPOSE:      Front end wrapper to emulate d.mon from earlier GRASSes
# COPYRIGHT:    (c) 2011 Hamish Bowman, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Starts a graphics display monitor which can be controlled from the command line.
#% keywords: display
#% keywords: CLI
#%End
#%Option
#% key: width
#% type: integer
#% description: Width for display monitor if not set by GRASS_WIDTH
#% answer: 800
#%End
#%Option
#% key: height
#% type: integer
#% description: Height for display monitor if not set by GRASS_HEIGHT
#% answer: 600
#%End
#%Option
#% key: handler
#% type: string
#% description: Window program to use
#% options: ximgview,wximgview,wxpyimgview,qiv
#% answer: wximgview
#%End
#%option
#% key: percent
#% type: integer
#% description: Percentage of CPU time to use
#% answer: 10
#%end
#%option
#% key: color
#% type: string
#% description: Background color, either a standard GRASS color or R:G:B triplet (separated by colons)
#% answer: white
#% gisprompt: old_color,color,color
#%end
#%Flag
#% key: c
#% description: Use the Cario driver to render images
#%End
#%Flag
#% key: b
#% description: output Bourne shell code to set up display
#%End
#%Flag
#% key: d
#% description: output DOS code to set up display
#%End

import sys
import os
from grass.script import core as grass

def main():
    handler = options['handler']

    img_tmp = grass.tempfile()
    os.remove(img_tmp)
    img_tmp += ".bmp"


    if flags['b']:
        print('GRASS_PNGFILE="%s"' % img_tmp)
        if not os.environ.has_key("GRASS_WIDTH"):
            print('GRASS_WIDTH=%s' % options['width'])
        if not os.environ.has_key("GRASS_HEIGHT"):
           print('GRASS_HEIGHT=%s' % options['height'])
        if flags['c']:
            print('GRASS_RENDER_IMMEDIATE=cairo')
	else:
	    print('GRASS_RENDER_IMMEDIATE=PNG')
        print('GRASS_PNG_MAPPED=TRUE')
        print('GRASS_PNG_READ=TRUE')
        print('export GRASS_PNGFILE GRASS_WIDTH GRASS_HEIGHT GRASS_RENDER_IMMEDIATE GRASS_PNG_MAPPED GRASS_PNG_READ;')

        print('d.erase color=%s;' % options['color'])
        if handler == "qiv":
            print('qiv -T "%s" &' % img_tmp)  # add --center ?
        else:
            print('%s image="%s" percent=%s &' % ( handler, img_tmp, options['percent']) )

        sys.exit(0)



    ## rest of this won't work, as parent can't inherit from the child..
    ##  (unless we do some ugly g.gisenv) 
    ##  ... any ideas? end by running grass.call(['bash'])?
    if not grass.find_program(handler, ['--help']):
        grass.fatal(_("'%s' not found.") % handler)

    os.environ['GRASS_PNGFILE'] = img_tmp
    if not os.environ.has_key("GRASS_WIDTH"):
        os.environ['GRASS_WIDTH'] = options['width']
    if not os.environ.has_key("GRASS_HEIGHT"):
        os.environ['GRASS_HEIGHT'] = options['height']
    if flags['c']:
        os.environ['GRASS_RENDER_IMMEDIATE'] = 'cairo'
    os.environ['GRASS_PNG_MAPPED'] = 'TRUE'
    os.environ['GRASS_PNG_READ'] = 'TRUE'
    #? os.environ['GRASS_PNG_AUTO_WRITE'] = 'FALSE'

    grass.run_command('d.erase', color = options['color'])

    if handler == "qiv":
        ret = grass.call(['qiv', '-T', img_tmp])
    else:
        ret = grass.exec_command(handler, image = img_tmp, percent = options['percent'])

    os.remove(img_tmp)
    sys.exit(ret)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
po
