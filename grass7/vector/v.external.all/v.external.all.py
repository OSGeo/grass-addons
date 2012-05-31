#!/usr/bin/env python
############################################################################
#
# MODULE:       v.external.all
# AUTHOR(S):    Martin Landa
# PURPOSE:      Links all OGR layers available in given OGR datasource.
# COPYRIGHT:    (C) 2012 by Martin Landa, and the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Links all OGR layers available in given OGR datasource.
#% keywords: vector
#% keywords: external
#% overwrite: yes
#%end
#%flag
#% key: l
#% description: List available layers in data source and exit
#%end
#%option
#% key: dsn
#% type: string
#% description: Name of input OGR or PostGIS data source
#% required: yes
#%end

import os
import sys

from grass.script import core as grass

def list_layers(dsn):
    ret = grass.read_command('v.external',
                             flags = 'l',
                             dsn = dsn)
    if not ret:
        sys.exit(1)
    
    return ret.splitlines()

def make_links(dsn):
    layers = list_layers(dsn)
    
    for layer in layers:
        oname = layer.replace('.', '_')
        grass.message(_("%s\nCreating link for OGR layer <%s> as <%s>...\n%s") % \
                          ('-' * 80, layer, oname, '-' * 80))
        if 0 != grass.run_command('v.external',
                                  dsn = dsn, layer = layer, output = oname):
            grass.warning(_("Unable to create link for OGR layer <%s>") % layer)
    
def main():
    if flags['l']:
        ret = list_layers(options['dsn'])
        sys.stdout.write(os.linesep.join(ret))
        sys.stdout.write(os.linesep)
    else:
        make_links(options['dsn'])
    
    return 0

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
