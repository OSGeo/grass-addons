#!/usr/bin/env python
# -*- coding: utf-8
"""
@module  r.info.iso
@brief   Module for creating metadata based on ISO from raster maps

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2014)
"""

#%module
#% description: Creates metadata based on ISO standard for specified raster map.
#% keywords: raster, metadata, iso
#%end

#%option G_OPT_R_MAP
#%end

#%option
#% key: profil
#% label: Metadata profil based on ISO
#% description: INSPIRE profile is not filled properly (unknown values are filled '$NULL')
#% options: basic, inspire
#% answer: basic
#%end

#%option G_OPT_F_OUTPUT
#% key: mdout
#% label: Name for output metadata file
#% required: no
#%end

#%option G_OPT_M_DIR
#% key: destination
#% label: Path to destination folder
#% required: no
#%end

import os
import sys
sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]), 'etc', 'wx.metadata'))

from grass.script import parser
from mdgrass import *


def main():
    if not options['destination']:
        destination = None
    else:
        destination = options['destination']

    if not options['mdout']:
        mdout = None
    else:
        mdout = options['mdout']

    md = GrassMD(options['map'], 'cell')
    if options['profil'] == 'inspire':
        md.createGrassInspireISO()
        xml_file = md.saveXML(path=destination,
                              xml_out_name=mdout,
                              overwrite=os.getenv('GRASS_OVERWRITE', False))
        if xml_file is not False:
            md.readXML(xml_file)
            print md.validate_inspire()

    else:
        md.createGrassBasicISO()
        xml_file = md.saveXML(path=destination,
                              xml_out_name=mdout,
                              overwrite=os.getenv('GRASS_OVERWRITE', False))
        if xml_file is not False:
            md.readXML(xml_file)
            print md.validate_basic()

if __name__ == "__main__":
    options, flags = parser()
    main()
