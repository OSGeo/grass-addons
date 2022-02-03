#!/usr/bin/env python

"""
@module  t.info.iso
@brief   Module for creating metadata based on ISO for temporal maps

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2015)
"""

# %module
# % description: Lists information about space time datasets and maps.
# % keyword: temporal
# % keyword: metadata
# % keyword: extent
# %end

# %option G_OPT_STDS_INPUT
# % description: Name of an existing space time dataset or map
# %end

# %option G_OPT_STDS_TYPE
# % guidependency: input
# % guisection: Required
# % options: strds, str3ds, stvds, raster, raster_3d, vector
# %end

# %option G_OPT_F_OUTPUT
# % required: no
# %end

import os
import sys

import grass.script as grass
import grass.temporal as tgis
from grass.script import parser

grass.utils.set_path(modulename="wx.metadata", dirname="mdlib", path="..")


def main():
    # Load metadata library
    from mdlib.mdgrass import GrassMD

    if not options["output"]:
        destination = None
        output_name = None
    else:
        destination, output_name = os.path.split(options["output"])

    name = options["input"]
    type_ = options["type"]

    # Make sure the temporal database exists
    tgis.init()

    dbif, connected = tgis.init_dbif(None)

    if name.find("@") >= 0:
        id_ = name
    else:
        id_ = "{}@{}".format(name, grass.gisenv()["MAPSET"])

    dataset = tgis.dataset_factory(type_, id_)

    if not dataset.is_in_db(dbif):
        grass.fatal(
            _("Dataset <%s> not found in temporal database") % (id_),
        )

    md = GrassMD(id_, type=type_)
    md.createTemporalISO()
    md.saveXML(
        path=destination,
        xml_out_name=output_name,
        overwrite=os.getenv("GRASS_OVERWRITE", False),
    )


if __name__ == "__main__":
    options, flags = parser()
    sys.exit(main())
