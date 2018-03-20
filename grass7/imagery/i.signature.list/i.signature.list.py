#!/usr/bin/env python
#
############################################################################
#
# MODULE:	i.signature.list
# AUTHOR(S):	Luca Delucchi
#
# PURPOSE:	List signature file for a group/subgroup
# COPYRIGHT:	(C) 1997-2016 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################


#%flag
#% key: g
#% description: Return in shell script style, it require group and subgroup options
#%end

#%option G_OPT_I_GROUP
#% description: Group to use for segmentation
#% required : no
#%end

#%option G_OPT_I_SUBGROUP 
#% description: Group to use for segmentation
#% required : no
#%end

import os
import sys
import grass.script as grass

def main():
    group = options['group']
    sub = options['subgroup']
    flagg = flags['g']
    
    if flagg and not (group and sub):
        grass.fatal(_("'g' flag requires group and subgroup options"))
   
    gisenv = grass.gisenv()
    
    path = os.path.join(
            gisenv['GISDBASE'],
            gisenv['LOCATION_NAME'])
    
    if group:
        try:
            name, mapset = group.split('@', 1)
        except ValueError:
            name = group
            mapset = gisenv['MAPSET']
        if not flagg:
            print("Group: {}".format(name))
        path = os.path.join(path, mapset, 'group', name)
        if sub:
            path = os.path.join(path, 'subgroup', sub)
            if not flagg:
                print("    Subgroup: {}".format(sub))
            for sig in os.listdir(path):
                if sig != 'REF':
                    if flagg:
                        print(sig)
                    else:
                        print("        {}".format(sig))
        else:
            path = os.path.join(path, 'subgroup')
            for di in os.listdir(path):
                for sig in os.listdir(os.path.join(path, di)):
                    if sig != 'REF':
                        print("        {}".format(sig))
    else:
        path = os.path.join(path, gisenv['MAPSET'], 'group')
        for gr in os.listdir(path):
            print("Group: {}".format(gr))
            for di in os.listdir(os.path.join(path, gr, 'subgroup')):
                print("    Subgroup: {}".format(di))
                for sig in os.listdir(os.path.join(path, gr, 'subgroup', di)):
                    if sig != 'REF':
                        print("        {}".format(sig))
                
    return


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
