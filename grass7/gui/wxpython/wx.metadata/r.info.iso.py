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
#%option G_OPT_R_MAP
#% key: map
#% label: Name of input raster map
#% required: yes
#%end

#%flag
#% key: o
#% label: Allow to overwrite exist metadata
#%end

#%option
#% key: profil
#% label: Metadata profil based on ISO
#% description: INSPIRE profile is not filled properly (unknown values are filled '$NULL')
#% options: basic, inspire
#% answer: basic
#%end

#%option G_OPT_R_MAP
#% key: mdout
#% label: Name of output metadata file
#% required: no
#%end

#%option G_OPT_M_DIR
#% key: destination
#% label: Path to destination folder
#% required: no
#%end

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
                              overwrite=flags['o'])
        if xml_file is not False:
            md.readXML(xml_file)
            print md.validate_inspire()

    else:
        md.createGrassBasicISO()
        xml_file = md.saveXML(path=destination,
                              xml_out_name=mdout,
                              overwrite=flags['o'])
        if xml_file is not False:
            md.readXML(xml_file)
            print md.validate_basic()

if __name__ == "__main__":
    options, flags = parser()
    main()
