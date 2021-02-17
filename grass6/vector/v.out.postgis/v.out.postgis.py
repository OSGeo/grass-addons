#!/usr/bin/env python
############################################################################
#
# MODULE:       v.out.postgis
# AUTHOR:       Martin Landa <landa.martin gmail.com>
# PURPOSE:      Converts GRASS vectors into PostGIS
#               (Wrapper for v.out.ogr)
# COPYRIGHT:    (c) 2009 Martin Landa, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Converts GRASS vector map(s) into PostGIS
#% keywords: vector, conversion
#%End

#%flag
#% key: a
#% description: Convert all vector maps in the mapset
#%end

#%option
#% key: input
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of vector map to be converted
#%required: no
#%end

#%option
#% key: dbname
#% type: string
#% key_desc: name
#% description: Name of PostGIS database
#% required: yes
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new,vector,vector
#% key_desc: name
#% description: Name for output vector map
#% required: no
#%end

import sys
import grass.script as grass

def main():
    if not flags['a'] and not options['input']:
        grass.fatal('Parameter <input> required')

    map_input = []
    map_output = []
    if flags['a']:
        mapset = grass.gisenv()['MAPSET']
        map_input = map_output = grass.mlist_grouped(type = 'vect',
                                                    mapset = mapset)[mapset]
    else:
        map_input = [options['input']]

    if not flags['a']:
        if not options['output']:
            map_output = map_input
        else:
            map_output = [options['output']]

    i = 0
    for imap in map_input:
        # determine feature type
        ret = grass.read_command('v.info',
                                 flags = 't',
                                 map = imap)
        if not ret:
            grass.fatal('Unable to get information about vector map <%s>' % imap)

        info = {}
        for line in ret.splitlines():
            key, value = line.split('=')
            info[key.strip()] = int(value.strip())

        # extension needed?
        fnum = 0
        if info['points'] > 0:
            fnum += 1
        if info['lines'] > 0:
            fnum += 1
        if info['areas'] > 0:
            fnum += 1

        for ftype in ('points', 'lines', 'areas'):
            if info[ftype] < 1:
                continue

            omap = map_output[i]
            if fnum != 1:
                omap += '_' + ftype

            grass.message('Converting <%s> to <%s> (%s)...' % \
                          (imap, omap, ftype))

            if grass.overwrite():
                grass.run_command('v.out.ogr',
                                  input = imap,
                                  type = ftype.rstrip('s'),
                                  dsn = "PG:dbname=%s" % options['dbname'],
                                  olayer = omap,
                                  format = 'PostgreSQL',
                                  lco = "OVERWRITE=YES")
            else:
                grass.run_command('v.out.ogr',
                                  input = imap,
                                  type = ftype.rstrip('s'),
                                  dsn = "PG:dbname=%s" % options['dbname'],
                                  olayer = omap,
                                  format = 'PostgreSQL')
        i += 1

    return 0

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
