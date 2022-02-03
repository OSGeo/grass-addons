#!/usr/bin/env python

"""
@module  v.info.iso
@brief   Module for creating metadata based on ISO for vector maps

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2014)
"""

# %module
# % description: Creates metadata based on ISO standard for specified vector map.
# % keyword: vector
# % keyword: metadata
# % keyword: iso
# %end

# %option G_OPT_V_MAP
# %end

# %option
# % key: profile
# % label: Metadata profile based on ISO
# % description: INSPIRE profile is not filled properly (unknown values are filled with '$NULL')
# % options: basic, inspire
# % answer: basic
# %end

# %option G_OPT_F_OUTPUT
# % required: no
# %end

import os
import sys

from grass.script import parser
from grass.script.utils import set_path

set_path(modulename="wx.metadata", dirname="mdlib", path="..")


def main():
    # Load metadata library
    from mdlib.mdgrass import GrassMD

    if not options["output"]:
        destination = None
        name = None
    else:
        destination, name = os.path.split(options["output"])

    md = GrassMD(options["map"], "vector")
    if options["profile"] == "inspire":
        md.createGrassInspireISO()
        xml_file = md.saveXML(
            path=destination,
            xml_out_name=name,
            overwrite=os.getenv("GRASS_OVERWRITE", False),
        )

        if xml_file is not False:
            md.readXML(xml_file)
            print(md.validate_inspire())

    else:
        md.createGrassBasicISO()
        xml_file = md.saveXML(
            path=destination,
            xml_out_name=name,
            overwrite=os.getenv("GRASS_OVERWRITE", False),
        )

        if xml_file is not False:
            md.readXML(xml_file)
            print(md.validate_basic())


if __name__ == "__main__":
    options, flags = parser()
    sys.exit(main())
