#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       v.pack
# AUTHOR(S):    Luca Delucchi, Fondazione E. Mach (Italy)
#
# PURPOSE:      Pack up a vector map, collect vector map elements => gzip
# COPYRIGHT:    (C) 2011 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Packs up a vector map and support files for copying.
#% keywords: vector, export, copying
#%end
#%option
#% key: input
#% type: string
#% gisprompt: old,cell,vector
#% description: Name of vector map to pack up
#% key_desc: name
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new_file,file,output
#% description: Name for output file (default is <input>.pack)
#% key_desc: path
#% required : no
#%end

import os
import sys
import shutil
import tarfile

from grass.script import core as grass
from grass.script import db as grassdb

def main():
    infile = options['input']
    if options['output']:
        outfile = options['output']
    else:
        outfile = infile + '.pack'
        
    gfile = grass.find_file(infile, element = 'vector')
    if not gfile['name']:
        grass.fatal(_("Vector map <%s> not found") % infile)

    if os.path.exists(outfile):
        if os.getenv('GRASS_OVERWRITE'):
            grass.warning(_("Pack file <%s> already exists and will be overwritten") % outfile)
            grass.try_remove(outfile)
        else:
            grass.fatal(_("option <output>: <%s> exists.") % outfile)
    grass.message(_("Packing <%s> to <%s>...") % (gfile['fullname'], outfile))
    basedir = os.path.sep.join(gfile['file'].split(os.path.sep)[:-2])
    olddir  = os.getcwd()
    
    dbconn = grassdb.db_connection()
    if dbconn['database'].find('GISDBASE'):
      dbstr = os.path.sep.join(dbconn['database'].split(os.path.sep)[3:])
      fromdb = os.path.join(basedir, dbstr)

    sqlitedb = os.path.join(basedir, 'vector', infile, 'db.sqlite')
    
    cptable = grass.run_command('db.copy', from_driver = dbconn['driver'], 
                               from_database = fromdb, from_table =  infile, 
                               to_driver = 'sqlite', to_database = sqlitedb, 
                               to_table= infile)

    tar = tarfile.open(outfile, "w:gz")   
    tar.add(os.path.join(basedir,'vector',infile),infile)
    gisenv = grass.gisenv()
    for support in ['INFO', 'UNITS']:
        path = os.path.join(gisenv['GISDBASE'], gisenv['LOCATION_NAME'],
                            'PERMANENT', 'PROJ_' + support)
        if os.path.exists(path):
          tar.add(path,os.path.join(infile,'PROJ_' + support))
    tar.close()
    os.remove(sqlitedb)
    grass.verbose(_("Vector map saved to '%s'" % os.path.join(olddir, outfile)))
            
if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
