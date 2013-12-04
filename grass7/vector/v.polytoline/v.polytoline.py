#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       v.polytoline
# AUTHOR(S):    Luca delucchi
#
# PURPOSE:      Convert polygon to line
# COPYRIGHT:    (C) 2013 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (version 2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Convert polygon to line.
#% keywords: vector
#% keywords: geometry
#%end

#%option G_OPT_V_INPUT
#%end

#%option G_OPT_V_OUTPUT
#%end

import grass.script as grass
import os

def main():
    # Get the options
    input = options["input"]
    output = options["output"]

    overwrite = grass.overwrite()

    quiet = True

    if grass.verbosity() > 2:
        quiet = False

    in_info = grass.vector_info(input)
    if in_info['areas'] == 0 and in_info['boundaries'] == 0:
        grass.fatal(_("The input vector seems not to be polygon"))
    pid = os.getpid()
    out_type = '{inp}_type_{pid}'.format(inp=input, pid=pid)
    if 0 != grass.run_command('v.type', input=input, output=out_type, \
                              from_type='boundary', to_type='line', \
                              quiet=quiet):
        grass.fatal(_("Error converting polygon to line"))
    report = grass.read_command('v.category', flags='g', input=out_type,
                                option='report', quiet=quiet).split('\n')
    for r in report:
        if r.find('centroid') != -1:
            min_cat = report[0].split()[-2]
            max_cat = report[0].split()[-1]
            break
    if 0 != grass.run_command('v.edit', map=out_type, tool='delete', \
                              type='centroid', quiet=quiet, \
                              cats='{mi}-{ma}'.format(mi=min_cat, ma=max_cat)):
        grass.fatal(_("Error removing centroids"))
    if 0 != grass.run_command('v.category', input=out_type, option='add',
                              output=output, quiet=quiet, overwrite=overwrite):
        grass.run_command('g.remove', vect=out_type, quiet=quiet)
        grass.fatal(_("Error adding categories"))
    grass.run_command('g.remove', vect=out_type, quiet=quiet)

if __name__ == "__main__":
    options, flags = grass.parser()
    main()
