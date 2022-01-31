#!/usr/bin/env python
"""
MODULE:    v.in.osm

AUTHOR(S): Stepan Turek <stepan.turek AT seznam.cz>

PURPOSE:   Imports OpenStreetMap data into GRASS GIS.

COPYRIGHT: (C) 2016 Stepan Turek, and by the GRASS Development Team
            - list layers (-l) support and minor tweaks for OSM .pbf import by Markus Neteler

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

# %module
# % description: Imports OpenStreetMap data into GRASS GIS.
# % keyword: osm
# % keyword: vector
# % keyword: import
# %end

# %option G_OPT_F_BIN_INPUT
# % description: Table file to be imported or DB connection string
# %end

# %option G_OPT_V_OUTPUT
# % description: Name for output vector map
# % required: no
# %end

# %option G_OPT_DB_WHERE
# %end

# %option G_OPT_V_TYPE
# % description: Name for output vector map
# % options: point,line,boundary,centroid
# % answer: point,line,boundary,centroid
# % required: no
# %end

# %option G_OPT_DB_TABLE
# %end

# %flag
# % key: o
# % label: Override projection check (use current location's projection)
# % description: Assume that the dataset has the same projection as the current location
# %end

# %flag
# % key: l
# % label: List available OGR layers in data source and exit
# %end

import os
import sys
import atexit
from grass.script.utils import try_rmdir
import grass.script as grass
from grass.exceptions import CalledModuleError


class OsmImporter:
    def __init__(self):

        self.tmp_vects = []
        self.tmp_opid = str(os.getpid())

    def cleanup(self):

        for tmp in self.tmp_vects:
            grass.run_command(
                "g.remove", flags="f", type="vector", name=tmp, quiet=True
            )

    def _getTmpName(self, name):

        return name + "_" + self.tmp_opid

    def getNewTmp(self, name):

        tmp = self._getTmpName(name)

        self.tmp_vects.append(tmp)

        return tmp

    def getTmp(self, name):

        return self._getTmpName(name)

    def main(self, options, flags):

        # just get the layer names
        if flags["l"]:
            try:
                grass.run_command(
                    "v.in.ogr", quiet=True, input=options["input"], flags="l"
                )
                sys.exit()
            except CalledModuleError:
                grass.fatal(_("%s failed") % "v.in.ogr")
        else:
            if not options["table"]:
                grass.fatal(_("Required parameter <%s> not set") % "table")
            if not options["output"]:
                grass.fatal(_("Required parameter <%s> not set") % "output")

        # process
        try:
            # http://gdal.org/drv_osm.html
            os.environ["OGR_INTERLEAVED_READING"] = "YES"

            grass.debug("Step 1/3: v.in.ogr...", 2)
            grass.run_command(
                "v.in.ogr",
                quiet=True,
                input=options["input"],
                output=self.getNewTmp("ogr"),
                layer=options["table"],
                where=options["where"],
                type=options["type"],
                flags=flags["o"],
            )
        except CalledModuleError:
            grass.fatal(_("%s failed") % "v.in.ogr")

        try:
            grass.debug("Step 2/3: v.split...", 2)
            grass.run_command(
                "v.split",
                quiet=True,
                input=self.getTmp("ogr"),
                output=self.getNewTmp("split"),
                vertices=2,
            )
        except CalledModuleError:
            grass.fatal(_("%s failed") % "v.split")

        try:
            grass.debug("Step 3/3: v.build.polylines...", 2)
            grass.run_command(
                "v.build.polylines",
                quiet=True,
                input=self.getNewTmp("split"),
                output=options["output"],
                cats="same",
            )
        except CalledModuleError:
            grass.fatal(_("%s failed") % "v.build.polylines")


if __name__ == "__main__":
    options, flags = grass.parser()

    osm_imp = OsmImporter()
    atexit.register(osm_imp.cleanup)

    osm_imp.main(options, flags)
