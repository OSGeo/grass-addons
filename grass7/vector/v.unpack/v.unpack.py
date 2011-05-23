#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       v.unpack
# AUTHOR(S):    Luca Delucchi
#               
# PURPOSE:      Unpack up a vector map packed with v.pack
# COPYRIGHT:    (C) 2004-2008, 2010 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Unpacks a vector map packed with r.pack.
#% keywords: vector, import, copying
#%end
#%option
#% key: input
#% type: string
#% gisprompt: old,file,input
#% description: Name of input pack file
#% key_desc: path
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: Name for output vector map (default: taken from input file internals)
#% key_desc: name
#% required : no
#%end
#%flag
#% key: o
#% description: Override projection check (use current location's projection)
#%end

import os
import sys
import shutil
import tarfile
import atexit
import filecmp

from grass.script import core as grass
from grass.script import db as grassdb

def cleanup():
    grass.try_rmdir(tmp_dir)

def main():
    infile = options['input']
    
    global tmp_dir
    tmp_dir = grass.tempdir()
    grass.debug('tmp_dir = %s' % tmp_dir)
    
    if not os.path.exists(infile):
        grass.fatal(_("File <%s> not found" % infile))
    
    gisenv = grass.gisenv()
    mset_dir = os.path.join(gisenv['GISDBASE'],
                            gisenv['LOCATION_NAME'],
                            gisenv['MAPSET'])
    input_base = os.path.basename(infile)
    shutil.copyfile(infile, os.path.join(tmp_dir, input_base))
    os.chdir(tmp_dir)
    tar = tarfile.TarFile.open(name = input_base, mode = 'r:gz')
    try:
        data_name = tar.getnames()[0]
    except:
        grass.fatal(_("Pack file unreadable"))
    
    if options['output']:
        map_name = options['output']
    else:
        map_name = data_name
    
    gfile = grass.find_file(name = map_name, element = 'vector',
                            mapset = '.')
    overwrite = os.getenv('GRASS_OVERWRITE')
    if gfile['file'] and overwrite != '1':
        grass.fatal(_("Vector map <%s> already exists") % map_name)
    
    # extract data
    tar.extractall()

    # check projection compatibility in a rather crappy way
    if not filecmp.cmp(os.path.join(data_name,'PROJ_INFO'), os.path.join(mset_dir, '..', 'PERMANENT', 'PROJ_INFO')):
        if flags['o']:
            grass.warning(_("Projection information does not match. Proceeding..."))
        else:
            grass.fatal(_("Projection information does not match. Aborting."))

    vect_dir = os.path.join(mset_dir,'vector')
    new_dir = os.path.join(vect_dir,data_name)
    shutil.copytree(data_name, new_dir)

    dbconn = grassdb.db_connection()
    if dbconn['database'].find('GISDBASE'):
        dbstr = os.path.sep.join(dbconn['database'].split(os.path.sep)[3:])
        todb = os.path.join(mset_dir, dbstr)

    cptable = grass.run_command('db.copy', to_driver = dbconn['driver'], 
                               to_database = todb, to_table =  map_name, 
                               from_driver = 'sqlite', 
                               from_database = os.path.join(new_dir, 'db.sqlite'),
                               from_table= map_name)

    os.remove(os.path.join(new_dir,'PROJ_INFO'))
    os.remove(os.path.join(new_dir,'PROJ_UNITS'))
    os.remove(os.path.join(new_dir,'db.sqlite'))

    import pdb; pdb.set_trace()

    grass.verbose(_("Vector map saved to <%s>") % map_name)

if __name__ == "__main__":
  options, flags = grass.parser()
  atexit.register(cleanup)
  sys.exit(main())
